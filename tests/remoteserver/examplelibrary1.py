#!/usr/bin/env python

import os
import sys

from robotremoteserver import RobotRemoteServer


class ExampleLibrary:
    """Example library to be used with Robot Framework's remote server.

    This documentation is visible in docs generated by `Libdoc`.
    """

    def count_items_in_directory_new(self, path: str) -> int:
        """Returns the number of items in the directory specified by `path`."""
        items = [i for i in os.listdir(path) if not i.startswith(".")]
        return len(items)

    def strings_should_be_equal_new(self, str1: str, str2: str) -> None:
        print("Comparing '%s' to '%s'." % (str1, str2))
        if not (isinstance(str1, str) and isinstance(str2, str)):
            raise TypeError("Given strings are not strings.")
        if str1 != str2:
            raise AssertionError("Given strings are not equal.")


if __name__ == "__main__":
    RobotRemoteServer(ExampleLibrary(), *sys.argv[1:], port=8271)
