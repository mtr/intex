
bin_SCRIPTS = model_builder model_server query_handler
CLEANFILES = $(bin_SCRIPTS)

do_subst = sed -e 's,[@]datadir[@],$(datadir),g' \
               -e 's,[@]PYTHON[@],$(PYTHON),g' \
               -e 's,[@]PACKAGE[@],$(PACKAGE),g' \
               -e 's,[@]VERSION[@],$(VERSION),g'

model_builder: model_builder.py Makefile
	$(do_subst) <$< >$@
	chmod +x $@

model_server: model_server.py Makefile
	$(do_subst) <$< >$@
	chmod +x $@

query_handler: query_handler.py Makefile
	$(do_subst) <$< >$@
	chmod +x $@
