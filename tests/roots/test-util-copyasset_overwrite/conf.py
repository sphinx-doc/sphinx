import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['myext']
html_static_path = ['user_static']
html_theme = 'basic'
