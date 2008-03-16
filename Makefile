PYTHON ?= python

export PYTHONPATH = $(shell echo "$$PYTHONPATH"):./sphinx

.PHONY: all check clean clean-pyc pylint reindent testserver

all: clean-pyc check

check:
	@$(PYTHON) utils/check_sources.py -i sphinx/style/jquery.js sphinx
	@$(PYTHON) utils/check_sources.py converter

clean: clean-pyc clean-patchfiles

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

clean-patchfiles:
	find . -name '*.orig' -exec rm -f {} +
	find . -name '*.rej' -exec rm -f {} +

pylint:
	@pylint --rcfile utils/pylintrc sphinx

reindent:
	@$(PYTHON) utils/reindent.py -r -B .
