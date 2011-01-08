# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS   =
SPHINXBUILD  = python ../sphinx-build.py
PAPER        =

PAPEROPT_a4      = -D latex_paper_size=a4
PAPEROPT_letter  = -D latex_paper_size=letter
ALLSPHINXOPTS    = -d _build/doctrees $(PAPEROPT_$(PAPER)) \
                   $(SPHINXOPTS) $(O) .
I18NSPHINXOPTS   = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) $(O) .

.PHONY: help clean html dirhtml singlehtml text man pickle json htmlhelp \
	qthelp devhelp epub latex latexpdf changes linkcheck doctest

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html       to make standalone HTML files"
	@echo "  dirhtml    to make HTML files called index.html in directories"
	@echo "  singlehtml to make one big HTML file"
	@echo "  text       to make text files"
	@echo "  man        to make manual pages"
	@echo "  pickle     to make pickle files"
	@echo "  json       to make json files"
	@echo "  htmlhelp   to make HTML files and a HTML help project"
	@echo "  qthelp     to make Qt help files and project"
	@echo "  devhelp    to make Devhelp files and project"
	@echo "  epub       to make an epub file"
	@echo "  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  latexpdf   to make LaTeX files and run pdflatex"
	@echo "  texinfo    to make Texinfo files"
	@echo "  info       to make Texinfo files and run them through makeinfo"
	@echo "  gettext    to make PO message catalogs"
	@echo "  changes    to make an overview over all changed/added/deprecated items"
	@echo "  linkcheck  to check all external links for integrity"

clean:
	-rm -rf _build/*

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) _build/html
	@echo
	@echo "Build finished. The HTML pages are in _build/html."

dirhtml:
	$(SPHINXBUILD) -b dirhtml $(ALLSPHINXOPTS) _build/dirhtml
	@echo
	@echo "Build finished. The HTML pages are in _build/dirhtml."

singlehtml:
	$(SPHINXBUILD) -b singlehtml $(ALLSPHINXOPTS) _build/singlehtml
	@echo
	@echo "Build finished. The HTML page is in _build/singlehtml."

text:
	$(SPHINXBUILD) -b text $(ALLSPHINXOPTS) _build/text
	@echo
	@echo "Build finished."

man:
	$(SPHINXBUILD) -b man $(ALLSPHINXOPTS) _build/man
	@echo
	@echo "Build finished."

pickle:
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) _build/pickle
	@echo
	@echo "Build finished."

json:
	$(SPHINXBUILD) -b json $(ALLSPHINXOPTS) _build/json
	@echo
	@echo "Build finished."

htmlhelp:
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) _build/htmlhelp
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in _build/htmlhelp."

qthelp:
	$(SPHINXBUILD) -b qthelp $(ALLSPHINXOPTS) _build/qthelp
	@echo
	@echo "Build finished; now you can run qcollectiongenerator with the" \
	      ".qhcp project file in build/qthelp."
	@echo "# qcollectiongenerator _build/qthelp/Sphinx.qhcp"
	@echo "To view the help collection:"
	@echo "# assistant -collectionFile _build/qthelp/Sphinx.qhc"

devhelp:
	$(SPHINXBUILD) -b devhelp $(ALLSPHINXOPTS) _build/devhelp
	@echo
	@echo "Build finished."
	@echo "To view the help file:"
	@echo "# mkdir -p $$HOME/.local/share/devhelp/sphinx"
	@echo "# ln -s _build/devhelp $$HOME/.local/share/devhelp/sphinx"
	@echo "# devhelp"

epub:
	$(SPHINXBUILD) -b epub $(ALLSPHINXOPTS) _build/epub
	@echo
	@echo "Build finished. The epub file is in _build/epub."

latex:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) _build/latex
	@echo
	@echo "Build finished; the LaTeX files are in _build/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."

latexpdf:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) _build/latex
	@echo "Running LaTeX files through pdflatex..."
	make -C _build/latex all-pdf
	@echo "pdflatex finished; the PDF files are in _build/latex."

gettext:
	$(SPHINXBUILD) -b gettext $(I18NSPHINXOPTS) _build/locale
	@echo
	@echo "Build finished. The message catalogs are in _build/locale."

changes:
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) _build/changes
	@echo
	@echo "The overview file is in _build/changes."

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) _build/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in _build/linkcheck/output.txt."

doctest:
	$(SPHINXBUILD) -b doctest $(ALLSPHINXOPTS) _build/doctest

texinfo:
	$(SPHINXBUILD) -b texinfo $(ALLSPHINXOPTS) _build/texinfo
	@echo
	@echo "Build finished. The Texinfo files are in _build/texinfo."
	@echo "Run \`make' in that directory to run these through makeinfo" \
	      "(use \`make info' here to do that automatically)."

info:
	$(SPHINXBUILD) -b texinfo $(ALLSPHINXOPTS) _build/texinfo
	@echo "Running Texinfo files through makeinfo..."
	make -C _build/texinfo info
	@echo "makeinfo finished; the Info files are in _build/texinfo."
