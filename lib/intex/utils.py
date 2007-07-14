#! /usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
"""
Copyright (C) 2007 by Linpro AS
"""
__author__ = "Martin Thorsen Ranang <mtr@linpro.no>"
__revision__ = "$Rev$"
__version__ = "@VERSION@"

from itertools import chain

def flatten(sequence):
    """Returns a flattened list.
    """
    return list(chain(*sequence))

def main():
    """Module mainline (for standalone execution).
    """
    pass

if __name__ == "__main__":
    main()
