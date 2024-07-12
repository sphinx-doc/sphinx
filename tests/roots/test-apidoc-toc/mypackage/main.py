#!/usr/bin/env python3

import os

import mod_resource
import mod_something

if __name__ == "__main__":
    print(f"Hello, world! -> something returns: {mod_something.something()}")

    res_path = \
        os.path.join(os.path.dirname(mod_resource.__file__), 'resource.txt')
    with open(res_path, encoding='utf-8') as f:
        text = f.read()
    print(f"From mod_resource:resource.txt -> {text}")
