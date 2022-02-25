from setuptools import setup

from sphinx.setup_command import BuildDoc

cmdclass = {'build_sphinx': BuildDoc}

setup(
    name='sphinxdoc',
    cmdclass=cmdclass,
)
