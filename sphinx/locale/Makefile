IGNORED = ta
LOCALES = $(filter-out $(IGNORED),$(patsubst %/LC_MESSAGES,%,$(wildcard */LC_MESSAGES)))
POFILES = $(LOCALES:%=%/LC_MESSAGES/sphinx.po)
CHECK   = $(POFILES:.po=.check)

.PHONY: all
check: $(CHECK)

.PHONY: $(CHECK)
$(CHECK): %.check: %.po
	msgfmt --check -o /dev/null $<
