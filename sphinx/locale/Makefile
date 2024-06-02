# Ignore locales that are known failures. See utils/babel_runner.py
IGNORED = ta
POFILES = $(wildcard */LC_MESSAGES/sphinx.po)
CHECK   = $(POFILES:.po=.check)

.PHONY: all
check: $(filter-out $(IGNORED:=/LC_MESSAGES/sphinx.check),$(CHECK))

.PHONY: $(CHECK)
$(CHECK): %.check: %.po
	msgfmt --check -o /dev/null $<
