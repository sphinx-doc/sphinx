project = 'Sphinx intl <Tests>'
source_suffix = '.txt'
keep_warnings = True
templates_path = ['_templates']
html_additional_pages = {'contents': 'contents.html'}
release = version = '2013.120'
gettext_additional_targets = ['index']
exclude_patterns = ['_build']
rst_prolog = '''
.. |subst_prolog_1| replace:: prolog substitute text

.. |subst_prolog_2| image:: /img.png
'''
rst_epilog = '''
.. |subst_epilog_1| replace:: epilog substitute text

.. |subst_epilog_2| image:: /i18n.png
'''
