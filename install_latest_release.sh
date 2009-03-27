#! /bin/bash
#
# Copyright (C) 2009 by Martin Thorsen Ranang
#

sudo dpkg --purge intex && sudo dpkg --install $(ls -1 dist/*.deb |tail -1)
