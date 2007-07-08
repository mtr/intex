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


class SimpleParenParserTestCase(unittest.TestCase):
    matching_pairs = [
        ('(', ')'),
        ('[', ']'),
        ('{', '}'),
        ]

    closing = dict(matching_pairs)
    
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
        
        for combo in parenparser.cartesian(lefts, lefts, lefts):
            indices = []
            for i, opening in enumerate(reversed(combo)):
                combo.append(self.closing[opening])
                indices.append(((levels - (i + 1)), (levels + (i + 1))))
                
            self.assertEqual(indices,
                             list(self.get_all_indices(''.join(combo))))

class LaTeXTestCase(SimpleParenParserTestCase):
    def runTest(self):
        # Find all the scopes in each string, innermost scopes first.
        for string, scopes in [
            ('H2O@H$_{2}$O', ['{2}']),
            ('ABC@($a$, {$b$^$c$})', ['{$b$^$c$}', '($a$, {$b$^$c$})']),
            ('LaTeX@{\LaTeX}', ['{\LaTeX}']),
            ]:
            for k, (i, j) in enumerate(self.get_all_indices(string)):
                self.assertEqual(scopes[k], string[i:j])

class WhitespaceSplitTestCase(SimpleParenParserTestCase):
    def runTest(self):
        # Find all the scopes in each string, innermost scopes first.
        for separator, string, parts in [
            # Default whitespace-based splitting.
            (None, '', []),
            (None, 'abc def ghi', ['abc', 'def', 'ghi']),
            (None, '()', ['()']),
            (None, '(abc)', ['(abc)']),
            (None, '(abc) def', ['(abc)', 'def']),
            (None, 'abc(def)ghi (jkl) mno(pqr) stu',
             ['abc(def)ghi', '(jkl)', 'mno(pqr)', 'stu']),
            (None, '(abc(def)ghi (jkl) mno(pqr) stu)',
             ['(abc(def)ghi (jkl) mno(pqr) stu)']),
            (None, '()abc(def)ghi (jkl) mno(pqr) stu',
             ['()abc(def)ghi', '(jkl)', 'mno(pqr)', 'stu']),
            (None, 'abc(def)ghi (jkl) mno(pqr) stu()',
             ['abc(def)ghi', '(jkl)', 'mno(pqr)', 'stu()']),
            (None, 'abc(def)ghi (jkl) mno(pqr) stu (vwx) ()',
             ['abc(def)ghi', '(jkl)', 'mno(pqr)', 'stu', '(vwx)', '()']),
            ]:
            self.assertEqual(self.parser.split(string, separator), parts)

class TokenSplitTestCase(SimpleParenParserTestCase):
    def runTest(self):
        for separator, string, parts in [
            # '@'-based splitting.
            ('@', '', ['']),
            ('@', 'abc@def@ghi', ['abc', 'def', 'ghi']),
            ('@', '()', ['()']),
            ('@', '(abc)', ['(abc)']),
            ('@', '(abc)@def', ['(abc)', 'def']),
            ('@', 'abc(def)ghi@(jkl)@mno(pqr)@stu',
             ['abc(def)ghi', '(jkl)', 'mno(pqr)', 'stu']),
            ('@', '(abc(def)ghi@(jkl)@mno(pqr)@stu)',
             ['(abc(def)ghi@(jkl)@mno(pqr)@stu)']),
            ('@', '()abc(def)ghi@(jkl)@mno(pqr)@stu',
             ['()abc(def)ghi', '(jkl)', 'mno(pqr)', 'stu']),
            ('@', 'abc(def)ghi@(jkl)@mno(pqr)@stu()',
             ['abc(def)ghi', '(jkl)', 'mno(pqr)', 'stu()']),
            ('@', 'abc(def)ghi@(jkl)@mno(pqr)@stu@(vwx)@()',
             ['abc(def)ghi', '(jkl)', 'mno(pqr)', 'stu', '(vwx)', '()']),
            ]:
            self.assertEqual(self.parser.split(string, separator), parts)
                
class ParenParserTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self, [
            NonMatchingClosingTestCase(),
            NestedScopesTestCase(),
            LaTeXTestCase(),
            WhitespaceSplitTestCase(),
            TokenSplitTestCase(),
            ])
        
def main():
    """Module mainline (for standalone execution).
    """
    suite = ParenParserTestSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":
    main()
