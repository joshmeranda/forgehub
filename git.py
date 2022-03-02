from typing import Optional

import pygit2
from pygit2 import RemoteCallbacks, Repository


class Driver:
    def __init__(self, path: str,
                 https: Optional[str] = None,
                 ssh: Optional[str] = None,
                 clone_callbacks: Optional[RemoteCallbacks] = None):
        """Driver is a wrapper around all git operations.

        If neither `https` not `ssh` are specified, `Driver` will attempt to
        initialize a git repository at that path. Otherwise, `Driver` will
        attempt to clone the repository into `path` using the appropriate
        protocol. If both are specified, `https` will be ignored in favor of
        `ssh`.

        Take care to pass in an appropriately configured `remote_callbacks`
        values to ensure there are no issues when cloning the repositories.


        :param path: The path to an existing repository where git operations will take place.
        :param https: The https clone url for the repository.
        :param ssh: The ssh clone url for the repository.

        https://www.pygit2.org/recipes.html#main-porcelain-commands
        """

        if ssh is not None:
            self.__repo = pygit2.clone_repository(ssh, path, callbacks=clone_callbacks)
        elif https is not None:
            self.__repo = pygit2.clone_repository(https, path, callbacks=clone_callbacks)
        else:
            self.__repo = pygit2.init_repository(path)
