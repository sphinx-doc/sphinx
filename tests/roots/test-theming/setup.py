# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='test-theme',
    packages=find_packages(),
    include_package_data=True,
    entry_points="""
       [sphinx_themes]
       path = test_theme:get_path
    """,
)
