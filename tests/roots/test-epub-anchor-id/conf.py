latex_documents = [
    ('index', 'test.tex', 'The basic Sphinx documentation for testing', 'Sphinx', 'report')
]


def setup(app):
    app.add_crossref_type(directivename="setting", rolename="setting")
