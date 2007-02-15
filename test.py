#! /usr/bin/python
# -*- coding: latin-1 -*-
# $Id$
"""
Copyright (C) 2007 by Linpro AS
"""
__revision__ = "$Rev$"
__author__ = "Martin Thorsen Ranang <mtr@ranang.org>"

for value in ['A', 'B', 'c']:
    exec('%s="%s"' % (value, value))

import re

class MiniParser(object):
    __delimiter_pair = {
        '(': ')',
        '{': '}',
        }
    
    __scope_open_re = re.compile('''
    (?<![\\])                           # Do not match escaped tokens.
    [%s]                                # Any of the scope openers. 
    ''' % (''.join(__delimiter_pair), re.VERBOSE)
    
    def parse(self, string):
        # A stack of opened scopes.
        opened_scopes = []
        
        
        

def main():
    """Module mainline (for standalone execution)."""
    strings = ['H2O@H$_{2}$O', 'ABC@($a$, {$b$^$c$})', 'LaTeX@{\LaTeX}']

    

if __name__ == "__main__":
    main()
