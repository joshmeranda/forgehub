from render import DataLevelMap

from typing import Optional
from os import path
import subprocess

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


class Driver:
    __GIT_CONFIG_USER_NAME: str = "user.name"
    __GIT_CONFIG_USER_EMAIL: str = "user.email"
    __MUTATING_FILE_NAME: str = "repr.txt"

    def __init__(
        self,
        repo_path: str,
        https: Optional[str] = None,
        ssh: Optional[str] = None,
        clone_callbacks: Optional[RemoteCallbacks] = None,
        push_callbacks: Optional[RemoteCallbacks] = None,
    ):
        """Driver is a wrapper around all git operations.

        If neither `https` not `ssh` are specified, `Driver` will attempt to initialize a git repository at that path.
        Otherwise, `Driver` will attempt to clone the repository into `path` using the appropriate protocol. If both are
        specified, `https` will be ignored in favor of `ssh`.

        Take care to pass in an appropriately configured `remote_callbacks values to ensure there are no issues when cloning the repositories.

        :param repo_path: The path to an existing repository where git operations will take place.
        :param https: The https clone url for the repository.
        :param ssh: The ssh clone url for the repository.

        https://www.pygit2.org/recipes.html#main-porcelain-commands
        """
        self.__push_callbacks = push_callbacks

        if ssh is not None:
            self.__repo: Repository = pygit2.clone_repository(
                ssh, repo_path, callbacks=clone_callbacks
            )
        elif https is not None:
            self.__repo: Repository = pygit2.clone_repository(
                https, repo_path, callbacks=clone_callbacks
            )
        else:
            self.__repo: Repository = pygit2.init_repository(repo_path)

    def forge_commits(self, commits_per_day: DataLevelMap):
        """Given a `DataLevelMap` mapping dates to the real amount of commit to be made.

        :param commits_per_day: A correct mapping between a date and the amount of commits to be made on that date.
        """
        config = self.__repo.config

        try:
            signature = Signature(
                config[Driver.__GIT_CONFIG_USER_NAME],
                config[Driver.__GIT_CONFIG_USER_EMAIL],
            )
        except ValueError:
            raise ValueError(
                "could not determine author from repository, system, or global config"
            )

        mutating_file = path.join(
            path.dirname(self.__repo.path.rstrip(path.sep)), "repr.txt"
        )

        for date, commit_count in commits_per_day.items():
            for i in range(commit_count):
                message = f"commit #{i + 1} for {date.date()}"

                with open(mutating_file, "w") as file:
                    file.write(message)

                try:
                    ref = self.__repo.head.name
                    parents = [self.__repo.head.target]
                except GitError as err:
                    ref = "HEAD"
                    parents = []

                index = self.__repo.index
                index.add(Driver.__MUTATING_FILE_NAME)
                index.write()

                tree = index.write_tree()

                self.__repo.create_commit(
                    ref, signature, signature, message, tree, parents
                )

                # change the commit date
                # todo: ideally we would not spawn a subprocess every time to change the commit date
                new_date = date.strftime("%Y.%m.%d")
                _proc = subprocess.run(
                    f"git commit --amend --no-edit --date={new_date}".split(),
                    cwd=path.dirname(self.__repo.path.rstrip(path.sep)),
                    capture_output=True,
                )

    def push(self, remote_name: str = "origin"):
        """Push to the remote with the given name.

        :param remote_name: The name of the target origin.
        """
        try:
            remote = self.__repo.remotes[remote_name]
        except KeyError:
            return ValueError(
                f"no such remote '{remote_name}' exists for the given repo"
            )

        # todo: we should accept this from user, or determine the default branch name
        remote.push(["refs/heads/main"], callbacks=self.__push_callbacks)
