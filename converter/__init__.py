# -*- coding: utf-8 -*-
"""
    Documentation converter - high level functions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""

import sys
import os
import glob
import shutil
import codecs
from os import path

from .tokenizer import Tokenizer
from .latexparser import DocParser
from .restwriter import RestWriter
from .filenamemap import (fn_mapping, copyfiles_mapping, newfiles_mapping,
                          rename_mapping, dirs_to_make, toctree_mapping,
                          amendments_mapping)
from .console import red, green

def convert_file(infile, outfile, doraise=True, splitchap=False,
                 toctree=None, deflang=None, labelprefix=''):
    inf = codecs.open(infile, 'r', 'latin1')
    p = DocParser(Tokenizer(inf.read()).tokenize(), infile)
    if not splitchap:
        outf = codecs.open(outfile, 'w', 'utf-8')
    else:
        outf = None
    r = RestWriter(outf, splitchap, toctree, deflang, labelprefix)
    try:
        r.write_document(p.parse())
        if splitchap:
            for i, chapter in enumerate(r.chapters[1:]):
                coutf = codecs.open('%s/%d_%s' % (
                    path.dirname(outfile), i+1, path.basename(outfile)),
                                    'w', 'utf-8')
                coutf.write(chapter.getvalue())
                coutf.close()
        else:
            outf.close()
        return 1, r.warnings
    except Exception, err:
        if doraise:
            raise
        return 0, str(err)


def convert_dir(outdirname, *args):
    # make directories
    for dirname in dirs_to_make:
        try:
            os.mkdir(path.join(outdirname, dirname))
        except OSError:
            pass

    # copy files (currently only non-tex includes)
    for oldfn, newfn in copyfiles_mapping.iteritems():
        newpathfn = path.join(outdirname, newfn)
        globfns = glob.glob(oldfn)
        if len(globfns) == 1 and not path.isdir(newpathfn):
            shutil.copyfile(globfns[0], newpathfn)
        else:
            for globfn in globfns:
                shutil.copyfile(globfn, path.join(newpathfn,
                                                  path.basename(globfn)))

    # convert tex files
    # "doc" is not converted. It must be rewritten anyway.
    for subdir in ('api', 'dist', 'ext', 'inst', 'commontex',
                   'lib', 'mac', 'ref', 'tut', 'whatsnew'):
        if args and subdir not in args:
            continue
        if subdir not in fn_mapping:
            continue
        newsubdir = fn_mapping[subdir]['__newname__']
        deflang = fn_mapping[subdir].get('__defaulthighlightlang__')
        labelprefix = fn_mapping[subdir].get('__labelprefix__', '')
        for filename in sorted(os.listdir(subdir)):
            if not filename.endswith('.tex'):
                continue
            filename = filename[:-4] # strip extension
            newname = fn_mapping[subdir][filename]
            if newname is None:
                continue
            if newname.endswith(':split'):
                newname = newname[:-6]
                splitchap = True
            else:
                splitchap = False
            if '/' not in newname:
                outfilename = path.join(outdirname, newsubdir, newname + '.rst')
            else:
                outfilename = path.join(outdirname, newname + '.rst')
            toctree = toctree_mapping.get(path.join(subdir, filename))
            infilename = path.join(subdir, filename + '.tex')
            print green(infilename),
            success, state = convert_file(infilename, outfilename, False,
                                          splitchap, toctree, deflang, labelprefix)
            if not success:
                print red("ERROR:")
                print red("    " + state)
            else:
                if state:
                    print "warnings:"
                    for warning in state:
                        print "    " + warning

    # rename files, e.g. splitted ones
    for oldfn, newfn in rename_mapping.iteritems():
        try:
            if newfn is None:
                os.unlink(path.join(outdirname, oldfn))
            else:
                os.rename(path.join(outdirname, oldfn),
                          path.join(outdirname, newfn))
        except OSError, err:
            if err.errno == 2:
                continue
            raise

    # copy new files
    srcdirname = path.join(path.dirname(__file__), 'newfiles')
    for fn, newfn in newfiles_mapping.iteritems():
        shutil.copyfile(path.join(srcdirname, fn),
                        path.join(outdirname, newfn))

    # make amendments
    for newfn, (pre, post) in amendments_mapping.iteritems():
        fn = path.join(outdirname, newfn)
        try:
            ft = open(fn).read()
        except Exception, err:
            print "Error making amendments to %s: %s" % (newfn, err)
            continue
        else:
            fw = open(fn, 'w')
            fw.write(pre)
            fw.write(ft)
            fw.write(post)
            fw.close()
