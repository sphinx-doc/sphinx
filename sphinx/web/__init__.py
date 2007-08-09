# -*- coding: utf-8 -*-
"""
    sphinx.web
    ~~~~~~~~~~

    A web application to serve the Python docs interactively.

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""

import os
import sys
import getopt

import sphinx
from sphinx.web.application import setup_app
from sphinx.web.serve import run_simple

try:
    from werkzeug.debug import DebuggedApplication
except ImportError:
    DebuggedApplication = lambda x, y: x


def main(argv):
    opts, args = getopt.getopt(argv[1:], "dhf:")
    opts = dict(opts)
    if len(args) != 1 or '-h' in opts:
        print 'usage: %s [-d] [-f cfg.py] <doc_root>' % argv[0]
        print ' -d: debug mode, use werkzeug debugger if installed'
        print ' -f: use "cfg.py" file instead of doc_root/webconf.py'
        return 2

    conffile = opts.get('-f', os.path.join(args[0], 'webconf.py'))
    config = {}
    execfile(conffile, config)

    port = config.get('listen_port', 3000)
    hostname = config.get('listen_addr', 'localhost')
    debug = ('-d' in opts) or (hostname == 'localhost')

    config['data_root_path'] = args[0]
    config['debug'] = debug

    def make_app():
        app = setup_app(config, check_superuser=True)
        if debug:
            app = DebuggedApplication(app, True)
        return app

    if os.environ.get('RUN_MAIN') != 'true':
        print '* Sphinx %s- Python documentation web application' % \
              sphinx.__version__.replace('$', '').replace('Revision:', 'rev.')
        if debug:
            print '* Running in debug mode'

    run_simple(hostname, port, make_app, use_reloader=debug)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
