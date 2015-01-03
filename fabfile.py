# see http://atelier.lino-framework.org/dev/api/atelier.fablib.html

from atelier.fablib import *
setup_from_fabfile(globals(), 'sphinx')

env.revision_control_system = 'git'
