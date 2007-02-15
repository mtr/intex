#! /usr/bin/python
# -*- coding: latin-1 -*-
# $Id$
"""
Copyright (C) 2007 by Linpro AS
"""
__revision__ = "$Rev$"
__author__ = "Martin Thorsen Ranang <mtr@linpro.no>"

for value in ['A', 'B', 'c']:
    exec('%s="%s"' % (value, value))

import re

class MiniParser(object):
    __scope_open_re = re.compile()
    def parse(self, string):
        # A stack of opened scopes.
        opened_scopes = []

        
        

def main():
    """Module mainline (for standalone execution)."""
    strings = ['H2O@H$_{2}$O', 'ABC@($a$, {$b$^$c$})', 'LaTeX@{\LaTeX}']

    

if __name__ == "__main__":
    main()
