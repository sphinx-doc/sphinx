html_static_path = ['_static']
html_css_files = [
    'user.css',
    (
        'https://example.com/external.css',
        {'media': 'print', 'priority': 400},
    ),
]
html_js_files = [
    'user.js',
    'https://example.com/external.js',
]
