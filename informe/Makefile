MAIN = informe
LATEX = pdflatex
BIBTEX = bibtex

.PHONY: all clean

all:
	$(LATEX) $(MAIN).tex
	$(LATEX) $(MAIN).tex
	@echo "PDF generado: $(MAIN).pdf"

clean:
	rm -f *.aux *.log *.bbl *.blg *.out *.toc *.synctex.gz
