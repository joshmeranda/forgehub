import datetime

from forgehub.events import *
from forgehub.git import *
from forgehub.render import *

from argparse import ArgumentParser, FileType, Namespace
import os
import sys
from typing import Optional, Union

from github import AuthenticatedUser, Github, GithubException, NamedUser
import pygit2

GithubUser = Union[NamedUser.NamedUser, AuthenticatedUser.AuthenticatedUser]


def __parse_args() -> Namespace:
    # todo: create a new repository rather than using an existing repo
    parser = ArgumentParser(
        prog="forgehub",
        description="Abuse the github activity calendar to draw patterns or write messages",
        add_help=True,
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # # # # # # # # # # # # # # # # # #
    # subcommand write                #
    # # # # # # # # # # # # # # # # # #

    write_parser = subparsers.add_parser(
        "write", help="write text to your github activity calendar"
    )

    write_parser.add_argument(
        "repo",
        help="either a path to a locally cloned repo, or the url to an upstream repository",
    )

    write_parser.add_argument(
        "-d",
        "--dilute",
        action="store_true",
        help="specify to dilute existing activity by generating even more commits",
    )

    write_parser.add_argument(
        "--user",
        help=(
            "the name of the target user, if not specified the user is determined by"
            "either the user associated with the passed token or the git system / global configs"
        ),
    )

    source_group = write_parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "text",
        nargs="?",
        help="the text that should be displayed on the github activity calendar",
    )
    source_group.add_argument(
        "-l",
        "--load",
        type=FileType("r"),
        help="load an unscaled data level map from the given file",
    )

    create_group = write_parser.add_argument_group(
        title="creation",
        description="arguments controlling if and how a new repository is created",
    )
    create_group.add_argument(
        "-c",
        "--create",
        action="store_true",
        help="create a new local and remote repository  with the name given as repo rather than using an existing one (requires an access token)",
    )
    create_group.add_argument(
        "-p",
        "--private",
        action="store_true",
        help="specify that the new repository should be public rather than private (be careful of your activity calendar's 'Private Contributions' setting)",
    )
    create_group.add_argument(
        "--delete",
        action="store_true",
        help="if a repository already exists for the authenticated user, delete and replace it (use with caution)",
    )

    ssh_group = write_parser.add_argument_group(
        title="ssh", description="values to use when communicating with github over ssh"
    )
    ssh_group.add_argument(
        "--public",
        help="the file path of the public ssh key to for ssh operations, `~/.ssh/id_rsa.pub` if not specified",
    )
    ssh_group.add_argument(
        "--private",
        help="the file path of the private ssh key to for ssh operations, `~/.ssh/id_rsa.pub` if not specified",
    )

    # not required since we can still perform github queries using public only information
    token_group = write_parser.add_mutually_exclusive_group()
    token_group.add_argument(
        "-t", "--token", help="use the given value as the authenticated access token"
    )
    token_group.add_argument(
        "-F",
        "--token-file",
        type=FileType("r"),
        help="read the token from the given file",
    )

    behavior_group = write_parser.add_argument_group()
    behavior_group.add_argument(
        "--no-clean",
        action="store_true",
        help="do not remove any cloned repositories after commits are pushed",
    )
    behavior_group.add_argument(
        "-n",
        "--no-push",
        action="store_true",
        help="do not push the crafted commits automatically (implies (--no-clean)",
    )

    # # # # # # # # # # # # # # # # # #
    # subcommand dump                 #
    # # # # # # # # # # # # # # # # # #

    dump_parser = subparsers.add_parser(
        "dump", help="dump the DataLevelMap for the given data to a file, or stdout"
    )

    dump_parser.add_argument("text", help="the text to be rendered and dumped")
    dump_parser.add_argument(
        "-o", "--out", type=FileType("w"), help="the output file for the DataLevelMap"
    )
    dump_parser.add_argument(
        "-i", "--include-dates", action="store_true", help="include dates in output"
    )

    return parser.parse_args()


def __get_token(namespace: Namespace) -> Optional[str]:
    if namespace.token is not None:
        return namespace.token

    if namespace.token_file is not None:
        return namespace.token_file.readline().rstrip("\n")

    return None


def __get_user(namespace: Namespace) -> Optional[GithubUser]:
    token = __get_token(namespace)

    # todo: we should probably ask the user for username and password if not given (--login / --no-login /
    #       --interactive?) rather than just carrying on with an unauthenticated client
    if token is not None:
        github_client = Github(login_or_token=token)
    else:
        github_client = Github()

    if namespace.user is not None:
        return github_client.get_user(namespace.user)

    if token is not None:
        # return the authenticated user
        return github_client.get_user()

    # return from system / global config
    try:
        return pygit2.Config()["core.user"]
    except GithubException:
        return None


def __get_ssh_keys(namespace: Namespace) -> (str, str):
    """Retrieve the public key, and private key files.

    :param namespace: The namespace of command line arguments.
    :return: The paths to the private key, and the public key
    """
    home = os.getenv("HOME")

    if namespace.private is None:
        private = os.path.join(home, ".ssh", "id_rsa")
    else:
        private = namespace.private

    if namespace.public is None:
        public = os.path.join(home, ".ssh", "id_rsa.pub")
    else:
        public = namespace.public

    return private, public


def __repo_name_from_url(url: str) -> str:
    return url.split("/")[-1].split(".")[0]


def __parse_data_level_map_from_file(file) -> DataLevelMap:
    content: str = file.read().strip()

    if content.isdigit():
        data_levels = list(map(int, content.split()))

        renderer = TextRenderer()
        data_level_map = renderer.render_data_levels(data_levels)
    else:
        data_level_map = DataLevelMap()

        for line in content.splitlines():
            date, data_level = line.split(":")
            date = datetime.datetime.strptime(date, "%Y.%m.%d")

            data_level_map[date] = data_level

    return data_level_map


def __write(namespace: Namespace) -> int:
    print("rendering output...")
    if namespace.load is not None:
        try:
            data_level_map = __parse_data_level_map_from_file(namespace.load)
        except Exception as err:
            print(f"could not load DataLevelMap from file: {err}")
            return 1
    else:
        text = namespace.text if namespace.text is not None else input()

        renderer = TextRenderer()
        data_level_map = renderer.render(text.upper())

    try:
        user = __get_user(namespace)
    except GithubException as err:
        print(f"an error occurred fetching github user: {err}")
        return 1

    if user is None:
        print("no user could be determined from arguments or environment")
        return 1

    print(f"retrieving activity for user '{user}'...")
    _, max_events_per_day = events.get_max_events_per_day(user)
    boundaries = events.get_data_level_boundaries(max_events_per_day, namespace.dilute)
    data_level_map.scale_to_boundaries(boundaries)

    print("initializing repository...")
    private, public = __get_ssh_keys(namespace)
    repo = namespace.repo

    if os.path.exists(repo):
        repo_path = repo
        repo_upstream = None
    else:
        repo_path = __repo_name_from_url(repo)
        repo_upstream = repo

    callbacks = SshRemoteCallbacks(private, public)

    try:
        with GitDriver() as driver:
            if namespace.create:
                if not isinstance(user, AuthenticatedUser.AuthenticatedUser):
                    print("to create a new repository you must provide a token")
                    return 5

                driver.create(namespace.repo, user, callbacks, namespace.delete, namespace.private)
            elif repo_upstream is not None:
                driver.clone_into(repo_path, repo_upstream, callbacks)
            else:
                driver.init_repo(repo_path)
    except DriverInitError as err:
        print(f"error initializing repository: {err}")
        return 2
    except DriverForgeError as err:
        print(f"error forging commits: {err}")
        return 3
    except DriverPushError as err:
        print(f"error pushing to upstream: {err}")
        return 4

    return 0


def __dump(namespace: Namespace) -> int:
    renderer = render.TextRenderer()
    raw_data_level_map = renderer.render(namespace.text.upper())

    if namespace.out is None:
        out_file = sys.stdout
    else:
        out_file = namespace.out

    try:
        if namespace.include_dates:
            out_file.write(
                "\n".join(
                    map(
                        lambda pair: f"{pair[0].strftime('%Y.%m.%d')}:{pair[1]}",
                        raw_data_level_map.items(),
                    )
                )
            )
        else:
            # sort the data levels by date and write to output
            out_file.write(
                "".join(
                    [
                        str(i[1])
                        for i in sorted(
                            raw_data_level_map.items(), key=lambda i: i[0], reverse=True
                        )
                    ]
                )
            )
    except IOError as err:
        print(f"could not write to output: {err}")
        return 1

    if namespace.out is not None:
        out_file.close()

    return 0


def main():
    namespace = __parse_args()

    match namespace.subcommand:
        case "write":
            exit_code = __write(namespace)
        case "dump":
            exit_code = __dump(namespace)
        case _:
            exit_code = 5

    sys.exit(exit_code)
