#! /usr/bin/python
# -*- coding: latin-1 -*-
# $Id$
"""
Copyright (C) 2007 by Martin Thorsen Ranang
"""
__revision__ = "$Rev$"
__author__ = "Martin Thorsen Ranang <mtr@ranang.org>"


import re

class UnexpectedClosingError(ValueError):
    """Error indicating that an ParenParser detected an unexpected
    closing.
    """ 
    pass

class ParenParser(object):
    ESCAPE_TOKEN = '\\'

    __default_paren_pair = {
        '(': ')',
        '{': '}',
        '[': ']',
        }
    
    def __init__(self, paren_pair=__default_paren_pair):
        self.__paren_pair = paren_pair
        self.__closings = set(self.__paren_pair.values())
        
    def __reset(self):
        self.__consecutive_escapes = 0  # The number of consecutive escapes.
        self.__opened_scopes = []       # A stack of opened scopes.
        self.__expected_closing = None
        
    def __update_expected_closing(self):
        if self.__opened_scopes:
            most_recent_opening = self.__opened_scopes[-1][0]
            self.__expected_closing = self.__paren_pair[most_recent_opening]
        else:
            self.__expected_closing = None
        
    def get_scope_spans(self, string, start_index=0):
        self.__reset()
        
        for i in xrange(start_index, len(string)):
            token = string[i]
            
            if token == self.ESCAPE_TOKEN:
                self.__consecutive_escapes += 1
                continue
            
            # If the current TOKEN is not escaped; that is, the
            # __CONSECUTIVE_ESCAPES is zero or odd (bit-wise "& 1")...
            if not (self.__consecutive_escapes & 1):
                # If the TOKEN is an expected closing...
                if token == self.__expected_closing:
                    # Yield the start and end index for the closing
                    # scope.
                    yield self.__opened_scopes.pop()[1], (i + 1)
                    
                    self.__update_expected_closing()

                # If TOKEN is an unexpected closing...
                elif token in self.__closings:
                    j = self.__opened_scopes[-1][1]
                    reason = "Received unexpected closing '%s' at " \
                             "input position %d.  " \
                             "Input (from position %d):\n%s\n" \
                             "Expected closing was '%s'." \
                             % (token, i, j, string[j:(i + 1)],
                                self.__expected_closing)
                    raise UnexpectedClosingError, reason
                
                # If TOKEN is a legal opening token...
                elif (token in self.__paren_pair):
                    self.__opened_scopes.append((token, i))
                    self.__update_expected_closing()
                    
            # Reset the escape-token counter.
            self.__consecutive_escapes = 0

def main():
    """Module mainline (for standalone execution).
    """
    pass
        
if __name__ == "__main__":
    main()
