PYTHON ?= python3

.PHONY: all
all: style-check type-check test

.PHONY: clean
clean: clean
	# clean Python cache files:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name __pycache__ -exec rm -rf {} +

	# clean backup files:
	find . -name '*~' -exec rm -f {} +
	find . -name '*.bak' -exec rm -f {} +
	find . -name '*.swp' -exec rm -f {} +
	find . -name '*.swo' -exec rm -f {} +

	# clean generated:
	find . -name '.DS_Store' -exec rm -f {} +

	# clean rendered documentation:
	rm -rf doc/build/
	rm -rf doc/_build/
	rm -rf build/sphinx/

	# clean caches:
	find . -name '.mypy_cache' -exec rm -rf {} +
	find . -name '.ruff_cache' -exec rm -rf {} +

	# clean test files:
	rm -rf tests/.coverage
	rm -rf tests/build
	rm -rf .tox/
	rm -rf .cache/
	find . -name '.pytest_cache' -exec rm -rf {} +
	rm -f tests/test-server.lock

	# clean build files:
	rm -rf dist/
	rm -rf build/

.PHONY: style-check
style-check:
	@ruff check .

.PHONY: type-check
type-check:
	@mypy

.PHONY: doclinter
doclinter:
	@sphinx-lint --enable all --max-line-length 85 --disable triple-backticks \
	             -i CHANGES.rst -i LICENSE.rst -i EXAMPLES.rst \
	             $(addprefix -i doc/, _build _static _templates _themes) \
	             *.rst doc/ 2>&1 | sort -V

.PHONY: test
test:
	@$(PYTHON) -X dev -X warn_default_encoding -m pytest -v $(TEST)

.PHONY: covertest
covertest:
	@$(PYTHON) -X dev -X warn_default_encoding -m pytest -v --cov=sphinx --junitxml=.junit.xml $(TEST)

.PHONY: build
build:
	@$(PYTHON) -m build .

.PHONY: docs
docs:
ifndef target
	$(info You need to provide a target variable, e.g. `make docs target=html`.)
endif
	$(MAKE) -C doc $(target)
