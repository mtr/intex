#! /usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
"""
Copyright (C) 2007, 2008 by Martin Thorsen Ranang

This file is part of InTeX.

InTeX is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your
option) any later version.

InTeX is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License
along with InTeX.  If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = "Martin Thorsen Ranang <mtr@ranang.org>"
__revision__ = "$Rev$"
__version__ = "@VERSION@"

class Stack(list):
    def push(self, element):
        """Push an element to the stack.
        """
        list.append(self, element)

def main():
    """Module mainline (for standalone execution)."""
    pass


if __name__ == "__main__":
    main()
