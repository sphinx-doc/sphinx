# -*- coding: utf-8 -*-
"""
    sphinx.io
    ~~~~~~~~~

    Input/Output files

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from docutils.io import FileInput
from docutils.readers import standalone
from docutils.writers import UnfilteredWriter
from six import string_types, text_type
from typing import Any, Union  # NOQA

from sphinx.transforms import (
    ApplySourceWorkaround, ExtraTranslatableNodes, CitationReferences,
    DefaultSubstitutions, MoveModuleTargets, HandleCodeBlocks, SortIds,
    AutoNumbering, AutoIndexUpgrader, FilterSystemMessages,
)
from sphinx.transforms.compact_bullet_list import RefOnlyBulletListTransform
from sphinx.transforms.i18n import (
    PreserveTranslatableMessages, Locale, RemoveTranslatableInline,
)
from sphinx.util import import_object, split_docinfo
from sphinx.util.docutils import LoggingReporter

if False:
    # For type annotation
    from typing import Any, Union  # NOQA
    from docutils import nodes  # NOQA
    from docutils.io import Input  # NOQA
    from docutils.parsers import Parser  # NOQA
    from docutils.transforms import Transform  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.builders import Builder  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA


class SphinxBaseReader(standalone.Reader):
    """
    Add our source parsers
    """
    def __init__(self, app, parsers={}, *args, **kwargs):
        # type: (Sphinx, Dict[unicode, Parser], Any, Any) -> None
        standalone.Reader.__init__(self, *args, **kwargs)
        self.parser_map = {}  # type: Dict[unicode, Parser]
        for suffix, parser_class in parsers.items():
            if isinstance(parser_class, string_types):
                parser_class = import_object(parser_class, 'source parser')  # type: ignore
            parser = parser_class()
            if hasattr(parser, 'set_application'):
                parser.set_application(app)
            self.parser_map[suffix] = parser

    def read(self, source, parser, settings):
        # type: (Input, Parser, Dict) -> nodes.document
        self.source = source

        for suffix in self.parser_map:
            if source.source_path.endswith(suffix):
                self.parser = self.parser_map[suffix]
                break

        if not self.parser:
            self.parser = parser
        self.settings = settings
        self.input = self.source.read()
        self.parse()
        return self.document

    def get_transforms(self):
        # type: () -> List[Transform]
        return standalone.Reader.get_transforms(self) + self.transforms

    def new_document(self):
        document = standalone.Reader.new_document(self)
        reporter = document.reporter
        document.reporter = LoggingReporter(reporter.source, reporter.report_level,
                                            reporter.halt_level, reporter.debug_flag,
                                            reporter.error_handler)
        return document


class SphinxStandaloneReader(SphinxBaseReader):
    """
    Add our own transforms.
    """
    transforms = [ApplySourceWorkaround, ExtraTranslatableNodes, PreserveTranslatableMessages,
                  Locale, CitationReferences, DefaultSubstitutions, MoveModuleTargets,
                  HandleCodeBlocks, AutoNumbering, AutoIndexUpgrader, SortIds,
                  RemoveTranslatableInline, PreserveTranslatableMessages, FilterSystemMessages,
                  RefOnlyBulletListTransform]


class SphinxI18nReader(SphinxBaseReader):
    """
    Replacer for document.reporter.get_source_and_line method.

    reST text lines for translation do not have the original source line number.
    This class provides the correct line numbers when reporting.
    """

    transforms = [ApplySourceWorkaround, ExtraTranslatableNodes, CitationReferences,
                  DefaultSubstitutions, MoveModuleTargets, HandleCodeBlocks,
                  AutoNumbering, SortIds, RemoveTranslatableInline,
                  FilterSystemMessages, RefOnlyBulletListTransform]

    def __init__(self, *args, **kwargs):
        # type: (Any, Any) -> None
        SphinxBaseReader.__init__(self, *args, **kwargs)
        self.lineno = None  # type: int

    def set_lineno_for_reporter(self, lineno):
        # type: (int) -> None
        self.lineno = lineno

    def new_document(self):
        # type: () -> nodes.document
        document = SphinxBaseReader.new_document(self)
        reporter = document.reporter

        def get_source_and_line(lineno=None):
            return reporter.source, self.lineno

        reporter.get_source_and_line = get_source_and_line
        return document


class SphinxDummyWriter(UnfilteredWriter):
    supported = ('html',)  # needed to keep "meta" nodes

    def translate(self):
        # type: () -> None
        pass


class SphinxFileInput(FileInput):
    def __init__(self, app, env, *args, **kwds):
        # type: (Sphinx, BuildEnvironment, Any, Any) -> None
        self.app = app
        self.env = env
        kwds['error_handler'] = 'sphinx'  # py3: handle error on open.
        FileInput.__init__(self, *args, **kwds)

    def decode(self, data):
        # type: (Union[unicode, bytes]) -> unicode
        if isinstance(data, text_type):  # py3: `data` already decoded.
            return data
        return data.decode(self.encoding, 'sphinx')  # py2: decoding

    def read(self):
        # type: () -> unicode
        def get_parser_type(source_path):
            for suffix in self.env.config.source_parsers:
                if source_path.endswith(suffix):
                    parser_class = self.env.config.source_parsers[suffix]
                    if isinstance(parser_class, string_types):
                        parser_class = import_object(parser_class, 'source parser')  # type: ignore  # NOQA
                    return parser_class.supported
            else:
                return ('restructuredtext',)

        data = FileInput.read(self)
        if self.app:
            arg = [data]
            self.app.emit('source-read', self.env.docname, arg)
            data = arg[0]
        docinfo, data = split_docinfo(data)
        if 'restructuredtext' in get_parser_type(self.source_path):
            if self.env.config.rst_epilog:
                data = data + '\n' + self.env.config.rst_epilog + '\n'
            if self.env.config.rst_prolog:
                data = self.env.config.rst_prolog + '\n' + data
        return docinfo + data
