dnl Process this file with autoconf to produce a configure script.
dnl 
dnl $Id: configure.ac 314 2007-06-22 14:46:42Z mtr $
dnl
AC_INIT(intex, 1.0)
AC_CONFIG_SRCDIR(src/mkintex)
AM_INIT_AUTOMAKE

AM_GNU_GETTEXT([external])

AM_PATH_PYTHON(2.5,, :)

AC_OUTPUT([Makefile
           setup.py
	   bin/config.sh
	   lib/intex/config.py
	   src/Makefile
	   src/post-install.sh
	   src/post-uninstall.sh],
          [])
