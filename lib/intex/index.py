#! /usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
"""
Copyright (C) 2007 by Linpro AS
"""
__author__ = "Martin Thorsen Ranang <mtr@linpro.no>"
__revision__ = "$Rev$"
__version__ = "@VERSION@"

import logging
import re

from config import FIELD_SEPARATORS, TOKEN_COMMENT, TOKEN_ENTRY_META_INFO
from index_entry import AcronymEntry, ConceptEntry, PersonEntry
from stack import Stack

class Index(list):
    _concept_types = ['ACRONYMS', 'PEOPLE', 'CONCEPTS']
    _index_attrbiutes = {
        'name': None,
        }

    _re_macros = {
        'FIELD': '''
        [^%(COMMENT_TOKEN)s:\s]         # Non-comment and non-meta.
        (                               # Either
                                        #  escaped field separators
         \\\\[%(FIELD_SEPARATORS)s%(META_TOKEN)s] 
        |                               # or
                                        #  non-field-separators
         [^%(FIELD_SEPARATORS)s%(META_TOKEN)s] 
        )+                              # repeated.
        ''',
        'FIELD_SEPARATORS': FIELD_SEPARATORS,
        'COMMENT_TOKEN': TOKEN_COMMENT,
        'META_TOKEN': TOKEN_ENTRY_META_INFO,
        }
    # Instantiate/format the FIELD macro value by supplying the other
    # (i.e., FIELD_SEPARATORS, COMMENT_TOKEN, and META_TOKEN) mappings
    # in _RE_MACROS.
    _re_macros['FIELD'] = _re_macros['FIELD'] % _re_macros
    
    # Regular expressions, one pattern matcher for each context:
    _concept_re = re.compile('''
    ^                                   # Starts with
    (?P<indent>\s+)?                    # (possible) indentation,
    (?P<concept>%(FIELD)s)?             # an entry,
    [%(FIELD_SEPARATORS)s]*             # a separator,
    (?P<typeset_as>%(FIELD)s)?          # the full form,
    [%(FIELD_SEPARATORS)s]*             # another separator,
    (?P<meta>%(META_TOKEN)s.+)?         # meta information
    $                                   # at the end.
    ''' % _re_macros, re.VERBOSE)

    _acronym_re = re.compile('''
    ^                                     # Starts with
    (?P<indent>\s+)?                      # (possible) indentation,
    (?P<acronym>%(FIELD)s)?               # an entry,
    [%(FIELD_SEPARATORS)s]*               # a separator,
    (?P<full_form>%(FIELD)s)?             # the full form,
    [%(FIELD_SEPARATORS)s]*               # another separator,
    (?P<typeset_as>%(FIELD)s)?            # the full form,
    [%(FIELD_SEPARATORS)s]*               # another separator,
    (?P<meta>%(META_TOKEN)s.+)?           # meta information
    $                                     # at the end.
    ''' % _re_macros, re.VERBOSE)

    _person_re = re.compile('''
    ^                                      # Starts with
    (?P<indent>\s+)?                       # (possible) indentation,
    (?P<initials>%(FIELD)s)?               # an entry,
    [%(FIELD_SEPARATORS)s]*                # a separator,
    (?P<last_name>%(FIELD)s)?              # the full form,
    [%(FIELD_SEPARATORS)s]*                # another separator,
    (?P<first_name>%(FIELD)s)?             # the full form,
    [%(FIELD_SEPARATORS)s]*                # another separator,
    (?P<meta>%(META_TOKEN)s.+)?            # meta information
    $                                      # at the end.
    ''' % _re_macros, re.VERBOSE)

    # A map between context names and the match patterns:
    _context_matcher = {
        'ACRONYMS': _acronym_re,
        'CONCEPTS': _concept_re,
        'PEOPLE': _person_re,
        }

    _context_class = {
        'ACRONYMS': AcronymEntry,
        'CONCEPTS': ConceptEntry,
        'PEOPLE': PersonEntry,
        }
        
    # Add a macro definition to the values available when constructing
    # the regular expressions below.
    _re_macros['CONCEPT_TYPES'] = '|'.join(_context_matcher.keys())

    # A pattern to match meta directives:
    _meta_directive_re = re.compile('''
    ^                                   # Starts with
    %(COMMENT_TOKEN)s                   # the comment token,
    \s*                                 # possibly some whitespace,
    (                                   # then either
     (?P<attribute>\w+)\s*              #  an attribute
     =                                  #  sat to
     \s*(?P<value>\w+)                  #  some value,
     |                                  # or
     (?P<context>\*(%(CONCEPT_TYPES)s)\*) #  a context switch
    )                                   # followed by
    \s*                                 # possibly trailing whitespace
    $                                   # at the end.
    ''' % _re_macros, re.VERBOSE)

    # A pattern to match comment-only lines.
    _pure_comment_re = re.compile('''
    ^                                   # Starts with
    \s*                                 # possibly some whitespace
    %(COMMENT_TOKEN)s                   # and the comment token,
    .*                                  # followed by anything.
    ''' % _re_macros, re.VERBOSE)

    # A list used to instantiate the context dependent parser.
    _matchers = [
        _meta_directive_re,             # For matching meta directives.
        _pure_comment_re,               # For matching pure comments.
        None,               # The current context will be placed here.
        ]
    
    def __init__(self, filename=None, index_name='default'):
        """The constructor.
        """
        list.__init__(self)             # Initialize the base class.
        
        self._name = index_name # FIXME:  The index's name for use in/by ...
        self._current_matchers = list(Index._matchers)
        
        self._indentation_level = {
            '': 0,
            }
        
        self._elements = Stack()  # A stack of elements used when parsing.
        #self.__entries = []  # A list of all the entries in the index.
        
    # Accessors for the 'name' property (_-prefixed to force access
    # through the property):
    def _get_name(self):
        return self._name
        
    def _set_name(self, name):
        self._name = name
        
    name = property(_get_name, _set_name, None, 'The name of the index.')

    def handle_meta_directive(self, attribute=None, value=None, context=None):
        if attribute:
            # Set an attribute describing this index (e.g., its name).
            setattr(self, attribute, value)
        elif context:
            self._context = context[1:-1] # Remove pre and post '*'s.
            logging.info('Switching context to: "%s"', self._context, )
            self._matchers[-1] = self._context_matcher[self._context]
            self._entry_class = self._context_class[self._context]
            
    def handle_comment(self):
        """Do nothing.  (Yes, seriously.)
        """
        pass
    
    def _get_indentation_level(self, indent):
        if indent == None:
            indent = ''
            
        # Make sure that indentation by tabs are expanded.
        indent = indent.expandtabs()
        
        if indent not in self._indentation_level:
            if len(indent) < max(len(key) for key in self._indentation_level):
                # The indentation levels should be monotonically
                # increasing.  The first time an indentation level is
                # used, it is also defined and available for the rest
                # of the session.
                raise IndentationError, \
                      'On line %d in file "%s:\n%s' \
                      % ((self._line_num + 1), self._current_file,
                         self._current_line)
            else:
                self._indentation_level[indent] = len(self._indentation_level)
                
        return self._indentation_level[indent]
    
    def _get_current_parent(self):
        return self._elements and self._elements[-1].identity or None
    
    def handle_entry(self, indent=None, **rest):
        indent_level = self._get_indentation_level(indent)
        
        # Reduce the _ELEMENTS stack until its length equals the
        # current INDENT_LEVEL.
        while indent_level < len(self._elements):
            self._elements.pop()

        # Push the new entry onto the stack.  The current _ENTRY_CLASS
        # is set by the different meta directives (see
        # handle_meta_directive()).
        self._elements.push(self._entry_class(index=self,
                                              parent=self._get_current_parent(),
                                              **rest))
        
    _match_handler = {
        _meta_directive_re: handle_meta_directive,
        _pure_comment_re: handle_comment,
        _concept_re: handle_entry,
        _acronym_re: handle_entry,
        _person_re: handle_entry,
        }
    
    @classmethod
    def from_file(cls, filename):
        self = cls()

        self._current_file = filename
        
        stream = open(filename, 'r')
        
        for self._line_num, line in enumerate(stream):
            # Ignore whitespace-only lines.
            if line.isspace():
                continue
            
            # Keep a copy of the original line (for error messages,
            # etc.)
            self._current_line = line
            
            # Remove trailing white-space.
            line = line.rstrip()        
            
            # Parse the line trying different matchers.  Quit trying
            # after the first applicable matcher is used.
            for matcher in self._matchers:
                for match in matcher.finditer(line):
                    # Call the appropriate handler, given the current
                    # context.
                    self._match_handler[matcher](self, **match.groupdict())
                    break               # To avoid the else clause.
                else:
                    continue            # The matcher didn't apply, so
                                        # let's try the next one.
                
                break                   # Skip the remaining matchers.
            
        stream.close()            # Explicitly close the input stream.
        
        self._current_file = None
        
        return self

def main():
    """Module mainline (for standalone execution)."""
    pass


if __name__ == "__main__":
    main()
