project = 'Sphinx'
version = '1.4.4'

html_static_path = ['static', 'subdir']
html_extra_path = ['extra', 'subdir']
html_css_files = ['css/style.css',
                  ('https://example.com/custom.css',
                   {'title': 'title', 'media': 'print', 'priority': 400})]
html_js_files = ['js/custom.js',
                 ('https://example.com/script.js',
                  {'async': 'async', 'priority': 400})]
exclude_patterns = ['**/_build', '**/.htpasswd']
