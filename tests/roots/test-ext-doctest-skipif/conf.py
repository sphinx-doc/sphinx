extensions = ['sphinx.ext.doctest']

project = 'test project for the doctest :skipif: directive'
master_doc = 'skipif'
source_suffix = '.txt'
exclude_patterns = ['_build']

doctest_global_setup = '''
from test_ext_doctest import record
'''