import sys, os

sys.path.insert(0, os.path.abspath('.'))

extensions = ['sphinx.ext.autosummary']

# The suffix of source filenames.
source_suffix = '.rst'
autosummary_generate = True

exclude_patterns = ['_build']
