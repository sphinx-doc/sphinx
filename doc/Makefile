# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS   =
SPHINXBUILD  = python ../sphinx-build.py
PAPER        =

PAPEROPT_a4      = -D latex_paper_size=a4
PAPEROPT_letter  = -D latex_paper_size=letter
ALLSPHINXOPTS = -d _build/doctrees $(PAPEROPT_$(PAPER)) \
                $(SPHINXOPTS) .

.PHONY: help clean html dirhtml pickle htmlhelp qthelp latex changes linkcheck doctest

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html      to make standalone HTML files"
	@echo "  dirhtml   to make HTML files called index.html in directories"
	@echo "  pickle    to make pickle files"
	@echo "  json      to make json files"
	@echo "  htmlhelp  to make HTML files and a HTML help project"
	@echo "  latex     to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  changes   to make an overview over all changed/added/deprecated items"
	@echo "  linkcheck to check all external links for integrity"

clean:
	-rm -rf _build/*

html:
	mkdir -p _build/html _build/doctrees
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) _build/html
	@echo
	@echo "Build finished. The HTML pages are in _build/html."

dirhtml:
	mkdir -p _build/dirhtml _build/doctrees
	$(SPHINXBUILD) -b dirhtml $(ALLSPHINXOPTS) _build/dirhtml
	@echo
	@echo "Build finished. The HTML pages are in _build/dirhtml."

text:
	mkdir -p _build/text _build/doctrees
	$(SPHINXBUILD) -b text $(ALLSPHINXOPTS) _build/text
	@echo
	@echo "Build finished."

pickle:
	mkdir -p _build/pickle _build/doctrees
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) _build/pickle

json:
	mkdir -p _build/json _build/doctrees
	$(SPHINXBUILD) -b json $(ALLSPHINXOPTS) _build/json

htmlhelp:
	mkdir -p _build/htmlhelp _build/doctrees
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) _build/htmlhelp
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in _build/htmlhelp."

qthelp:
	mkdir -p _build/qthelp _build/doctrees
	$(SPHINXBUILD) -b qthelp $(ALLSPHINXOPTS) _build/qthelp
	@echo
	@echo "Build finished; now you can run qcollectiongenerator with the" \
	      ".qhcp project file in build/qthelp."
	@echo "# qcollectiongenerator _build/qthelp/Sphinx.qhcp"
	@echo "To view the help collection:"
	@echo "# assistant -collectionFile _build/qthelp/Sphinx.qhc"

latex:
	mkdir -p _build/latex _build/doctrees
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) _build/latex
	@echo
	@echo "Build finished; the LaTeX files are in _build/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."

changes:
	mkdir -p _build/changes _build/doctrees
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) _build/changes
	@echo
	@echo "The overview file is in _build/changes."

linkcheck:
	mkdir -p _build/linkcheck _build/doctrees
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) _build/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in _build/linkcheck/output.txt."

doctest:
	mkdir -p _build/doctest _build/doctrees
	$(SPHINXBUILD) -b doctest $(ALLSPHINXOPTS) _build/doctest
