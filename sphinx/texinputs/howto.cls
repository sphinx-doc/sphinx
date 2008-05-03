%
% howto.cls for Sphinx
%

\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{howto}[2008/05/01 Document class (Sphinx HOWTO)]

\RequirePackage{fancybox}

% Pass all given class options to the parent class.
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[twoside]{article}


% Set some sane defaults for section numbering depth and TOC depth.  You can
% reset these counter in your preamble.
%
\setcounter{secnumdepth}{2}


% The "fancyhdr" package makes nicer page footers reasonable to implement, and
% is used to put the chapter and section information in the footers.
%
\RequirePackage{fancyhdr}

% This gives us all the Python-specific markup that we really want.  This should
% come last.  Do not change this.
%
\RequirePackage{sphinx}

% This comes after python.sty because it otherwise defines its own "seealso"
% command.
%
\RequirePackage{makeidx}

% Need to do one of these....
\newcommand{\py@doHorizontalRule}{\rule{\textwidth}{1pt}}


% Change the title page to look a bit better, and fit in with the fncychap
% ``Bjarne'' style a bit better.
%
\renewcommand{\maketitle}{
  \py@doHorizontalRule
  \ifpdf
    \begingroup
    % This \def is required to deal with multi-line authors; it
    % changes \\ to ', ' (comma-space), making it pass muster for
    % generating document info in the PDF file.
    \def\\{, }
    \pdfinfo{
      /Author (\@author)
      /Title (\@title)
    }
    \endgroup
  \fi
  \begin{flushright}
    \sphinxlogo%
    {\rm\Huge\py@HeaderFamily \@title} \par
    {\em\large\py@HeaderFamily \py@release\releaseinfo} \par
    \vspace{25pt}
    {\Large\py@HeaderFamily \@author} \par
    \vspace{25pt}
    \@date \par
    \py@authoraddress \par
  \end{flushright}
  \@thanks
  \setcounter{footnote}{0}
  \let\thanks\relax\let\maketitle\relax
  %\gdef\@thanks{}\gdef\@author{}\gdef\@title{}
}


\let\py@OldTableofcontents=\tableofcontents
\renewcommand{\tableofcontents}{
  \begingroup
    \parskip = 0mm
    \py@OldTableofcontents
  \endgroup
  \py@doHorizontalRule
  \vspace{12pt}
}  

% Fix the theindex environment to add an entry to the Table of Contents; this is
% much nicer than just having to jump to the end of the book and flip around,
% especially with multiple indexes.
%
\let\py@OldTheindex=\theindex
\renewcommand{\theindex}{
  \clearpage
  \phantomsection
  \py@OldTheindex
  \addcontentsline{toc}{section}{\indexname}
}

\@ifundefined{fancyhf}{
  \pagestyle{plain}}{
  \pagestyle{normal}}		% start this way; change for
\pagenumbering{arabic}		% ToC & chapters

\thispagestyle{empty}
