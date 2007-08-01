# -*- coding: utf-8 -*-
#
# Python documentation build configuration file
#
# The contents of this file are pickled, so don't put values in the namespace
# that aren't pickleable (module imports are okay, they're removed automatically).
#

# The default replacements for |version| and |release|:
# The short X.Y version.
version = '2.6'
# The full version, including alpha/beta/rc tags.
release = '2.6a0'
# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%B %d, %Y'

# List of files that shouldn't be included in the build.
unused_files = [
    'whatsnew/2.0.rst',
    'whatsnew/2.1.rst',
    'whatsnew/2.2.rst',
    'whatsnew/2.3.rst',
    'whatsnew/2.4.rst',
    'whatsnew/2.5.rst',
    'macmodules/scrap.rst',
    'modules/xmllib.rst',
]

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
last_updated_format = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
use_smartypants = True

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True
