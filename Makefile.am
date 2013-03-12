# Copyright (C) 2007 by Martin Thorsen Ranang
#
# $Id$
#
SUBDIRS =  src latex doc 

ACLOCAL_AMFLAGS = -I m4

EXTRA_DIST = config.rpath m4/ChangeLog  m4/ChangeLog src/*.py #lib/

pysetyp = setup.py

PYTHON = /usr/bin/python2.7

GET_RELEASE = $(top_srcdir)/bin/get_release

RELEASE := $(shell $(GET_RELEASE))

DISTDIR = $(top_srcdir)/dist

release:
	$(top_srcdir)/bin/get_release

next_release:
	$(top_srcdir)/bin/increase_release

tag_release:
	$(top_srcdir)/bin/tag_release

rpm_sign:
	rpmsign --addsign $(DISTDIR)/$(PACKAGE)-$(VERSION)-$(RELEASE).*.rpm

# rpm: all release tag_release $(pysetyp)
rpm: all release $(pysetyp)
	@python $(pysetyp) clean
	@python $(pysetyp) bdist_rpm --python=$(PYTHON) --release=$(RELEASE) --post-install=$(top_srcdir)/src/post-install.sh --post-uninstall=$(top_srcdir)/src/post-uninstall.sh

deb_sign: deb
	pushd $(DISTDIR) && dpkg-sig --sign builder $(PACKAGE)_$(VERSION)-$(RELEASE)_all.deb && popd

deb: rpm
	pushd $(DISTDIR) && fakeroot alien --to-deb --keep-version --scripts $(PACKAGE)-$(VERSION)-$(RELEASE).noarch.rpm && popd

tests:
	PYTHONPATH=$(top_srcdir)/lib pytest test

#etags --language-force=Python
etags:
	etags --language=python \
		src/* \
		$$(find lib -name \*\.py |tr '\n' ' ')
