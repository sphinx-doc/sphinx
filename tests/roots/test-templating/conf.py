project = 'Sphinx templating <Tests>'
source_suffix = {
    '.txt': 'restructuredtext'
}
keep_warnings = True
templates_path = ['_templates']
release = version = '2013.120'
exclude_patterns = ['_build']

extensions = ['sphinx.ext.autosummary']
autosummary_generate = ['autosummary_templating']
