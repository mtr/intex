#! /usr/bin/python
# -*- coding: latin-1 -*-
# $Id$
"""
Copyright (C) 2007 by Martin Thorsen Ranang
"""
__revision__ = "$Rev$"
__author__ = "Martin Thorsen Ranang <mtr@ranang.org>"

import parenparser
import unittest

def cartesian(*sequences):
    """Returns the cartesian product of the SEQUENCES.

    Written by Guido van Rossum.
    """
    if len(sequences) == 0:
        yield []
    else:
        head, tail = sequences[:-1], sequences[-1]
        tail = list(tail)          # <--- This is what I was proposing
        for x in cartesian(*head):
            for y in tail:
                yield x + [y]

class SimpleParenParserTestCase(unittest.TestCase):
    matching_pairs = [
        ('(', ')'),
        ('[', ']'),
        ('{', '}'),
        ]

    closing = dict(matching_pairs)
    opening = dict((right, left) for (left, right) in matching_pairs)
    
    def setUp(self):
        self.parser = parenparser.ParenParser()

    def get_all_indices(self, string):
        return list(self.parser.get_scope_spans(string))
        
class NonMatchingClosingTestCase(SimpleParenParserTestCase):
    def runTest(self):
        # Test all simple combinations of non-matching closing
        # parenthesis.  For example: '(}' and '(})'
        for left, right in self.matching_pairs:
            for ignore, token in self.matching_pairs:
                if token == right:
                    continue
                
                failing = '%(left)s%(token)s' % locals()
                self.assertRaises(parenparser.UnexpectedClosingError,
                                  self.get_all_indices, failing)

                failing += right
                self.assertRaises(parenparser.UnexpectedClosingError,
                                  self.get_all_indices, failing)

class NestedScopesTestCase(SimpleParenParserTestCase):
    def runTest(self):
        lefts = [left for left, right in self.matching_pairs]
        levels = len(lefts)
        
        for combo in cartesian(lefts, lefts, lefts):
            indices = []
            for i, opening in enumerate(reversed(combo)):
                combo.append(self.closing[opening])
                indices.append(((levels - (i + 1)), (levels + (i + 1))))
                
            self.assertEqual(indices,
                             list(self.get_all_indices(''.join(combo))))
            
class ParenParserTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self, [
            NonMatchingClosingTestCase(),
            NestedScopesTestCase(),
            ])
        
def main():
    """Module mainline (for standalone execution).
    """
    suite = ParenParserTestSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":
    main()
