exclude_patterns = ['_build']

latex_elements = {
    'preamble': r'''
\makeatletter
\def\dividetwolengths#1#2{\the\dimexpr
    \numexpr65536*\dimexpr#1\relax/\dimexpr#2\relax sp}%
\newwrite\out
\immediate\openout\out=\jobname-dimensions.txt
\def\toout{\immediate\write\out}
\def\getWfromoptions #1width=#2,#3\relax{\def\WidthFromOption{#2}}%
\def\getHfromoptions #1height=#2,#3\relax{\def\HeightFromOption{#2}}%
\def\tempincludegraphics[#1]#2{%
    \sphinxsafeincludegraphics[#1]{#2}%
    \edef\obtainedratio
       {\dividetwolengths\spx@image@requiredheight\spx@image@requiredwidth}%
    \getWfromoptions#1,width=,\relax
    \getHfromoptions#1,height=,\relax
    \def\ratiocheck{}%
    \ifx\WidthFromOption\empty\else
    \ifx\HeightFromOption\empty\else
      \edef\askedforratio{\dividetwolengths\HeightFromOption\WidthFromOption}%
      \edef\ratiocheck{\dividetwolengths\obtainedratio\askedforratio}%
    \fi\fi
    \toout{original options = #1^^J%
           width = \the\dimexpr\spx@image@requiredwidth,
           linewidth = \the\linewidth^^J%
           height = \the\dimexpr\spx@image@requiredheight,
           maxheight = \the\spx@image@maxheight^^J%
           obtained  H/W = \obtainedratio^^J%
    \ifx\ratiocheck\empty
    \else
           asked for H/W = \askedforratio^^J%
           ratio of ratios = \ratiocheck^^J%
    \fi
          }%
    \ifx\ratiocheck\empty
    \else
      \ifpdfabsdim\dimexpr\ratiocheck-1pt\relax > 0.01pt
        \ASPECTRATIOERROR
      \fi
    \fi
}
\def\sphinxincludegraphics#1#{\tempincludegraphics#1}
\makeatother
''',
}
