#! /usr/bin/python
# -*- coding: latin-1 -*-
# $Id$
"""
Copyright (C) 2007 by Martin Thorsen Ranang
"""
__revision__ = "$Rev$"
__author__ = "Martin Thorsen Ranang <mtr@ranang.org>"


import re

class ParenParser(object):
    ESCAPE_TOKEN = '\\'

    __default_paren_pair = {
        '(': ')',
        '{': '}',
        }
    
    def __init__(self, paren_pair=__default_paren_pair):
        self.__paren_pair = paren_pair
        
    def __setup(self):
        self.__consecutive_escapes = 0  # The number of consecutive escapes.
        self.__opened_scopes = []       # A stack of opened scopes.
        self.__expected_closing = None
        
    def __update_expected_closing(self):
        if self.__opened_scopes:
            most_recent_opening = self.__opened_scopes[-1][0]
            self.__expected_closing = self.__paren_pair[most_recent_opening]
        else:
            self.__expected_closing = None
        
    def get_scope_spans(self, string):
        self.__setup()
        
        for i in xrange(len(string)):
            token = string[i]
            
            if token == self.ESCAPE_TOKEN:
                self.__consecutive_escapes += 1
                continue
            
            # If the CONSECUTIVE_ESCAPES is zero or odd...
            if not (self.__consecutive_escapes & 1):
                if token == self.__expected_closing:
                    # Yield the start and end index for the closing scope.
                    yield self.__opened_scopes.pop()[1], (i + 1)
                    
                    self.__update_expected_closing()
                    
                elif (token in self.__paren_pair):
                    self.__opened_scopes.append((token, i))
                    self.__update_expected_closing()
                    
            # Reset the escape-token counter.
            self.__consecutive_escapes = 0

def main():
    """Module mainline (for standalone execution)."""
    strings = ['H2O@H$_{2}$O', 'ABC@($a$, {$b$^$c$})', 'LaTeX@{\LaTeX}']

    p = ParenParser()
    
    for string in strings:
        for i, j in p.get_scope_spans(string):
            print string[i:j]
        
if __name__ == "__main__":
    main()
