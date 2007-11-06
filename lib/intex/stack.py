#! /usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
"""
Copyright (C) 2007 by Martin Thorsen Ranang
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
