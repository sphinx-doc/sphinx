# Makefile for Sphinx LaTeX output

ALLDOCS = $(basename $(wildcard *.tex))
ALLPDF = $(addsuffix .pdf,$(ALLDOCS))
ALLDVI = $(addsuffix .dvi,$(ALLDOCS))

# Prefix for archive names
ARCHIVEPRREFIX =

all: $(ALLPDF)
all-pdf: $(ALLPDF)
all-dvi: $(ALLDVI)
all-ps: all-dvi
	for f in *.dvi; do dvips $f; done

zip: all-$(FMT)
	mkdir $(ARCHIVEPREFIX)docs-$(FMT)
	cp $(ALLPDF) $(ARCHIVEPREFIX)docs-$(FMT)
	zip -q -r -9 $(ARCHIVEPREFIX)docs-$(FMT).zip $(ARCHIVEPREFIX)docs-$(FMT)
	rm -r $(ARCHIVEPREFIX)docs-$(FMT)

tar: all-$(FMT)
	mkdir $(ARCHIVEPREFIX)docs-$(FMT)
	cp $(ALLPDF) $(ARCHIVEPREFIX)docs-$(FMT)
	tar cf $(ARCHIVEPREFIX)docs-$(FMT).tar
	rm -r $(ARCHIVEPREFIX)docs-$(FMT)

bz2: tar-$(FMT)
	bzip2 -9 -k $(ARCHIVEPREFIX)docs-$(FMT).tar

%.dvi: %.tex
	latex $<
	latex $<
	latex $<
	-makeindex -s python.ist $(basename $<).idx
	-makeindex -s python.ist $(basename mod$<).idx
	latex $<
	latex $<

%.pdf: %.tex
	pdflatex $<
	pdflatex $<
	pdflatex $<
	-makeindex -s python.ist $(basename $<).idx
	-makeindex -s python.ist $(basename mod$<).idx
	pdflatex $<
	pdflatex $<

.PHONY: all all-pdf all-dvi all-ps

