# Copyright (C) 2007 by Martin Thorsen Ranang
#
# $Id: Makefile.am 1026 2007-07-18 12:49:41Z mtr $
#

dist_man_MANS = mkintex.1

mkintex.1:
	docbook2x-man mkintex.xml

mkintex.1.gz: mkintex.1
	gzip --force mkintex.1

all: mkintex.1.gz

clean:
	rm -rf mkintex.1 mkintex.1.gz *~
