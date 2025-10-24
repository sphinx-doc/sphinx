extensions = ['sphinx.ext.apidoc']

apidoc_separate_modules = True
apidoc_template_dir = '_templates/default'
apidoc_modules = [
    {
        'path': 'src/pkg_default',
        'destination': 'generated/default',
    },
    {
        'path': 'src/pkg_custom',
        'destination': 'generated/custom',
        'template_dir': '_templates/custom',
    },
]
