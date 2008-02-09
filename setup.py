# -*- coding: utf-8 -*-
import ez_setup
ez_setup.use_setuptools()
import sphinx

from setuptools import setup, Feature

setup(
    name='Sphinx',
    version=sphinx.__version__,
#    url='',
#    download_url='',
    license='BSD',
    author='Georg Brandl',
    author_email='georg@python.org',
    description='Python documentation generator',
    long_description='',
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=['sphinx'],
    include_package_data=True,
    scripts=['sphinx-build.py', 'sphinx-web.py', 'sphinx-quickstart.py'],
    entry_points={
        'console_scripts': [
            'sphinx-build = sphinx:main',
            'sphinx-web = sphinx.web:main',
            'sphinx-quickstart = sphinx.quickstart:main'
        ]
    },
    install_requires=['Pygments>=0.8', 'docutils==0.4']
)
