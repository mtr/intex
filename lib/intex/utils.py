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

from itertools import chain
from string import whitespace

ESCAPE_TOKEN = '\\'

def flatten(sequence):
    """Returns a flattened list.
    """
    return list(chain(*sequence))

def _init_escape_aware_split(delimiter):
    if delimiter is None:
        delimiter = whitespace
        lookahead = 1
    else:
        lookahead = len(delimiter)

    return delimiter, lookahead, list(), (None, None)

def escape_aware_split(string, delimiter=None, maxsplit=None):
    delimiter, lookahead, parts, (i, j) = _init_escape_aware_split(delimiter)
    
    for k in xrange((len(string) - (lookahead - 1))):
        token = string[k:(k + lookahead)]

        if (token == delimiter) or (token in delimiter):
            # Found a delimiter.  Check the number of contiguous
            # escape tokens in front of it (right to left).
            for l in xrange((k - 1), -1, -1):
                if string[l] != ESCAPE_TOKEN:
                    break
            
            escapes = (k - l - 1)
            
            if not (escapes & 1):   # Odd number of escapes?
                # Split here.
                parts.append(string[i:k])
                
                i = (k + lookahead) # Skip the delimiter token.
                
        if len(parts) == maxsplit:
            break
                
    parts.append(string[i:j])
    
    return parts

def escape_aware_rsplit(string, delimiter=None, maxsplit=None):
    delimiter, lookahead, parts, (i, j) = _init_escape_aware_split(delimiter)
    
    for k in xrange((len(string) - lookahead), -1, -1):
        token = string[k:(k + lookahead)]

        if (token == delimiter) or (token in delimiter):
            # Found a delimiter.  Check the number of contiguous
            # escape tokens in front of it (right to left).
            for l in xrange((k - 1), -1, -1):
                if string[l] != ESCAPE_TOKEN:
                    break
                
            escapes = (k - l - 1)
            
            if not (escapes & 1):   # Odd number of escapes?
                # Split here.
                parts.append(string[k + lookahead:j])
                
                j = k                   # Skip the delimiter token.
                
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
