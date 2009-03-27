#! /bin/bash
#
# Copyright (C) 2009 by Martin Thorsen Ranang
#

make next_release
make tag_release
svn update
svn2cl
make deb_sign
