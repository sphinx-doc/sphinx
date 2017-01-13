PYTHON ?= python

.PHONY: all style-check clean clean-pyc clean-patchfiles clean-backupfiles \
        clean-generated pylint reindent test covertest build

DONT_CHECK = -i build -i dist -i sphinx/style/jquery.js \
             -i sphinx/pycode/pgen2 -i sphinx/util/smartypants.py \
             -i .ropeproject -i doc/_build -i tests/path.py \
             -i utils/convert.py \
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

clean: clean-pyc clean-pycache clean-patchfiles clean-backupfiles clean-generated clean-testfiles clean-buildfiles clean-mypyfiles

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
	find . -name '*.swp' -exec rm -f {} +
	find . -name '*.swo' -exec rm -f {} +

clean-generated:
	find . -name '.DS_Store' -exec rm -f {} +
	rm -f doc/_build/
	rm -f sphinx/pycode/*.pickle
	rm -f utils/*3.py*
	rm -f utils/regression_test.js

clean-testfiles:
	rm -rf tests/.coverage
	rm -rf tests/build
	rm -rf .tox/
	rm -rf .cache/

clean-buildfiles:
	rm -rf build

clean-mypyfiles:
	rm -rf .mypy_cache/

pylint:
	@pylint --rcfile utils/pylintrc sphinx

reindent:
	@$(PYTHON) utils/reindent.py -r -n .

test:
	@cd tests; $(PYTHON) run.py --ignore py35 -v $(TEST)

test-async:
	@cd tests; $(PYTHON) run.py -v $(TEST)

covertest:
	@cd tests; $(PYTHON) run.py -v --cov=sphinx --junitxml=.junit.xml $(TEST)

build:
	@$(PYTHON) setup.py build
