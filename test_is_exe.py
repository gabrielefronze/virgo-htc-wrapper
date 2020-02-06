#! /usr/bin/env python3

from sub_converter import is_exe, is_abs_path
import os.path

def test(path):
    if is_exe(path):
        print("{} is an exe".format(path))
    else:
        print("{} is not an exe".format(path))

    if is_abs_path(path):
        print("{} is abs path".format(path))
    else:
        print("{} is not abs path".format(path))


if __name__ == "__main__":
    test("./")
    test("/Library")
    test("./test_is_exe.py")
    test(os.path.abspath("./test_is_exe.py"))
