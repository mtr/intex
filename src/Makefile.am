
bin_SCRIPTS = mkintex
CLEANFILES = $(bin_SCRIPTS)

do_subst = sed -e 's,[@]datadir[@],$(datadir),g' \
               -e 's,[@]PYTHON[@],$(PYTHON),g' \
               -e 's,[@]PACKAGE[@],$(PACKAGE),g' \
               -e 's,[@]VERSION[@],$(VERSION),g'

mkintex: mkintex.py Makefile
	$(do_subst) <$< >$@
	chmod +x $@
