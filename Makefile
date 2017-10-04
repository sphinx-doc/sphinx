PYTHON ?= python

DONT_CHECK = -i .ropeproject \
             -i .tox \
             -i build \
             -i dist \
             -i doc/_build \
             -i sphinx/pycode/pgen2 \
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
             -i sphinx/style/jquery.js \
             -i sphinx/util/smartypants.py \
             -i tests/build \
             -i tests/path.py \
             -i tests/roots/test-directive-code/target.py \
             -i tests/roots/test-warnings/undecodable.rst \
             -i tests/test_autodoc_py35.py \
             -i tests/typing_test_data.py \
             -i utils/convert.py

.PHONY: all
all: clean-pyc clean-backupfiles style-check type-check test

.PHONY: style-check
style-check:
	@PYTHONWARNINGS=all $(PYTHON) utils/check_sources.py $(DONT_CHECK) .

.PHONY: type-check
type-check:
	mypy sphinx/

.PHONY: clean
clean: clean-pyc clean-pycache clean-patchfiles clean-backupfiles clean-generated clean-testfiles clean-buildfiles clean-mypyfiles

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +

.PHONY: clean-pycache
clean-pycache:
	find . -name __pycache__ -exec rm -rf {} +

.PHONY: clean-patchfiles
clean-patchfiles:
	find . -name '*.orig' -exec rm -f {} +
	find . -name '*.rej' -exec rm -f {} +

.PHONY: clean-backupfiles
clean-backupfiles:
	find . -name '*~' -exec rm -f {} +
	find . -name '*.bak' -exec rm -f {} +
	find . -name '*.swp' -exec rm -f {} +
	find . -name '*.swo' -exec rm -f {} +

.PHONY: clean-generated
clean-generated:
	find . -name '.DS_Store' -exec rm -f {} +
	rm -rf Sphinx.egg-info/
	rm -rf doc/_build/
	rm -f sphinx/pycode/*.pickle
	rm -f utils/*3.py*
	rm -f utils/regression_test.js

.PHONY: clean-testfiles
clean-testfiles:
	rm -rf tests/.coverage
	rm -rf tests/build
	rm -rf .tox/
	rm -rf .cache/

.PHONY: clean-buildfiles
clean-buildfiles:
	rm -rf build

.PHONY: clean-mypyfiles
clean-mypyfiles:
	rm -rf .mypy_cache/

.PHONY: pylint
pylint:
	@pylint --rcfile utils/pylintrc sphinx

.PHONY: reindent
reindent:
	@$(PYTHON) utils/reindent.py -r -n .

.PHONY: test
test:
	@cd tests; $(PYTHON) run.py --ignore py35 -v $(TEST)

.PHONY: test-async
test-async:
	@cd tests; $(PYTHON) run.py -v $(TEST)

.PHONY: covertest
covertest:
	@cd tests; $(PYTHON) run.py -v --cov=sphinx --junitxml=.junit.xml $(TEST)

.PHONY: build
build:
	@$(PYTHON) setup.py build

.PHONY: docs
docs:
ifndef target
	  $(info You need to give a provide a target variable, e.g. `make docs target=html`.)
endif
	  $(MAKE) -C doc $(target)
