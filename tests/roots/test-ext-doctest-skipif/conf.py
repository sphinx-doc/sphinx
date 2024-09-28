extensions = ['sphinx.ext.doctest']

project = 'test project for the doctest :skipif: directive'
root_doc = 'skipif'
source_suffix = {
    '.txt': 'restructuredtext'
}
exclude_patterns = ['_build']

doctest_global_setup = '''
from tests.test_extensions.test_ext_doctest import record

record('doctest_global_setup', 'body', True)
'''

doctest_global_cleanup = '''
record('doctest_global_cleanup', 'body', True)
'''
