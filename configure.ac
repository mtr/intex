dnl Process this file with autoconf to produce a configure script.
dnl 
dnl $Id$
dnl
AC_INIT(intex, 1.4.1)
AC_CONFIG_SRCDIR(src/mkintex.py)
AM_INIT_AUTOMAKE

dnl AM_GNU_GETTEXT([external])

AM_PATH_PYTHON(2.5,, :)

AC_OUTPUT([Makefile
	   setup.cfg
           setup.py
	   bin/config.sh
	   doc/Makefile
	   doc/mkintex.xml
	   latex/Makefile
	   lib/intex/config.py
	   src/Makefile
	   src/post-install.sh
	   src/post-uninstall.sh],
          [])
