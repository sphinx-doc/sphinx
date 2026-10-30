import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

project = 'Smart quotes cache'
extensions = ['smartquotes_builder']
