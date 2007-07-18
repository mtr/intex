# Copyright (C) 2007 by Martin Thorsen Ranang
#
# $Id: Makefile.am 299 2007-06-20 19:35:26Z mtr $
#
SUBDIRS = src #po lib

ACLOCAL_AMFLAGS = -I m4

EXTRA_DIST = m4/ChangeLog src/*.py #lib/

pysetyp = setup.py

PYTHON = /usr/bin/python2.5

GET_RELEASE = $(top_srcdir)/bin/get_release

RELEASE := $(shell $(GET_RELEASE))

DISTDIR = $(top_srcdir)/dist

release:
	$(top_srcdir)/bin/increase_release

next_release:
	$(top_srcdir)/bin/increase_release

tag_release:
	$(top_srcdir)/bin/tag_release

rpm: all release tag_release $(pysetyp)
	@python $(pysetyp) clean
	@python $(pysetyp) bdist_rpm --python=$(PYTHON) --release=$(RELEASE) --post-install=$(top_srcdir)/src/post-install.sh --post-uninstall=$(top_srcdir)/src/pre-uninstall.sh

deb: rpm
	pushd $(DISTDIR) && fakeroot alien --to-deb --keep-version --scripts $(PACKAGE)-$(VERSION)-$(RELEASE).noarch.rpm && popd

tests:
	PYTHONPATH=$(top_srcdir)/lib pytest test

etags:
	etags --language-force=Python \
		src/* \
		$$(find lib -name \*\.py |tr '\n' ' ')
