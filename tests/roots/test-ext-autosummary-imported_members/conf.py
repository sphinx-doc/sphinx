import os
import sys

sys.path.insert(0, os.path.abspath('.'))

extensions = ['sphinx.ext.autosummary']
autosummary_generate = True
autosummary_imported_members = True

# test for #10058 - shoud be scoped just to test_autosummary_imported_members_table_10058
autodoc_class_signature = 'separated'