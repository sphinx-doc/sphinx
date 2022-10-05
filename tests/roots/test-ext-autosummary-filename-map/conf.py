import os
import sys

sys.path.insert(0, os.path.abspath('.'))

extensions = ['sphinx.ext.autosummary']
autosummary_generate = True
autosummary_filename_map = {
    "autosummary_dummy_module": "module_mangled",
    "autosummary_dummy_module.bar": "bar"
}
