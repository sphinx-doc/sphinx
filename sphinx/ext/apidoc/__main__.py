"""So program can be started with ``python -m sphinx.apidoc ...``"""

import logging as _logging
import sys

from sphinx.ext.apidoc import main

_logging.basicConfig()

raise SystemExit(main(sys.argv[1:]))
