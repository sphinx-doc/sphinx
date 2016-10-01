PYTHON ?= python

.PHONY: all style-check clean clean-pyc clean-patchfiles clean-backupfiles \
        clean-generated pylint reindent test covertest build

DONT_CHECK = -i build -i dist -i sphinx/style/jquery.js \
             -i sphinx/pycode/pgen2 -i sphinx/util/smartypants.py \
             -i .ropeproject -i doc/_build -i tests/path.py \
             -i tests/coverage.py -i utils/convert.py \
             -i tests/typing_test_data.py \
             -i tests/test_autodoc_py35.py \
             -i tests/roots/test-warnings/undecodable.rst \
             -i tests/build \
             -i tests/roots/test-warnings/undecodable.rst \
             -i sphinx/search/da.py \
             -i sphinx/search/de.py \
             -i sphinx/search/en.py \
             -i sphinx/search/es.py \
             -i sphinx/search/fi.py \
             -i sphinx/search/fr.py \
             -i sphinx/search/hu.py \
             -i sphinx/search/it.py \
             -i sphinx/search/ja.py \
             -i sphinx/search/nl.py \
             -i sphinx/search/no.py \
             -i sphinx/search/pt.py \
             -i sphinx/search/ro.py \
             -i sphinx/search/ru.py \
             -i sphinx/search/sv.py \
             -i sphinx/search/tr.py \
             -i .tox

all: clean-pyc clean-backupfiles style-check test

style-check:
	@$(PYTHON) utils/check_sources.py $(DONT_CHECK) .

clean: clean-pyc clean-pycache clean-patchfiles clean-backupfiles clean-generated clean-testfiles clean-buildfiles

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +

clean-pycache:
	find . -name __pycache__ -exec rm -rf {} +

clean-patchfiles:
	find . -name '*.orig' -exec rm -f {} +
	find . -name '*.rej' -exec rm -f {} +

clean-backupfiles:
	find . -name '*~' -exec rm -f {} +
	find . -name '*.bak' -exec rm -f {} +

clean-generated:
	rm -f utils/*3.py*

clean-testfiles:
	rm -rf tests/build
	rm -rf .tox/

clean-buildfiles:
	rm -rf build

pylint:
	@pylint --rcfile utils/pylintrc sphinx

reindent:
	@$(PYTHON) utils/reindent.py -r -n .

test:
	@cd tests; $(PYTHON) run.py -I py35 -d -m '^[tT]est' $(TEST)

test-async:
	@cd tests; $(PYTHON) run.py -d -m '^[tT]est' $(TEST)

covertest:
	@cd tests; $(PYTHON) run.py -d -m '^[tT]est' --with-coverage \
		--cover-package=sphinx $(TEST)

build:
	@$(PYTHON) setup.py build
