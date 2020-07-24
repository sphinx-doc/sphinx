#!/usr/bin/env python3

import os

import mod_resource
import mod_something


if __name__ == "__main__":
    print("Hello, world! -> something returns: {}".format(mod_something.something()))

    res_path = \
        os.path.join(os.path.dirname(mod_resource.__file__), 'resource.txt')
    with open(res_path) as f:
        text = f.read()
    print("From mod_resource:resource.txt -> {}".format(text))
