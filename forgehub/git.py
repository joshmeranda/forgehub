from forgehub.render import DataLevelMap

from typing import Optional
from os import path
import shutil
import subprocess

from github import GithubException
from github.AuthenticatedUser import AuthenticatedUser

import pygit2
from pygit2 import (
    credentials,
    GitError,
    Keypair,
    RemoteCallbacks,
    Repository,
    Signature,
    Username,
)

__all__ = [
    "SshRemoteCallbacks",
    "DriverError",
    "DriverInitError",
    "DriverForgeError",
    "DriverPushError",
    "GitDriver",
]


class SshRemoteCallbacks(RemoteCallbacks):
    def __init__(self, private: str, public: str):
        """Provides the necessary for communicating with GitHub over ssh."""
        super().__init__()

        self.__private = private
        self.__public = public

    def credentials(self, url, username_from_url, allowed_types):
        if allowed_types & credentials.GIT_CREDENTIAL_USERNAME:
            return Username("git")
        elif allowed_types & credentials.GIT_CREDENTIAL_SSH_KEY:
            return Keypair("git", self.__public, self.__private, "")
        else:
            return None


class DriverError(Exception):
    """A base error class for other driver related errors."""


class DriverInitError(DriverError):
    """An error for any issue with driver initialization."""


class DriverForgeError(DriverError):
    """An error for any issue related to forging commits."""


class DriverPushError(DriverError):
    """An error for any issue related to pushing to a remote."""


def _did_repo_exist(data: dict) -> bool:
    """Check if the data from a `GithubException` indicates the repository already existed.

    :param data: The data received  from a `GithubException`.
    """
    try:
        error_messages = [error["message"] for error in data["errors"]]

        return "name already exists on this account" in error_messages
    except KeyError:
        return False


class GitDriver:
    __GIT_CONFIG_USER_NAME: str = "user.name"
    __GIT_CONFIG_USER_EMAIL: str = "user.email"
    __MUTATING_FILE_NAME: str = "repr.txt"

    def __init__(self, cleanup: bool = False):
        """A wrapper around all git repository operations, providing a context manager for simple resource cleanup.

        Note: under normal conditions, when a `GitDriver`'s context is left and `cleanup` is `True`, any repositories
        that were cloned into a local directory will be deleted; however, if an exception is raised within its context,
        the cloned repositories will not be cleaned up.

        :param cleanup: Specifies that any cloned repositories should be deleted once the context is left.
        """
        self.__cleanup = cleanup
        self.__repo: Optional[Repository] = None

        # specifies that the repository pointed to by self.__repo was a local repository
        # existing prior to this init method
        self.__was_local_repo = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # we only want to remove the repo path if the driver was configured to clean up the repo, the repo was cloned,
        # and no exception was received by the driver's __exit__
        if exc_type is None and self.__cleanup and not self.__was_local_repo:
            shutil.rmtree(self.__repo.path)

    def init_repo(self, repo_path: str):
        """Initialize the driver's internal repository using the repository at the given path.

        :param repo_path: The path to a local git repository.
        """
        try:
            self.__repo = pygit2.init_repository(repo_path)
            self.__was_local_repo = True
        except GitError as err:
            raise DriverInitError(
                f"could not initialize repository at '{repo_path}': {err}"
            )

    def clone_into(
        self,
        repo_path: str,
        upstream: str,
        clone_callbacks: Optional[RemoteCallbacks] = None,
    ):
        """Clone an upstream repository to a local repository.

        :param repo_path: The path to clone teh created repository into.
        :param upstream: The upstream url for the repository to clone.
        :param clone_callbacks: A RemoteCallbacks instance properly configured to clone over the upstream protocol.
        """
        try:
            self.__repo = pygit2.clone_repository(
                upstream, repo_path, callbacks=clone_callbacks
            )
        except GitError as err:
            raise DriverInitError(
                f"could not clone repository at '{upstream}' into '{repo_path}': {err}"
            )

    def create(
        self,
        name: str,
        user: AuthenticatedUser,
        clone_callbacks: Optional[RemoteCallbacks] = None,
        replace_existing: bool = False,
        private: bool = False,
    ):
        """Create a remote repository and clone to the local system.

        :param name: The name of the new repository.
        :param user: An authenticated GitHub user who is to own the new repository.
        :param clone_callbacks: The RemoteCallbacks to provide when cloning the new repository.
        :param replace_existing: If a repository with the given name already exists, delete it and create a new one.
        :param private: Specifies if the new repository should be private.
        """
        try:
            remote_repo = user.create_repo(
                name,
                (
                    "This repository was auto generated by ForgeHub!"
                    "To learn more please visit: https://github.com/joshmeranda/forgehub"
                ),
                private=private,
                has_issues=False,
                has_wiki=False,
                has_downloads=False,
                has_projects=False,
                auto_init=False,
            )
        except GithubException as err:
            if _did_repo_exist(err.data) and replace_existing:
                try:
                    user.get_repo(name).delete()

                    remote_repo = user.create_repo(
                        name,
                        (
                            "This repository was auto generated by ForgeHub!"
                            "To learn more please visit: https://github.com/joshmeranda/forgehub"
                        ),
                        private=private,
                        has_issues=False,
                        has_wiki=False,
                        has_downloads=False,
                        has_projects=False,
                        auto_init=False,
                    )

                    default_branch = remote_repo.default_branch
                except (GithubException, ValueError) as err:
                    raise DriverInitError(
                        f"could not delete pre-existing repository '{name}': {err}"
                    )
            else:
                raise DriverInitError(f"could not create new repository '{name}': {err}")

        self.clone_into(name, remote_repo.ssh_url, clone_callbacks)

    def forge_commits(self, commits_per_day: DataLevelMap):
        """Given a `DataLevelMap` mapping dates to the real amount of commit to be made.

        :param commits_per_day: A correct mapping between a date and the amount of commits to be made on that date.
        """
        config = self.__repo.config

        try:
            signature = Signature(
                config[GitDriver.__GIT_CONFIG_USER_NAME],
                config[GitDriver.__GIT_CONFIG_USER_EMAIL],
            )
        except ValueError:
            raise DriverForgeError(
                "could not determine author from repository, system, or global config"
            )

        mutating_file = path.join(
            path.dirname(self.__repo.path.rstrip(path.sep)), "repr.txt"
        )

        for date, commit_count in commits_per_day.items():
            for i in range(commit_count):
                message = f"commit #{i + 1} for {date.date()}"

                with open(mutating_file, "w") as file:
                    try:
                        file.write(message)
                    except IOError as err:
                        raise DriverForgeError(err)

                try:
                    ref = self.__repo.head.name
                    parents = [self.__repo.head.target]
                except GitError:
                    ref = "HEAD"
                    parents = []

                try:
                    index = self.__repo.index
                    index.add(GitDriver.__MUTATING_FILE_NAME)
                    index.write()

                    tree = index.write_tree()

                    self.__repo.create_commit(
                        ref, signature, signature, message, tree, parents
                    )
                except GitError as err:
                    raise DriverForgeError(err)

                # change the commit date
                # todo: ideally we would not spawn a subprocess every time to change the commit date
                new_date = date.strftime("%Y.%m.%d")
                _proc = subprocess.run(
                    f"git commit --amend --no-edit --date={new_date}".split(),
                    cwd=path.dirname(self.__repo.path.rstrip(path.sep)),
                    capture_output=True,
                )

    def push(
        self,
        remote_name: str = "origin",
        ref_specs: Optional[list[str]] = None,
        push_callbacks: Optional[RemoteCallbacks] = None,
    ):
        """Push to the remote with the given name.

        If an error occurs while pushing, an internal flag will be set and a cloned repository will not be removed when
        the `Driver` context is left.

        :param remote_name: The name of the target origin.
        :param ref_specs: A list of the references to use when pushing, defaults to `["refs/heads/main"]`.
        :param push_callbacks: The RemoteCallbacks to provide when pushing the repository.
        """
        if ref_specs is None:
            ref_specs = ["refs/heads/main"]
        else:
            for spec in ref_specs:
                if not pygit2.reference_is_valid_name(spec):
                    raise DriverPushError(f"refspec name '{spec}' is not valid")

        try:
            remote = self.__repo.remotes[remote_name]

            remote.push(ref_specs, callbacks=push_callbacks)
        except KeyError:
            raise DriverPushError(
                f"no such remote '{remote_name}' exists for the given repo"
            )
        except GitError as err:
            raise DriverPushError(err)
