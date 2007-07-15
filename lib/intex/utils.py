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
from string import whitespace

ESCAPE_TOKEN = '\\'

def flatten(sequence):
    """Returns a flattened list.
    """
    return list(chain(*sequence))

def escape_aware_split(string, delimiter=whitespace, maxsplit=None):
    parts = list()

    i, j = None, None
    
    for k, token in enumerate(string):
        if token in delimiter:
            # Found a delimiter.  Check the number of contiguous
            # escape tokens in front of it (right to left).
            for l in xrange((k - 1), -1, -1):
                if string[l] != ESCAPE_TOKEN:
                    break
                
            escapes = (k - l - 1)
            
            if not (escapes & 1):   # Odd number of escapes?
                # Split here.
                parts.append(string[i:k])
                
                i = (k + 1)         # Skip the delimiter token.

        if len(parts) == maxsplit:
            break
                
    parts.append(string[i:j])
    
    return parts

def escape_aware_rsplit(string, delimiter=whitespace, maxsplit=None):
    parts = list()
    
    i, j = None, None
    
    for k, token in reversed(list(enumerate(string))):
        if token in delimiter:
            # Found a delimiter.  Check the number of contiguous
            # escape tokens in front of it (right to left).
            for l in xrange((k - 1), -1, -1):
                if string[l] != ESCAPE_TOKEN:
                    break
                
            escapes = (k - l - 1)
            
            if not (escapes & 1):   # Odd number of escapes?
                # Split here.
                parts.append(string[k+ 1:j])
                
                j = k         # Skip the delimiter token.

        if len(parts) == maxsplit:
            break
                
    parts.append(string[i:j])           # Add the rest, if applicable.
    parts.reverse()                     # Reverse the list in-place.
    
    return parts

def main():
    """Module mainline (for standalone execution).
    """
    pass

if __name__ == "__main__":
    main()
