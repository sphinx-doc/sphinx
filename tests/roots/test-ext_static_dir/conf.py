import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

project = 'Test Extension Static Dir'
extensions = ['staticdirext']
