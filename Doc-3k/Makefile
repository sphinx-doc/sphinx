#
# Makefile for Python documentation
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#

PYTHON  = python
SVNROOT = http://svn.python.org/projects

.PHONY: help checkout html web htmlhelp clean

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html  to make standalone HTML files"
	@echo "  web   to make file usable by Sphinx.web"
	@echo "  htmlhelp to make HTML files and a HTML help project"

checkout:
	@if [ ! -d tools/sphinx ]; then \
	  echo "Checking out Sphinx..."; \
	  svn checkout $(SVNROOT)/doctools/trunk/sphinx tools/sphinx; \
	fi
	@if [ ! -d tools/docutils ]; then \
	  echo "Checking out Docutils..."; \
	  svn checkout $(SVNROOT)/external/docutils-0.4/docutils tools/docutils; \
	fi
	@if [ ! -d tools/pygments ]; then \
	  echo "Checking out Pygments..."; \
	  svn checkout $(SVNROOT)/external/Pygments-0.8.1/pygments tools/pygments; \
	fi

update:
	svn update tools/sphinx
	svn update tools/docutils
	svn update tools/pygments

html: checkout
	mkdir -p build/html build/doctrees
	$(PYTHON) tools/sphinx-build.py -bhtml -dbuild/doctrees . build/html
	@echo
	@echo "Build finished. The HTML pages are in build/html."

web: checkout
	mkdir -p build/web build/doctrees
	$(PYTHON) tools/sphinx-build.py -bweb -dbuild/doctrees . build/web
	@echo
	@echo "Build finished; now you can run"
	@echo "  PYTHONPATH=tools $(PYTHON) -m sphinx.web build/web"
	@echo "to start the server."

htmlhelp: checkout
	mkdir -p build/hhp build/doctrees
	$(PYTHON) tools/sphinx-build.py -bhtmlhelp -dbuild/doctrees . build/hhp
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      "build/hhp/pydoc.hhp project file."

clean:
	-rm -rf build/*
	-rm -rf tools/sphinx
