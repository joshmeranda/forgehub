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
    # todo: dump data level maps to file
    # todo: import data level map from file
    parser = ArgumentParser(
        prog="forgehub",
        description="Abuse the github activity calendar to draw patterns or write messages",
        add_help=True,
    )

    parser.add_argument(
        "text", help="the text that should be displayed on the github activity calendar"
    )
    parser.add_argument(
        "repo",
        help="either a path to a locally cloned repo, or the url to an upstream repository",
    )

    parser.add_argument(
        "-d",
        "--dilute",
        action="store_true",
        help="specify to dilute existing activity by generating even more commits",
    )

    parser.add_argument(
        "--user",
        help=(
            "the name of the target user, if not specified the user is determined by"
            "either the user associated with the passed token or the git system / global configs"
        ),
    )

    ssh_group = parser.add_argument_group(
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
    token_group = parser.add_mutually_exclusive_group()
    token_group.add_argument(
        "-t", "--token", help="use the given value as the authenticated access token"
    )
    token_group.add_argument(
        "-f",
        "--token-file",
        type=FileType("r"),
        help="read the token from the given file",
    )

    behavior_group = parser.add_argument_group()
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


def main():
    namespace = __parse_args()

    try:
        user = __get_user(namespace)
    except GithubException as err:
        print(f"an error occurred fetching github user: {err}")
        sys.exit(1)

    if user is None:
        print("no user could be determined from arguments or environment")
        sys.exit(1)

    print(f"retrieving activity for user '{user}'...")
    _, max_events_per_day = events.get_max_events_per_day(user)
    boundaries = events.get_data_level_boundaries(max_events_per_day, namespace.dilute)

    print("rendering output...")
    renderer = TextRenderer()
    raw_data_level_map = renderer.render(namespace.text)
    scaled_data_level_map = render.scale_data_level_map(boundaries, raw_data_level_map)

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
        with Driver(repo_path, repo_upstream, callbacks, callbacks) as driver:
            print("crafting commits...")
            driver.forge_commits(scaled_data_level_map)

            if not namespace.no_push:
                print("pushing to upstream...")
                driver.push()
    except DriverInitError as err:
        print(f"error initializing repository: {err}")
        sys.exit(2)
    except DriverForgeError as err:
        print(f"error forging commits: {err}")
        sys.exit(3)
    except DriverPushError as err:
        print(f"error pushing to upstream: {err}")
        sys.exit(4)
