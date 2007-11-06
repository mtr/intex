#! /usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
"""
Copyright (C) 2007 by Martin Thorsen Ranang
"""
__author__ = "Martin Thorsen Ranang <mtr@ranang.org>"
__revision__ = "$Rev$"
__version__ = "@VERSION@"

from collections import defaultdict
from cStringIO import StringIO
import logging
import re
import sys

from config import (
    FIELD_SEPARATORS,
    INTEX_DEFAULT_INDEX,
    TOKEN_COMMENT,
    TOKEN_ENTRY_META_INFO,
    )
from acronym_entry import AcronymEntry
from concept_entry import ConceptEntry
from person_entry import PersonEntry
from stack import Stack
from utils import flatten, escape_aware_rsplit

import entry

class _IndexError(Exception):
    """Base class for errors in the index module.
    """

class IndexSyntaxError(_IndexError, SyntaxError):
    """Error caused by invalid syntax in the input .itx file.
    """

class Index(list):
    _intex_re = re.compile('\\\@writefile\{%s\}' \
                           '\{\\\indexentry\{(?P<key>.*)\}\{(?P<page>\w+)\}\}' \
                           % (INTEX_DEFAULT_INDEX))
    
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
        'ALIAS_POINTER': '-->',
        }
    # Instantiate/format the FIELD macro value by supplying the other
    # (i.e., FIELD_SEPARATORS, COMMENT_TOKEN, and META_TOKEN) mappings
    # in _RE_MACROS.
    _re_macros['FIELD'] = _re_macros['FIELD'] % _re_macros

    # A regulare expression to match aliasing index entries.
    _alias_re = re.compile('''
    ^                                   # Starts with
    (?P<entry>.+)                       # the entry (including whitespace),
    \s*?%(ALIAS_POINTER)s\s*            # the alias indicator,
    (?P<alias>.+)                       # the entry being aliased,
    $                                   # at the end.
    ''' % _re_macros, re.VERBOSE)
    
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
    (?P<name>%(FIELD)s)?                   # the name,
    [%(FIELD_SEPARATORS)s]*                # another separator
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

    def handle_meta_directive(self, attribute=None, value=None, context=None,
                              alias=None):
        if attribute:
            # Set an attribute describing this index (e.g., its name).
            logging.info('Setting the index\'s %s=%s.', attribute, repr(value))
            setattr(self, attribute, value)
        elif context:
            self._context = context[1:-1] # Remove pre and post '*'s.
            logging.info('Switching context to: "%s"', self._context, )
            self._matchers[-1] = self._context_matcher[self._context]
            self._entry_class = self._context_class[self._context]
            
    def handle_comment(self, alias=None):
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
                raise IndentationError('On line %d in file "%s:\n%s' \
                                       % ((self._line_num + 1),
                                          self._filename,
                                          self._current_line))
            else:
                self._indentation_level[indent] = len(self._indentation_level)
                
        return self._indentation_level[indent]
    
    def _get_current_parent(self):
        if self._elements:
            return self._elements[-1].identity
        else:
            None
            
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
                                              indent_level=indent_level,
                                              **rest))
        
    _match_handler = {
        _meta_directive_re: handle_meta_directive,
        _pure_comment_re: handle_comment,
        _concept_re: handle_entry,
        _acronym_re: handle_entry,
        _person_re: handle_entry,
        }

    @staticmethod
    def syntax_error(filename, line_number, message):
        logging.error('Syntax error on line %d in file "%s": %s',
                      line_number, filename, message)
        sys.exit(1)
                 
    @classmethod
    def from_file(cls, filename):
        self = cls()
        
        self._filename = filename
        
        logging.info('Reading index definitions from "%s".', filename)
        
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

            # Find out whether the entry is an alias for another
            # entry.
            for match in self._alias_re.finditer(line):
                line, alias = map(match.group, ['entry', 'alias'])
                break
            else:
                alias = None
                
            # Parse the line trying different matchers.  Quit trying
            # after the first applicable matcher is used.
            for matcher in self._matchers:
                if matcher is None:
                    self.syntax_error(filename, (self._line_num + 1),
                                      "Encountered an entry, but no " \
                                      "current entry type " \
                                      "('*ACRONYMS*', '*CONCEPTS*', or " \
                                      "'*PERSONS*') has been defined.")

                for match in matcher.finditer(line):
                    # Call the appropriate handler, given the current
                    # context.
                    try:
                        self._match_handler[matcher](self, alias=alias,
                                                     **match.groupdict())
                    except entry.MissingAcronymExpansionError, e:
                        self.syntax_error(filename, (self._line_num + 1),
                                          'Missing full-form expansion for ' \
                                          'acronym definition of "%s".' \
                                          % (e.message, ))
                    except:
                        raise
                    break               # To avoid the else clause.
                else:
                    continue            # The matcher didn't apply, so
                                        # let's try the next one.
                
                break                   # Skip the remaining matchers.
            
        stream.close()            # Explicitly close the input stream.
        
        return self

    def __str__(self):
        stream = StringIO()
        previous_type = None
        for entry in self:
            if type(entry) != previous_type:
                print >> stream, entry.get_plain_header()
                
            print >> stream, entry

            previous_type = type(entry)
            
        string = stream.getvalue()
        stream.close()
        
        return string

    def generate_reference_index(self):
        references = defaultdict(set)
        
        for entry in self:
            for inflection, phrase in entry.reference_short.iteritems():
                if phrase:
                    references[phrase].add(entry)

        ambiguous_short_references = [
            entries
            for phrase, entries in sorted(references.iteritems())
            if len(entries) > 1]
        
        for entries in ambiguous_short_references:
            logging.warn('The short-form references for the entries\n'
                         '%s\nare the same (%s) and hence ambiguous.  '
                         'Hence, the entries must be referred to using '
                         'the full form references.',
                         '\nand\n'.join(str(entry) for entry in entries),
                         list(entries)[0].reference_short['singular'])

        ambiguous_short_references = set(flatten(ambiguous_short_references))

        references = dict()
        
        for entry in self:
            for inflection, phrase in entry.reference.iteritems():
                if phrase in references:
                    logging.error('Duplicate full-form reference "%s" ' \
                                  'detected.  Please correct the file "%s".', \
                                  phrase, self._filename)
                    sys.exit(1)
                    
                references[phrase] = (entry, inflection)

            if entry not in ambiguous_short_references:
                for inflection, phrase in entry.reference_short.iteritems():
                    references[phrase] = (entry, inflection)

                use_short_reference = True
            else:
                use_short_reference = False

            entry.use_short_reference = use_short_reference

        self.references = references

    def get_auxiliary_entries(self, filename):
        for i, line in enumerate(open(filename, 'r')):
            line_number = (i + 1)
            match = self._intex_re.match(line.rstrip())
            if not match:
                yield (line_number, False, line)
                continue
            key, page = match.groups()

            # Keep track of any page-number typesetting hints.
            parts = escape_aware_rsplit(key, '|', 1)

            if len(parts) > 1:
                key, typeset_page_number = parts
                typeset_page_number = '|' + typeset_page_number
            else:
                typeset_page_number = ''
                
            # Do _not_ try to convert page into an integer, it may
            # occurr as roman numerals.
            yield (line_number, True, (key, page, typeset_page_number))
            
    def interpret_auxiliary(self, auxiliary_filename, internal_file,
                            index_file):
        not_found = set()
        already_output = set()
        already_handled = set()
        
        for line_number, is_concept, data \
                in self.get_auxiliary_entries(auxiliary_filename):
            if not is_concept:
                logging.debug('Ignoring non-concept: "%s" on line %d in "%s".',
                              data.rstrip(), line_number, auxiliary_filename)
                continue
            
            key, page, typeset_page_number = data

            logging.debug('Handling reference "%s" on page %s.', key, page)
            
            if key not in self.references:
                if key.lower() in self.references:
                    key = key.lower()
                    logging.debug('lowered key: %s', key)
                else:
                    not_found.add((key, page))
                    continue
            
            concept, inflection = self.references[key]
            logging.debug('Reference expanded to %s (inflection=%s)',
                          repr(concept), inflection)
            
            for line in concept.generate_index_entries(page,
                                                       typeset_page_number):
                if line not in already_output:
                    print >> index_file, line
                    already_output.add(line)
                    
            if key not in already_handled:
                for line in concept.generate_internal_macros(inflection):
                    if line not in already_output:
                        print >> internal_file, line
                        already_output.add(line)

                already_handled.add(key)
            
        return not_found

        
def main():
    """Module mainline (for standalone execution).
    """
    pass

if __name__ == "__main__":
    main()
