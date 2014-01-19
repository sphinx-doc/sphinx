# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS   =
SPHINXBUILD  = python ../sphinx-build.py
SPHINXPROJ   = sphinx
BUILDDIR     = _build

# User-friendly check for sphinx-build
ifeq ($(shell which $(SPHINXBUILD) >/dev/null 2>&1; echo $$?), 1)
$(error \
The '$(SPHINXBUILD)' command was not found. Make sure you have Sphinx \
installed, then set the SPHINXBUILD environment variable to point \
to the full path of the '$(SPHINXBUILD)' executable. Alternatively you \
can add the directory with the executable to your PATH. \
If you don't have Sphinx installed, grab it from http://sphinx-doc.org/)
endif

help:
	@$(SPHINXBUILD) -M help "$(BUILDDIR)" $(SPHINXOPTS) $(O)

%:
	@$(SPHINXBUILD) -M $@ "$(BUILDDIR)" $(SPHINXOPTS) $(O)
