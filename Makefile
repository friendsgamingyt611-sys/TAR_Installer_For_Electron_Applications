# Standard Makefile for TIFEA (TAR Installer For Electron Applications)

PREFIX ?= /usr/local
DESTDIR ?=
BINDIR ?= $(PREFIX)/bin
DATADIR ?= $(PREFIX)/share
MANDIR ?= $(DATADIR)/man
PYTHON ?= python3

.PHONY: all build install uninstall test clean rpm flatpak

all: build

build:
	@echo "Building TIFEA..."
	$(PYTHON) -m pip install --no-build-isolation --no-deps --editable . || $(PYTHON) setup.py build 2>/dev/null || true

test:
	@echo "Running unit test suite..."
	PYTHONPATH=. $(PYTHON) -m unittest discover -s tests

install:
	@echo "Installing TIFEA to $(DESTDIR)$(PREFIX)..."
	install -d $(DESTDIR)$(BINDIR)
	install -m 0755 bin/tifea $(DESTDIR)$(BINDIR)/tifea
	ln -sf tifea $(DESTDIR)$(BINDIR)/tifiea
	ln -sf tifea $(DESTDIR)$(BINDIR)/targz-installer
	
	# Man page
	install -d $(DESTDIR)$(MANDIR)/man1
	install -m 0644 data/man/tifea.1 $(DESTDIR)$(MANDIR)/man1/tifea.1
	
	# Shell completions
	install -d $(DESTDIR)$(DATADIR)/bash-completion/completions
	install -m 0644 data/completions/tifea.bash $(DESTDIR)$(DATADIR)/bash-completion/completions/tifea
	
	install -d $(DESTDIR)$(DATADIR)/zsh/site-functions
	install -m 0644 data/completions/tifea.zsh $(DESTDIR)$(DATADIR)/zsh/site-functions/_tifea
	
	install -d $(DESTDIR)$(DATADIR)/fish/vendor_completions.d
	install -m 0644 data/completions/tifea.fish $(DESTDIR)$(DATADIR)/fish/vendor_completions.d/tifea.fish
	
	# AppStream Metadata
	install -d $(DESTDIR)$(DATADIR)/metainfo
	install -m 0644 data/metainfo/org.example.tifea.metainfo.xml $(DESTDIR)$(DATADIR)/metainfo/org.example.tifea.metainfo.xml
	
	# Python package install
	$(PYTHON) -m pip install --no-deps --root $(DESTDIR) . 2>/dev/null || true

uninstall:
	@echo "Uninstalling TIFEA..."
	rm -f $(DESTDIR)$(BINDIR)/tifea
	rm -f $(DESTDIR)$(BINDIR)/tifiea
	rm -f $(DESTDIR)$(BINDIR)/targz-installer
	rm -f $(DESTDIR)$(MANDIR)/man1/tifea.1
	rm -f $(DESTDIR)$(DATADIR)/bash-completion/completions/tifea
	rm -f $(DESTDIR)$(DATADIR)/zsh/site-functions/_tifea
	rm -f $(DESTDIR)$(DATADIR)/fish/vendor_completions.d/tifea.fish
	rm -f $(DESTDIR)$(DATADIR)/metainfo/org.example.tifea.metainfo.xml

rpm:
	@echo "Building RPM package..."
	rpmbuild -ba tifea.spec

flatpak:
	@echo "Building Flatpak package..."
	flatpak-builder --force-clean build-dir org.example.tifea.json

clean:
	rm -rf build dist *.egg-info .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
