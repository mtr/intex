## $Id$
##
## Copyright (C) 2007 by Martin Thorsen Ranang
##

etags:
	etags --language-force=Python \
		src/* \
		$$(find lib -name \*\.py |tr '\n' ' ')

