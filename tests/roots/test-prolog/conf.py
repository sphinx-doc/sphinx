import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['prolog_markdown_parser']

rst_prolog = '*Hello world*.\n\n'
rst_epilog = '\n\n*Good-bye world*.'
