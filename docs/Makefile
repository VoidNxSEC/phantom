# Makefile for Sphinx documentation

.PHONY: help clean html live-html pdf

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

help:
	@echo "Sphinx documentation build targets:"
	@echo "  make html       - Build HTML documentation"
	@echo "  make live-html  - Build with live-reload"
	@echo "  make clean      - Remove build directory"
	@echo "  make pdf        - Build PDF documentation"
	@echo "  make serve      - Serve documentation on port 8001"

clean:
	rm -rf $(BUILDDIR)

html:
	$(SPHINXBUILD) -b html $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html"

live-html:
	sphinx-autobuild -b html $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html

pdf:
	$(SPHINXBUILD) -b latexpdf $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/pdf
	@echo "Build finished. The PDF is in $(BUILDDIR)/pdf"

serve: html
	python -m http.server 8001 -d _build/html

install-deps:
	pip install -r requirements-docs.txt

check:
	sphinx-build -W -b html $(SOURCEDIR) $(BUILDDIR)/html

.PHONY: all
all: clean html pdf

.PHONY: preview
preview: clean html serve
