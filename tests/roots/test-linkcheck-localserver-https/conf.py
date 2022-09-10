import sys

exclude_patterns = ['_build']
linkcheck_timeout = 0.01 if sys.platform != 'win32' else 0.05

del sys
