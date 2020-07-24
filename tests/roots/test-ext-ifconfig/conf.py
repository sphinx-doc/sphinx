extensions = ['sphinx.ext.ifconfig']
exclude_patterns = ['_build']

confval1 = True


def setup(app):
    app.add_config_value('confval1', False, None)
    app.add_config_value('confval2', False, None)
