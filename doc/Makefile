# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS   =
SPHINXBUILD  = python ../sphinx-build.py
SPHINXPROJ   = sphinx
SOURCEDIR    = .
BUILDDIR     = _build

# Has to be explicit, otherwise we don't get "make" without targets right.
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%:
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
