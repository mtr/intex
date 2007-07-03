#! /usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
"""
Copyright (C) 2007 by Linpro AS
"""
__author__ = "Martin Thorsen Ranang <mtr@linpro.no>"
__revision__ = "$Rev$"
__version__ = "@VERSION@"

import re

from config import FIELD_SEPARATORS, TOKEN_COMMENT, TOKEN_ENTRY_META_INFO
from index_entry import AcronymEntry, ConceptEntry, PersonEntry


class Index(list):
    __concept_types = ['ACRONYMS', 'PEOPLE', 'CONCEPTS']
    __index_attrbiutes = {
        'name': None,
        }

    __re_macros = {
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
    __re_macros['FIELD'] = __re_macros['FIELD'] % __re_macros
    
    # Regular expressions, one pattern matcher for each context:
    __concept_re = re.compile('''
    ^                                   # Starts with
    (?P<indent>\s+)?                    # (possible) indentation,
    (?P<concept>%(FIELD)s)?             # an entry,
    [%(FIELD_SEPARATORS)s]*             # a separator,
    (?P<typeset_as>%(FIELD)s)?          # the full form,
    [%(FIELD_SEPARATORS)s]*             # another separator,
    (?P<meta>%(META_TOKEN)s.+)?         # meta information
    $                                   # at the end.
    ''' % __re_macros, re.VERBOSE)

    __acronym_re = re.compile('''
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
    ''' % __re_macros, re.VERBOSE)

    __person_re = re.compile('''
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
    ''' % __re_macros, re.VERBOSE)

    # A map between context names and the match patterns:
    __context_matcher = {
        'ACRONYMS': __acronym_re,
        'CONCEPTS': __concept_re,
        'PEOPLE': __person_re,
        }

    __context_class = {
        'ACRONYMS': AcronymEntry,
        'CONCEPTS': ConceptEntry,
        'PEOPLE': PersonEntry,
        }
        
    # Add a macro definition to the values available when constructing
    # the regular expressions below.
    __re_macros['CONCEPT_TYPES'] = '|'.join(__context_matcher.keys())

    # A pattern to match meta directives:
    __meta_directive_re = re.compile('''
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
    ''' % __re_macros, re.VERBOSE)

    # A pattern to match comment-only lines.
    __pure_comment_re = re.compile('''
    ^                                   # Starts with
    \s*                                 # possibly some whitespace
    %(COMMENT_TOKEN)s                   # and the comment token,
    .*                                  # followed by anything.
    ''' % __re_macros, re.VERBOSE)

    # A list used to instantiate the context dependent parser.
    __matchers = [
        __meta_directive_re,
        __pure_comment_re,
        None,               # The current context will be placed here.
        ]
    
    def __init__(self, filename=None, index_name='default'):
        """The constructor.
        """
        list.__init__(self)
        
        self.__name = index_name
        self.__current_matchers = list(Index.__matchers)

        self.__indentation_level = {
            '': 0,
            }

        self.__elements = []  # A stack of elements used when parsing.
        #self.__entries = []  # A list of all the entries in the index.
        
    # Accessors for the 'name' property (__-prefixed to force access
    # through the property):
    def __get_name(self):
        return self.__name
        
    def __set_name(self, name):
        self.__name = name
        
    name = property(__get_name, __set_name, None, 'The name of the index.')

    def handle_meta_directive(self, attribute=None, value=None, context=None):
        if attribute:
            # Set an attribute describing this index (e.g., its name).
            setattr(self, attribute, value)
        elif context:
            self.__context = context[1:-1] # Remove pre and post '*'s.
            logging.info('Switching context to: "%s"', self.__context, )
            self.__matchers[-1] = self.__context_matcher[self.__context]
            self.__entry_class = self.__context_class[self.__context]
            
    def handle_comment(self):
        """Do nothing.  (Yes, seriously.)
        """
        pass
    
    def __get_indentation_level(self, indent):
        if indent == None:
            indent = ''
            
        # Make sure that indentation by tabs are expanded.
        indent = indent.expandtabs()
        
        if indent not in self.__indentation_level:
            if len(indent) < max(len(key) for key in self.__indentation_level):
                # The indentation levels should be monotonically
                # increasing.  The first time an indentation level is
                # used, it is also defined and available for the rest
                # of the session.
                raise IndentationError, \
                      'On line %d in file "%s:\n%s' \
                      % ((self.__line_num + 1), self.__current_file,
                         self.__current_line)
            else:
                self.__indentation_level[indent] = len(self.__indentation_level)
                
        return self.__indentation_level[indent]

    def __prepare_element_stack(self, indent):
        level = self.__get_indentation_level(indent)

        while level < len(self.__elements):
            self.__elements.pop()

    def __get_current_parent(self):
        return self.__elements and self.__elements[-1].identity or None
        
    def handle_entry(self, indent=None, **rest):
        self.__prepare_element_stack(indent)
        self.__elements.append(self.__entry_class(self,
                                                  self.__get_current_parent(),
                                                  **rest))
        
    __match_handler = {
        __meta_directive_re: handle_meta_directive,
        __pure_comment_re: handle_comment,
        __concept_re: handle_entry,
        __acronym_re: handle_entry,
        __person_re: handle_entry,
        #__concept_re: handle_concept,
        #__acronym_re: handle_acronym,
        #__person_re: handle_person,
        }
    
    @classmethod
    def from_file(cls, filename):
        self = cls()

        self.__current_file = filename
        
        stream = open(filename, 'r')
        
        for self.__line_num, line in enumerate(stream):
            if line.isspace():
                continue

            # Keep a copy of the original line (for error messages,
            # etc.)
            self.__current_line = line
            
            # Remove trailing white-space.
            line = line.rstrip()        
            
            # Parse the line trying different matchers.  Quit trying
            # after the first applicable matcher is used.
            for matcher in self.__matchers:
                for match in matcher.finditer(line):
                    # Call the appropriate handler, given the current
                    # context.
                    self.__match_handler[matcher](self, **match.groupdict())
                    break               # To avoid the else clause.
                else:
                    continue            # The matcher didn't apply.
                break                   # Skip the remaining matchers.
            
        stream.close()            # Explicitly close the input stream.

        self.__current_file = None
        
        return self


def main():
    """Module mainline (for standalone execution)."""
    pass


if __name__ == "__main__":
    main()
