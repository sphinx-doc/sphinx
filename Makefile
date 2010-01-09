PYTHON ?= python

export PYTHONPATH = $(shell echo "$$PYTHONPATH"):./sphinx

.PHONY: all check clean clean-pyc clean-patchfiles pylint reindent test

all: clean-pyc check test

check:
	@$(PYTHON) utils/check_sources.py -i build -i dist -i sphinx/style/jquery.js \
		-i sphinx/pycode/pgen2 -i sphinx/util/smartypants.py -i .ropeproject \
		-i doc/_build -i ez_setup.py -i tests/path.py -i tests/coverage.py .

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

test:
	@cd tests; $(PYTHON) run.py -d -m '^[tT]est' $(TEST)

covertest:
	@cd tests; $(PYTHON) run.py -d -m '^[tT]est' --with-coverage --cover-package=sphinx $(TEST)
