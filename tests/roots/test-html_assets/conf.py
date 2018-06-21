# -*- coding: utf-8 -*-

master_doc = 'index'
project = 'Sphinx'
version = '1.4.4'

html_static_path = ['static', 'subdir']
html_extra_path = ['extra', 'subdir']
html_css_files = ['css/style.css',
                  ('https://example.com/custom.css', {'title': 'title', 'media': 'print'})]
html_js_files = ['js/custom.js',
                 ('https://example.com/script.js', {'async': 'async'})]
exclude_patterns = ['**/_build', '**/.htpasswd']
