from os import path
import sys

sys.path.insert(0, path.abspath(path.dirname(__file__)))

project = 'test project for doctest + autodoc reporting'
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest']
master_doc = 'index'
