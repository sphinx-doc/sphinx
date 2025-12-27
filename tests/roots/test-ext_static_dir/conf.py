import sys
from pathlib import Path

# Add the test root to path so we can import the extension
sys.path.insert(0, str(Path(__file__).parent))

project = 'Test Extension Static Dir'
extensions = ['staticdirext']
