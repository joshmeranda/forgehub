from typing import Optional


class Driver:
    def __init__(self, path: Optional[str] = None,
                 https: Optional[str] = None,
                 ssh: Optional[str] = None):
        """Driver is a wrapper around all git operations.

        At least one of `path`, `https`, or `ssh` must be specified or a
        `ValueError` will be raised. If 2 or one are specified they will be
        used in this order: ssh, https, path. If either `ssh` or `https` is
        specified, the repo will be cloned into the current working directory.

        :param path: The path to an existing repository where git operations will take place.
        :param https: The https clone url for the repository.
        :param ssh: The ssh clone url for the repository.
        """

        if ssh is not None:
            pass
        elif https is not None:
            pass
        elif path is not None:
            pass
        else:
            raise ValueError("at least one of ssh, http, or path must not be None")

    def __clone_ssh(self):
        pass

    def __clone_https(self):
        pass

    def init_repo(self):
        pass
