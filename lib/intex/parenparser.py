#! /usr/bin/python
# -*- coding: latin-1 -*-
# $Id$
"""
Copyright (C) 2007 by Martin Thorsen Ranang
"""
__revision__ = "$Rev$"
__author__ = "Martin Thorsen Ranang <mtr@ranang.org>"

import re

#from stack import Stack
    
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

    @staticmethod
    def filter_outer_scopes(scopes):
        """Removes scopes that appear inside other scopes.  Hence, only
        the outermost scopes will be returned.
        
        Example:
        >>> parenparser.remove_inner_scopes([(2, 5), (3, 4), (6, 12),
        ...                                  (7, 11), (8, 10)])
        [(2, 5), (6, 12)]
        """
        scopes = sorted(scopes)
        keep = []
        
        for n, (i, j) in enumerate(scopes):
            if n == 0:
                pass                    # Must define an outer scope.
            elif j < keep[-1][-1]:
                continue
            
            keep.append((i, j))
            
        return keep
    
    def split(self, string, separator=None, maxsplit=None):
        """Return a list of the words in the string STRING, using
        SEPARATOR as the delimiter string, but scopes defined by
        parenthetical tokens are not split.  If MAXSPLIT is given, at
        most MAXSPLIT splits are done.  If SEPARATOR is not specified
        or is None, any whitespace string is a separator.

        Please note: The MAXSPLIT argument is not honored yet.
        """
        # Make sure only outermost scopes are considered.
        indices = self.filter_outer_scopes(self.get_scope_spans(string))

        # If no parenthetical scopes were detected, there are no
        # scopes to honor.
        if not indices:
            return string.split(separator)
        
        # The following is added to avoid any special-case handling
        # after the for-loop below.
        if indices[-1][1] < len(string):
            indices.append((-1, None))
        
        k = None
        result = []
        
        for i, j in indices:
            parts = string[k:i].split(separator) + [string[i:j]]
            
            first_part = parts[0]
            if result and (k is not None) and (first_part[0] == string[k]):
                result[-1] += first_part
            else:
                result.append(first_part)
                
            if len(parts) > 1:
                result.extend(parts[1:-1])
                
                last_part = parts[-1]
                if result[-1][-1] == string[i - 1]:
                    result[-1] += last_part
                else:
                    result.append(last_part)
                
            k = j

        return result
    
def main():
    """Module mainline (for standalone execution).
    """
    p = ParenParser()
    
    for string in [
        '',
        'a b c',
        '()',
        '(abc)',
        '(abc) def',
        'abc(def)ghi (jkl) mno(pqr) stu',
        '(abc(def)ghi (jkl) mno(pqr) stu)',
        '()abc(def)ghi (jkl) mno(pqr) stu',
        'abc(def)ghi (jkl) mno(pqr) stu()',
        'abc(def)ghi (jkl) mno(pqr) stu (vwx) ()',
        ]:
        print '("%s",\n %s),' % (string, p.split(string))
        
if __name__ == "__main__":
    main()
