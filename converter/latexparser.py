# -*- coding: utf-8 -*-
"""
    Python documentation LaTeX file parser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    For more documentation, look into the ``restwriter.py`` file.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

from .docnodes import CommentNode, RootNode, NodeList, ParaSepNode, \
     TextNode, EmptyNode, NbspNode, SimpleCmdNode, BreakNode, CommandNode, \
     DescLineCommandNode, InlineNode, IndexNode, SectioningNode, \
     EnvironmentNode, DescEnvironmentNode, TableNode, VerbatimNode, \
     ListNode, ItemizeNode, EnumerateNode, DescriptionNode, \
     DefinitionsNode, ProductionListNode

from .util import umlaut, empty


class ParserError(Exception):
    def __init__(self, msg, lineno):
        Exception.__init__(self, msg, lineno)

    def __str__(self):
        return '%s, line %s' % self.args


def generic_command(name, argspec, nodetype=CommandNode):
    def handle(self):
        args = self.parse_args('\\'+name, argspec)
        return nodetype(name, args)
    return handle

def sectioning_command(name):
    """ Special handling for sectioning commands: move labels directly following
        a sectioning command before it, as required by reST. """
    def handle(self):
        args = self.parse_args('\\'+name, 'M')
        snode = SectioningNode(name, args)
        for l, t, v, r in self.tokens:
            if t == 'command' and v == 'label':
                largs = self.parse_args('\\label', 'T')
                snode.args[0] = NodeList([snode.args[0], CommandNode('label', largs)])
                break
            if t == 'text':
                if not v.strip():
                    # discard whitespace; after a section that's no problem
                    continue
            self.tokens.push((l, t, v, r))
            break
        # no label followed
        return snode
    return handle

def generic_environment(name, argspec, nodetype=EnvironmentNode):
    def handle(self):
        args = self.parse_args(name, argspec)
        return nodetype(name, args, self.parse_until(self.environment_end))
    return handle


class DocParserMeta(type):
    def __init__(cls, name, bases, dict):
        for nodetype, commands in cls.generic_commands.iteritems():
            for cmdname, argspec in commands.iteritems():
                setattr(cls, 'handle_' + cmdname,
                        generic_command(cmdname, argspec, nodetype))

        for cmdname in cls.sectioning_commands:
            setattr(cls, 'handle_' + cmdname, sectioning_command(cmdname))

        for nodetype, envs in cls.generic_envs.iteritems():
            for envname, argspec in envs.iteritems():
                setattr(cls, 'handle_%s_env' % envname,
                        generic_environment(envname, argspec, nodetype))


class DocParser(object):
    """ Parse a Python documentation LaTeX file. """
    __metaclass__ = DocParserMeta

    def __init__(self, tokenstream, filename):
        self.tokens = tokenstream
        self.filename = filename

    def parse(self):
        self.rootnode = RootNode(self.filename, None)
        self.rootnode.children = self.parse_until(None)
        self.rootnode.transform()
        return self.rootnode

    def parse_until(self, condition=None, endatbrace=False):
        nodelist = NodeList()
        bracelevel = 0
        for l, t, v, r in self.tokens:
            if condition and condition(t, v, bracelevel):
                return nodelist.flatten()
            if t == 'command':
                if len(v) == 1 and not v.isalpha():
                    nodelist.append(self.handle_special_command(v))
                    continue
                handler = getattr(self, 'handle_' + v, None)
                if not handler:
                    raise ParserError('no handler for \\%s command' % v, l)
                nodelist.append(handler())
            elif t == 'bgroup':
                bracelevel += 1
            elif t == 'egroup':
                if bracelevel == 0 and endatbrace:
                    return nodelist.flatten()
                bracelevel -= 1
            elif t == 'comment':
                nodelist.append(CommentNode(v))
            elif t == 'tilde':
                nodelist.append(NbspNode())
            elif t == 'mathmode':
                pass # ignore math mode
            elif t == 'parasep':
                nodelist.append(ParaSepNode())
            else:
                # includes 'boptional' and 'eoptional' which don't have a
                # special meaning in text
                nodelist.append(TextNode(v))
        return nodelist.flatten()

    def parse_args(self, cmdname, argspec):
        """ Helper to parse arguments of a command. """
        # argspec: M = mandatory, T = mandatory, check text-only,
        #          O = optional, Q = optional, check text-only
        args = []
        def optional_end(type, value, bracelevel):
            return type == 'eoptional' and bracelevel == 0

        for i, c in enumerate(argspec):
            assert c in 'OMTQ'
            nextl, nextt, nextv, nextr = self.tokens.pop()
            while nextt == 'comment' or (nextt == 'text' and nextv.isspace()):
                nextl, nextt, nextv, nextr = self.tokens.pop()

            if c in 'OQ':
                if nextt == 'boptional':
                    arg = self.parse_until(optional_end)
                    if c == 'Q' and not isinstance(arg, TextNode):
                        raise ParserError('%s: argument %d must be text only' %
                                          (cmdname, i), nextl)
                    args.append(arg)
                else:
                    # not given
                    args.append(EmptyNode())
                    self.tokens.push((nextl, nextt, nextv, nextr))
                continue

            if nextt == 'bgroup':
                arg = self.parse_until(None, endatbrace=True)
                if c == 'T' and not isinstance(arg, TextNode):
                    raise ParserError('%s: argument %d must be text only' %
                                      (cmdname, i), nextl)
                args.append(arg)
            else:
                if nextt != 'text':
                    raise ParserError('%s: non-grouped non-text arguments not '
                                      'supported' % cmdname, nextl)
                args.append(TextNode(nextv[0]))
                self.tokens.push((nextl, nextt, nextv[1:], nextr[1:]))
        return args

    sectioning_commands = [
        'chapter',
        'chapter*',
        'section',
        'subsection',
        'subsubsection',
        'paragraph',
    ]

    generic_commands = {
        CommandNode: {
            'label': 'T',

            'localmoduletable': '',
            'verbatiminput': 'T',
            'input': 'T',
            'centerline': 'M',

            # Pydoc specific commands
            'versionadded': 'OT',
            'versionchanged': 'OT',
            'deprecated': 'TM',
            'XX' 'X': 'M',  # used in dist.tex ;)

            # module-specific
            'declaremodule': 'QTT',
            'platform': 'T',
            'modulesynopsis': 'M',
            'moduleauthor': 'TT',
            'sectionauthor': 'TT',

            # reference lists
            'seelink': 'TMM',
            'seemodule': 'QTM',
            'seepep': 'TMM',
            'seerfc': 'TTM',
            'seetext': 'M',
            'seetitle': 'OMM',
            'seeurl': 'MM',
        },

        DescLineCommandNode: {
            # additional items for ...desc
            'funcline': 'TM',
            'funclineni': 'TM',
            'methodline': 'QTM',
            'methodlineni': 'QTM',
            'memberline': 'QT',
            'memberlineni': 'QT',
            'dataline': 'T',
            'datalineni': 'T',
            'cfuncline': 'MTM',
            'cmemberline': 'TTT',
            'csimplemacroline': 'T',
            'ctypeline': 'QT',
            'cvarline': 'TT',
        },

        InlineNode: {
            # specials
            'footnote': 'M',
            'frac': 'TT',
            'refmodule': 'QT',
            'citetitle': 'QT',
            'ulink': 'MT',
            'url': 'M',

            # mapped to normal
            'textrm': 'M',
            'b': 'M',
            'email': 'M', # email addresses are recognized by ReST

            # mapped to **strong**
            'textbf': 'M',
            'strong': 'M',

            # mapped to *emphasized*
            'textit': 'M',
            'emph': 'M',

            # mapped to ``code``
            'bfcode': 'M',
            'code': 'M',
            'samp': 'M',
            'character': 'M',
            'texttt': 'M',

            # mapped to `default role`
            'var': 'M',

            # mapped to [brackets]
            'optional': 'M',

            # mapped to :role:`text`
            'cdata': 'M',
            'cfunction': 'M',      # -> :cfunc:
            'class': 'M',
            'command': 'M',
            'constant': 'M',       # -> :const:
            'csimplemacro': 'M',   # -> :cmacro:
            'ctype': 'M',
            'data': 'M',           # NEW
            'dfn': 'M',
            'envvar': 'M',
            'exception': 'M',      # -> :exc:
            'file': 'M',
            'filenq': 'M',
            'filevar': 'M',
            'function': 'M',       # -> :func:
            'grammartoken': 'M',   # -> :token:
            'guilabel': 'M',
            'kbd': 'M',
            'keyword': 'M',
            'mailheader': 'M',
            'makevar': 'M',
            'manpage': 'MM',
            'member': 'M',
            'menuselection': 'M',
            'method': 'M',         # -> :meth:
            'mimetype': 'M',
            'module': 'M',         # -> :mod:
            'newsgroup': 'M',
            'option': 'M',
            'pep': 'M',
            'program': 'M',
            'programopt': 'M',     # -> :option:
            'longprogramopt': 'M', # -> :option:
            'ref': 'T',
            'regexp': 'M',
            'rfc': 'M',
            'token': 'M',

            'NULL': '',
            # these are defined via substitutions
            'shortversion': '',
            'version': '',
            'today': '',
        },

        SimpleCmdNode: {
            # these are directly mapped to text
            'AA': '', # A as in Angstrom
            'ASCII': '',
            'C': '',
            'Cpp': '',
            'EOF': '',
            'LaTeX': '',
            'POSIX': '',
            'UNIX': '',
            'Unix': '',
            'backslash': '',
            'copyright': '',
            'e': '', # backslash
            'geq': '',
            'infinity': '',
            'ldots': '',
            'leq': '',
            'moreargs': '',
            'pi': '',
            'plusminus': '',
            'sub': '', # menu separator
            'textbackslash': '',
            'textunderscore': '',
            'texteuro': '',
            'textasciicircum': '',
            'textasciitilde': '',
            'textgreater': '',
            'textless': '',
            'textbar': '',
            'tilde': '',
            'unspecified': '',
        },

        IndexNode: {
            'bifuncindex': 'T',
            'exindex': 'T',
            'kwindex': 'T',
            'obindex': 'T',
            'opindex': 'T',
            'refmodindex': 'T',
            'refexmodindex': 'T',
            'refbimodindex': 'T',
            'refstmodindex': 'T',
            'stindex': 'T',
            'index': 'M',
            'indexii': 'TT',
            'indexiii': 'TTT',
            'indexiv': 'TTTT',
            'ttindex': 'T',
            'withsubitem': 'TM',
        },

        # These can be safely ignored
        EmptyNode: {
            'setindexsubitem': 'T',
            'tableofcontents': '',
            'makeindex': '',
            'makemodindex': '',
            'maketitle': '',
            'appendix': '',
            'documentclass': 'OM',
            'usepackage': 'OM',
            'noindent': '',
            'protect': '',
            'ifhtml': '',
            'fi': '',
        },
    }

    generic_envs = {
        EnvironmentNode: {
            # generic LaTeX environments
            'abstract': '',
            'quote': '',
            'quotation': '',

            'notice': 'Q',
            'seealso': '',
            'seealso*': '',
        },

        DescEnvironmentNode: {
            # information units
            'datadesc': 'T',
            'datadescni': 'T',
            'excclassdesc': 'TM',
            'excdesc': 'T',
            'funcdesc': 'TM',
            'funcdescni': 'TM',
            'classdesc': 'TM',
            'classdesc*': 'T',
            'memberdesc': 'QT',
            'memberdescni': 'QT',
            'methoddesc': 'QMM',
            'methoddescni': 'QMM',
            'opcodedesc': 'TT',

            'cfuncdesc': 'MTM',
            'cmemberdesc': 'TTT',
            'csimplemacrodesc': 'T',
            'ctypedesc': 'QT',
            'cvardesc': 'TT',
        },
    }

    # ------------------------- special handlers -----------------------------

    def handle_special_command(self, cmdname):
        if cmdname in '{}%$^#&_ ':
            # these are just escapes for special LaTeX commands
            return TextNode(cmdname)
        elif cmdname in '\'`~"c':
            # accents and umlauts
            nextl, nextt, nextv, nextr = self.tokens.next()
            if nextt == 'bgroup':
                _, nextt, _, _ = self.tokens.next()
                if nextt != 'egroup':
                    raise ParserError('wrong argtype for \\%s' % cmdname, nextl)
                return TextNode(cmdname)
            if nextt != 'text':
                # not nice, but {\~} = ~
                self.tokens.push((nextl, nextt, nextv, nextr))
                return TextNode(cmdname)
            c = umlaut(cmdname, nextv[0])
            self.tokens.push((nextl, nextt, nextv[1:], nextr[1:]))
            return TextNode(c)
        elif cmdname == '\\':
            return BreakNode()
        raise ParserError('no handler for \\%s command' % cmdname,
                          self.tokens.peek()[0])

    def handle_begin(self):
        envname, = self.parse_args('begin', 'T')
        handler = getattr(self, 'handle_%s_env' % envname.text, None)
        if not handler:
            raise ParserError('no handler for %s environment' % envname.text,
                              self.tokens.peek()[0])
        return handler()

    # ------------------------- command handlers -----------------------------

    def mk_metadata_handler(self, name, mdname=None):
        if mdname is None:
            mdname = name
        def handler(self):
            data, = self.parse_args('\\'+name, 'M')
            self.rootnode.params[mdname] = data
            return EmptyNode()
        return handler

    handle_title = mk_metadata_handler(None, 'title')
    handle_author = mk_metadata_handler(None, 'author')
    handle_authoraddress = mk_metadata_handler(None, 'authoraddress')
    handle_date = mk_metadata_handler(None, 'date')
    handle_release = mk_metadata_handler(None, 'release')
    handle_setshortversion = mk_metadata_handler(None, 'setshortversion',
                                                 'shortversion')
    handle_setreleaseinfo = mk_metadata_handler(None, 'setreleaseinfo',
                                                'releaseinfo')

    def handle_note(self):
        note = self.parse_args('\\note', 'M')[0]
        return EnvironmentNode('notice', [TextNode('note')], note)

    def handle_warning(self):
        warning = self.parse_args('\\warning', 'M')[0]
        return EnvironmentNode('notice', [TextNode('warning')], warning)

    def handle_ifx(self):
        for l, t, v, r in self.tokens:
            if t == 'command' and v == 'fi':
                break
        return EmptyNode()

    def handle_c(self):
        return self.handle_special_command('c')

    def handle_mbox(self):
        return self.parse_args('\\mbox', 'M')[0]

    def handle_leftline(self):
        return self.parse_args('\\leftline', 'M')[0]

    def handle_Large(self):
        return self.parse_args('\\Large', 'M')[0]

    def handle_pytype(self):
        # \pytype{x} is synonymous to \class{x} now
        return self.handle_class()

    def handle_nodename(self):
        return self.handle_label()

    def handle_verb(self):
        # skip delimiter
        l, t, v, r = self.tokens.next()
        l, t, v, r = self.tokens.next()
        assert t == 'text'
        node = InlineNode('code', [TextNode(r)])
        # skip delimiter
        l, t, v, r = self.tokens.next()
        return node

    def handle_locallinewidth(self):
        return EmptyNode()

    def handle_linewidth(self):
        return EmptyNode()

    def handle_setlength(self):
        self.parse_args('\\setlength', 'MM')
        return EmptyNode()

    def handle_stmodindex(self):
        arg, = self.parse_args('\\stmodindex', 'T')
        return CommandNode('declaremodule', [EmptyNode(),
                                             TextNode(u'standard'),
                                             arg])

    def handle_indexname(self):
        return EmptyNode()

    def handle_renewcommand(self):
        self.parse_args('\\renewcommand', 'MM')
        return EmptyNode()

    # ------------------------- environment handlers -------------------------

    def handle_document_env(self):
        return self.parse_until(self.environment_end)

    handle_sloppypar_env = handle_document_env
    handle_flushleft_env = handle_document_env
    handle_math_env = handle_document_env

    def handle_verbatim_env(self):
        text = []
        for l, t, v, r in self.tokens:
            if t == 'command' and v == 'end' :
                tok = self.tokens.peekmany(3)
                if tok[0][1] == 'bgroup' and \
                   tok[1][1] == 'text' and \
                   tok[1][2] == 'verbatim' and \
                   tok[2][1] == 'egroup':
                    self.tokens.popmany(3)
                    break
            text.append(r)
        return VerbatimNode(TextNode(''.join(text)))

    # involved math markup must be corrected manually
    def handle_displaymath_env(self):
        text = ['XXX: translate this math']
        for l, t, v, r in self.tokens:
            if t == 'command' and v == 'end' :
                tok = self.tokens.peekmany(3)
                if tok[0][1] == 'bgroup' and \
                   tok[1][1] == 'text' and \
                   tok[1][2] == 'displaymath' and \
                   tok[2][1] == 'egroup':
                    self.tokens.popmany(3)
                    break
            text.append(r)
        return VerbatimNode(TextNode(''.join(text)))

    # alltt is different from verbatim because it allows markup
    def handle_alltt_env(self):
        nodelist = NodeList()
        for l, t, v, r in self.tokens:
            if self.environment_end(t, v):
                break
            if t == 'command':
                if len(v) == 1 and not v.isalpha():
                    nodelist.append(self.handle_special_command(v))
                    continue
                handler = getattr(self, 'handle_' + v, None)
                if not handler:
                    raise ParserError('no handler for \\%s command' % v, l)
                nodelist.append(handler())
            elif t == 'comment':
                nodelist.append(CommentNode(v))
            else:
                # all else is appended raw
                nodelist.append(TextNode(r))
        return VerbatimNode(nodelist.flatten())

    def handle_itemize_env(self, nodetype=ItemizeNode):
        items = []
        # a usecase for nonlocal :)
        running = [False]

        def item_condition(t, v, bracelevel):
            if self.environment_end(t, v):
                del running[:]
                return True
            if t == 'command' and v == 'item':
                return True
            return False

        # the text until the first \item is discarded
        self.parse_until(item_condition)
        while running:
            itemname, = self.parse_args('\\item', 'O')
            itemcontent = self.parse_until(item_condition)
            items.append([itemname, itemcontent])
        return nodetype(items)

    def handle_enumerate_env(self):
        return self.handle_itemize_env(EnumerateNode)

    def handle_description_env(self):
        return self.handle_itemize_env(DescriptionNode)

    def handle_definitions_env(self):
        items = []
        running = [False]

        def item_condition(t, v, bracelevel):
            if self.environment_end(t, v):
                del running[:]
                return True
            if t == 'command' and v == 'term':
                return True
            return False

        # the text until the first \item is discarded
        self.parse_until(item_condition)
        while running:
            itemname, = self.parse_args('\\term', 'M')
            itemcontent = self.parse_until(item_condition)
            items.append([itemname, itemcontent])
        return DefinitionsNode(items)

    def mk_table_handler(self, envname, numcols):
        def handle_table(self):
            args = self.parse_args('table'+envname, 'TT' + 'M'*numcols)
            firstcolformat = args[1].text
            headings = args[2:]
            lines = []
            for l, t, v, r in self.tokens:
                # XXX: everything outside of \linexxx is lost here
                if t == 'command':
                    if v == 'line'+envname:
                        lines.append(self.parse_args('\\line'+envname,
                                                     'M'*numcols))
                    elif v == 'end':
                        arg = self.parse_args('\\end', 'T')
                        assert arg[0].text.endswith('table'+envname), arg[0].text
                        break
            for line in lines:
                if not empty(line[0]):
                    line[0] = InlineNode(firstcolformat, [line[0]])
            return TableNode(numcols, headings, lines)
        return handle_table

    handle_tableii_env = mk_table_handler(None, 'ii', 2)
    handle_longtableii_env = handle_tableii_env
    handle_tableiii_env = mk_table_handler(None, 'iii', 3)
    handle_longtableiii_env = handle_tableiii_env
    handle_tableiv_env = mk_table_handler(None, 'iv', 4)
    handle_longtableiv_env = handle_tableiv_env
    handle_tablev_env = mk_table_handler(None, 'v', 5)
    handle_longtablev_env = handle_tablev_env

    def handle_productionlist_env(self):
        env_args = self.parse_args('productionlist', 'Q')
        items = []
        for l, t, v, r in self.tokens:
            # XXX: everything outside of \production is lost here
            if t == 'command':
                if v == 'production':
                    items.append(self.parse_args('\\production', 'TM'))
                elif v == 'productioncont':
                    args = self.parse_args('\\productioncont', 'M')
                    args.insert(0, EmptyNode())
                    items.append(args)
                elif v == 'end':
                    arg = self.parse_args('\\end', 'T')
                    assert arg[0].text == 'productionlist'
                    break
        node = ProductionListNode(items)
        # the argument specifies a production group
        node.arg = env_args[0]
        return node

    def environment_end(self, t, v, bracelevel=0):
        if t == 'command' and v == 'end':
            self.parse_args('\\end', 'T')
            return True
        return False
