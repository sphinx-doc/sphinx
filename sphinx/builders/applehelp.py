# -*- coding: utf-8 -*-
"""
    sphinx.builders.applehelp
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Build Apple help books.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import codecs
import errno

from os import path

from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.util.osutil import copyfile, ensuredir, os_path
from sphinx.util.console import bold
from sphinx.errors import SphinxError

import plistlib
import subprocess


# Use plistlib.dump in 3.4 and above
try:
    write_plist = plistlib.dump
except AttributeError:
    write_plist = plistlib.writePlist


class AppleHelpIndexerFailed(SphinxError):
    def __str__(self):
        return 'Help indexer failed'

    
class AppleHelpBuilder(StandaloneHTMLBuilder):
    """
    Builder that outputs an Apple help book.  Requires Mac OS X as it relies
    on the ``hiutil`` command line tool.
    """
    name = 'applehelp'

    # don't copy the reST source
    copysource = False
    supported_image_types = ['image/png', 'image/gif', 'image/jpeg',
                             'image/tiff', 'image/jp2', 'image/svg+xml']

    # don't add links
    add_permalinks = False
    # *do* add the sidebar (Apple Help doesn't have its own)
    embedded = False
    
    def init(self):
        super(AppleHelpBuilder, self).init()
        # the output files for HTML help must be .html only
        self.out_suffix = '.html'

        self.bundle_path = path.join(self.outdir,
                                     self.config.applehelp_bundle_name \
                                     + '.help')
        self.outdir = path.join(self.bundle_path,
                                'Contents',
                                'Resources',
                                (self.config.language or 'en') + '.lproj')

    def handle_finish(self):
        contents_dir = path.join(self.bundle_path, 'Contents')
        resources_dir = path.join(contents_dir, 'Resources')
        language_dir = path.join(resources_dir,
                                 (self.config.language or 'en') + '.lproj')

        for d in [contents_dir, resources_dir, language_dir]:
            ensuredir(d)

        # Construct the Info.plist file
        info_plist = {
            'CFBundleDevelopmentRegion': self.config.applehelp_dev_region,
            'CFBundleIdentifier': self.config.applehelp_bundle_id,
            'CFBundleInfoDictionaryVersion': 6.0,
            'CFBundleName': self.config.applehelp_bundle_name,
            'CFBundlePackageType': 'BNDL',
            'CFBundleShortVersionString': self.config.release,
            'CFBundleSignature': 'hbwr',
            'CFBundleVersion': self.config.applehelp_bundle_version,
            'CFBundleHelpTOCFile': 'index.html',
            'HPDBookAccessPath': 'index.html',
            'HPDBookIndexPath': 'index.helpindex',
            'HPDBookTitle': self.config.html_title,
            'HPDBookType': 3,
        }

        if self.config.applehelp_icon is not None:
            info_plist['HPDBookIconPath'] \
                = path.basename(self.config.applehelp_icon)

        if self.config.applehelp_kb_url is not None:
            info_plist['HPDBookKBProduct'] = self.config.applehelp_kb_product
            info_plist['HPDBookKBURL'] = self.config.applehelp_kb_url

        if self.config.applehelp_remote_url is not None:
            info_plist['HPDBookRemoteURL'] = self.config.applehelp_remote_url

        self.info(bold('writing Info.plist... '), nonl=True)
        f = codecs.open(path.join(contents_dir, 'Info.plist'), 'w')
        try:
            write_plist(info_plist, f)
        finally:
            f.close()
        self.info('done')

        # Copy the icon, if one is supplied
        if self.config.applehelp_icon:
            self.info(bold('copying icon... '), nonl=True)

            try:
                copyfile(path.join(self.srcdir, self.config.applehelp_icon),
                         path.join(resources_dir, info_plist['HPDBookIconPath']))

                self.info('done')
            except Exception as err:
                self.warn('cannot copy icon file %r: %s' %
                          (path.join(self.srcdir, self.config.applehelp_icon),
                           err))
                del info_plist['HPDBookIconPath']

        # Generate the help index
        self.info(bold('generating help index... '), nonl=True)

        args = [
            '/usr/bin/hiutil',
            '-Cf',
            path.join(language_dir, 'index.helpindex'),
            language_dir
            ]

        if self.config.applehelp_index_anchors is not None:
            args.append('-a')

        if self.config.applehelp_min_term_length is not None:
            args += ['-m', '%s' % self.config.applehelp_min_term_length]

        if self.config.applehelp_stopwords is not None:
            args += ['-s', self.config.applehelp_stopwords]

        if self.config.applehelp_locale is not None:
            args += ['-l', self.config.applehelp_locale]
            
        result = subprocess.call(args)

        if result != 0:
            raise AppleHelpIndexerFailed
        else:
            self.info('done')
        
