"""Test extension that registers a static directory."""

from pathlib import Path


def setup(app):
    app.add_static_dir(Path(__file__).parent / 'static')
    app.add_js_file('js/myext.js')
    app.add_css_file('css/myext.css')
    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
