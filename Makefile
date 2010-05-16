PYTHON ?= python3

export PYTHONPATH = $(shell echo "$$PYTHONPATH"):./sphinx

.PHONY: all check clean clean-pyc clean-patchfiles clean-generated pylint \
        reindent test

DONT_CHECK = -i build -i dist -i sphinx/style/jquery.js \
             -i sphinx/pycode/pgen2 -i sphinx/util/smartypants.py \
             -i .ropeproject -i doc/_build -i tests/path.py \
             -i tests/coverage.py -i env -i utils/convert.py \
             -i utils/reindent3.py -i utils/check_sources3.py -i .tox

all: clean-pyc check test

check: convert-utils
ifeq ($(PYTHON), python3)
	@$(PYTHON) utils/check_sources3.py $(DONT_CHECK) .
else
	@$(PYTHON) utils/check_sources.py $(DONT_CHECK) .
endif

clean: clean-pyc clean-patchfiles clean-backupfiles clean-generated

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +

clean-patchfiles:
	find . -name '*.orig' -exec rm -f {} +
	find . -name '*.rej' -exec rm -f {} +

clean-backupfiles:
	find . -name '*~' -exec rm -f {} +
	find . -name '*.bak' -exec rm -f {} +

clean-generated:
	rm -f utils/*3.py*

pylint:
	@pylint --rcfile utils/pylintrc sphinx

reindent: convert-utils
ifeq ($(PYTHON), python3)
	@$(PYTHON) utils/reindent3.py -r -B .
else
	@$(PYTHON) utils/reindent.py -r -B .
endif

test: build
	@cd tests; $(PYTHON) run.py -d -m '^[tT]est' $(TEST)

covertest: build
	@cd tests; $(PYTHON) run.py -d -m '^[tT]est' --with-coverage \
		--cover-package=sphinx $(TEST)

build:
	@$(PYTHON) setup.py build

convert-utils:
	@python3 utils/convert.py -i utils/convert.py utils/
