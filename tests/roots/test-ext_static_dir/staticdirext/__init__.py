"""Test extension that registers a static directory."""

from pathlib import Path

HERE = Path(__file__).resolve().parent


def setup(app):
    app.add_static_dir(HERE / 'static')
    app.add_js_file('js/myext.js')
    app.add_css_file('css/myext.css')
    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
