"""constants for LaTeX builder."""

from __future__ import annotations

from typing import Any

PDFLATEX_DEFAULT_FONTPKG = r'''
\usepackage{tgtermes}
\usepackage{tgheros}
\renewcommand{\ttdefault}{txtt}
'''

PDFLATEX_DEFAULT_FONTPKGMATH = r'''
\usepackage{amssymb}% may become stix2 at some future version
'''

PDFLATEX_DEFAULT_FONTSUBSTITUTION = r'''
\expandafter\ifx\csname T@LGR\endcsname\relax
\else
% LGR was declared as font encoding
  \substitutefont{LGR}{\rmdefault}{cmr}
  \substitutefont{LGR}{\sfdefault}{cmss}
  \substitutefont{LGR}{\ttdefault}{cmtt}
\fi
\expandafter\ifx\csname T@X2\endcsname\relax
  \expandafter\ifx\csname T@T2A\endcsname\relax
  \else
  % T2A was declared as font encoding
    \substitutefont{T2A}{\rmdefault}{cmr}
    \substitutefont{T2A}{\sfdefault}{cmss}
    \substitutefont{T2A}{\ttdefault}{cmtt}
  \fi
\else
% X2 was declared as font encoding
  \substitutefont{X2}{\rmdefault}{cmr}
  \substitutefont{X2}{\sfdefault}{cmss}
  \substitutefont{X2}{\ttdefault}{cmtt}
\fi
'''

XELATEX_DEFAULT_FONTPKG = r'''
\setmainfont{FreeSerif}[
  Extension      = .otf,
  UprightFont    = *,
  ItalicFont     = *Italic,
  BoldFont       = *Bold,
  BoldItalicFont = *BoldItalic
]
\setsansfont{FreeSans}[
  Extension      = .otf,
  UprightFont    = *,
  ItalicFont     = *Oblique,
  BoldFont       = *Bold,
  BoldItalicFont = *BoldOblique,
]
\setmonofont{FreeMono}[
  Extension      = .otf,
  UprightFont    = *,
  ItalicFont     = *Oblique,
  BoldFont       = *Bold,
  BoldItalicFont = *BoldOblique,
]
'''

XELATEX_DEFAULT_FONTPKGMATH = r'''
\usepackage{unicode-math}
\setmathfont{XITSMath-Regular.otf}[
    StylisticSet=1,% choice of shape for "\mathcal"
    BoldFont=XITSMath-Bold.otf,
    ItalicFont=XITS-Italic.otf,% text only (\mathit)
    BoldItalicFont=XITS-BoldItalic.otf,% text only
    NFSSFamily=XITS,
]
\makeatletter
\AtBeginDocument{%
  % work around unicode-math problems with \mathbf{\Gamma} et al.
  \SetMathAlphabet{\mathrm}{normal}{TU}{XITS}{m}{n}
  \SetMathAlphabet{\mathit}{normal}{TU}{XITS}{m}{it}
  \SetMathAlphabet{\mathbf}{normal}{TU}{XITS}{b}{n}
  \SetMathAlphabet{\mathrm}{bold}{TU}{XITS}{b}{n}
  \SetMathAlphabet{\mathit}{bold}{TU}{XITS}{b}{it}
  \SetMathAlphabet{\mathbf}{bold}{TU}{XITS}{b}{n}
  \def\Gamma{Γ}
  \def\Delta{Δ}
  \def\Theta{Θ}
  \def\Lambda{Λ}
  \def\Xi{Ξ}
  \def\Pi{Π}
  \def\Sigma{Σ}
  \def\Upsilon{Υ}
  \def\Phi{Φ}
  \def\Psi{Ψ}
  \def\Omega{Ω}
  % Make subscripts a bit larger for legibility
  \def\defaultscriptratio{.8}
  \def\defaultscriptscriptratio{.6}
  \DeclareMathSizes{9}{9}{7}{5}
  \DeclareMathSizes{\@xpt}{\@xpt}{8}{6}
  \DeclareMathSizes{\@xipt}{\@xipt}{8.76}{6.57}
  \DeclareMathSizes{\@xiipt}{\@xiipt}{9.6}{7.2}
  \DeclareMathSizes{\@xivpt}{\@xivpt}{11.52}{8.64}
}
\makeatother
'''

XELATEX_GREEK_DEFAULT_FONTPKG = (XELATEX_DEFAULT_FONTPKG +
                                 '\n\\newfontfamily\\greekfont{FreeSerif}' +
                                 '\n\\newfontfamily\\greekfontsf{FreeSans}' +
                                 '\n\\newfontfamily\\greekfonttt{FreeMono}')

LUALATEX_DEFAULT_FONTPKG = XELATEX_DEFAULT_FONTPKG
LUALATEX_DEFAULT_FONTPKGMATH = XELATEX_DEFAULT_FONTPKGMATH

DEFAULT_SETTINGS: dict[str, Any] = {
    'latex_engine':    'pdflatex',
    'papersize':       '',
    'pointsize':       '',
    'pxunit':          '.75bp',
    'classoptions':    '',
    'extraclassoptions': '',
    'maxlistdepth':    '',
    'sphinxpkgoptions':     '',
    'sphinxsetup':     '',
    'fvset':           '\\fvset{fontsize=auto}',
    'passoptionstopackages': '',
    'geometry':        '\\usepackage{geometry}',
    'inputenc':        '',
    'utf8extra':       '',
    'cmappkg':         '\\usepackage{cmap}',
    'fontenc':         '\\usepackage[T1]{fontenc}',
    'amsmath':         '\\usepackage{amsmath,amstext}',
    'multilingual':    '',
    'babel':           '\\usepackage{babel}',
    'polyglossia':     '',
    'fontpkg':         PDFLATEX_DEFAULT_FONTPKG,
    'fontpkgmath':     PDFLATEX_DEFAULT_FONTPKGMATH,
    'fontsubstitution': PDFLATEX_DEFAULT_FONTSUBSTITUTION,
    'substitutefont':  '',
    'textcyrillic':    '',
    'textgreek':       '\\usepackage{textalpha}',
    'fncychap':        '\\usepackage[Bjarne]{fncychap}',
    'hyperref':        ('% Include hyperref last.\n'
                        '\\usepackage{hyperref}\n'
                        '% Fix anchor placement for figures with captions.\n'
                        '\\usepackage{hypcap}% it must be loaded after hyperref.\n'
                        '% Set up styles of URL: it should be placed after hyperref.\n'
                        '\\urlstyle{same}'),
    'contentsname':    '',
    'extrapackages':   '',
    'preamble':        '',
    'title':           '',
    'release':         '',
    'author':          '',
    'releasename':     '',
    'makeindex':       '\\makeindex',
    'shorthandoff':    '',
    'maketitle':       '\\sphinxmaketitle',
    'tableofcontents': '\\sphinxtableofcontents',
    'atendofbody':     '',
    'printindex':      '\\printindex',
    'transition':      '\n\n\\bigskip\\hrule\\bigskip\n\n',
    'figure_align':    'htbp',
    'tocdepth':        '',
    'secnumdepth':     '',
}

ADDITIONAL_SETTINGS: dict[Any, dict[str, Any]] = {
    'pdflatex': {
        'inputenc':     '\\usepackage[utf8]{inputenc}',
        'utf8extra':   ('\\ifdefined\\DeclareUnicodeCharacter\n'
                        '% support both utf8 and utf8x syntaxes\n'
                        '  \\ifdefined\\DeclareUnicodeCharacterAsOptional\n'
                        '    \\def\\sphinxDUC#1{\\DeclareUnicodeCharacter{"#1}}\n'
                        '  \\else\n'
                        '    \\let\\sphinxDUC\\DeclareUnicodeCharacter\n'
                        '  \\fi\n'
                        '  \\sphinxDUC{00A0}{\\nobreakspace}\n'
                        '  \\sphinxDUC{2500}{\\sphinxunichar{2500}}\n'
                        '  \\sphinxDUC{2502}{\\sphinxunichar{2502}}\n'
                        '  \\sphinxDUC{2514}{\\sphinxunichar{2514}}\n'
                        '  \\sphinxDUC{251C}{\\sphinxunichar{251C}}\n'
                        '  \\sphinxDUC{2572}{\\textbackslash}\n'
                        '\\fi'),
    },
    'xelatex': {
        'latex_engine': 'xelatex',
        'polyglossia':  '\\usepackage{polyglossia}',
        'babel':        '',
        'fontenc':     ('\\usepackage{fontspec}\n'
                        '\\defaultfontfeatures[\\rmfamily,\\sffamily,\\ttfamily]{}'),
        'fontpkg':      XELATEX_DEFAULT_FONTPKG,
        'fontpkgmath':  XELATEX_DEFAULT_FONTPKGMATH,
        'fvset':        '\\fvset{fontsize=\\small}',
        'fontsubstitution': '',
        'textgreek':    '',
        'utf8extra':   ('\\catcode`^^^^00a0\\active\\protected\\def^^^^00a0'
                        '{\\leavevmode\\nobreak\\ }'),
    },
    'lualatex': {
        'latex_engine': 'lualatex',
        'polyglossia':  '\\usepackage{polyglossia}',
        'babel':        '',
        'fontenc':     ('\\usepackage{fontspec}\n'
                        '\\defaultfontfeatures[\\rmfamily,\\sffamily,\\ttfamily]{}'),
        'fontpkg':      LUALATEX_DEFAULT_FONTPKG,
        'fontpkgmath':  LUALATEX_DEFAULT_FONTPKGMATH,
        'fvset':        '\\fvset{fontsize=\\small}',
        'fontsubstitution': '',
        'textgreek':    '',
        'utf8extra':   ('\\catcode`^^^^00a0\\active\\protected\\def^^^^00a0'
                        '{\\leavevmode\\nobreak\\ }'),
    },
    'platex': {
        'latex_engine': 'platex',
        'babel':        '',
        'classoptions': ',dvipdfmx',
        'fontpkg':      PDFLATEX_DEFAULT_FONTPKG,
        'fontpkgmath':  PDFLATEX_DEFAULT_FONTPKGMATH,
        'fontsubstitution': '',
        'textgreek':    '',
        'fncychap':     '',
        'geometry':     '\\usepackage[dvipdfm]{geometry}',
    },
    'uplatex': {
        'latex_engine': 'uplatex',
        'babel':        '',
        'classoptions': ',dvipdfmx',
        'fontpkg':      PDFLATEX_DEFAULT_FONTPKG,
        'fontpkgmath':  PDFLATEX_DEFAULT_FONTPKGMATH,
        'fontsubstitution': '',
        'textgreek':    '',
        'fncychap':     '',
        'geometry':     '\\usepackage[dvipdfm]{geometry}',
    },

    # special settings for latex_engine + language_code
    ('lualatex', 'fr'): {
        # use babel instead of polyglossia by default
        'polyglossia':  '',
        'babel':        '\\usepackage{babel}',
    },
    ('xelatex', 'fr'): {
        # use babel instead of polyglossia by default
        'polyglossia':  '',
        'babel':        '\\usepackage{babel}',
    },
    ('xelatex', 'zh'): {
        'polyglossia':  '',
        'babel':        '\\usepackage{babel}',
        'fontenc':      '\\usepackage{xeCJK}',
        # set formatcom=\xeCJKVerbAddon to prevent xeCJK from adding extra spaces in
        # fancyvrb Verbatim environment.
        'fvset':        '\\fvset{fontsize=\\small,formatcom=\\xeCJKVerbAddon}',
    },
    ('xelatex', 'el'): {
        'fontpkg':      XELATEX_GREEK_DEFAULT_FONTPKG,
    },
}


SHORTHANDOFF = r'''
\ifdefined\shorthandoff
  \ifnum\catcode`\=\string=\active\shorthandoff{=}\fi
  \ifnum\catcode`\"=\active\shorthandoff{"}\fi
\fi
'''
