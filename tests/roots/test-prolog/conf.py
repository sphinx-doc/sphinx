import os
import sys

sys.path.insert(0, os.path.abspath('.'))


extensions = ['prolog_markdown_parser']

rst_prolog = '*Hello world*.\n\n'
rst_epilog = '\n\n*Good-bye world*.'
