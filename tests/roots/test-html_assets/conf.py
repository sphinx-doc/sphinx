# -*- coding: utf-8 -*-

master_doc = 'index'
project = 'Sphinx'
version = '1.4.4'

html_static_path = ['static', 'subdir']
html_extra_path = ['extra', 'subdir']
html_stylesheets = ['css/style.css',
                    ('https://example.com/custom.css', True, 'title')]
html_javascripts = ['js/custom.js']
exclude_patterns = ['**/_build', '**/.htpasswd']
