#! /usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
"""
Copyright (C) 2007 by Martin Thorsen Ranang
"""
__author__ = "Martin Thorsen Ranang <mtr@ranang.org>"
__revision__ = "$Rev$"
__version__ = "@VERSION@"

import logging
import re

from config import FIELD_SEPARATORS, TOKEN_ENTRY_META_INFO, TOKEN_TYPESET_AS
from paren_parser import ParenParser
from utils import flatten, escape_aware_split, escape_aware_rsplit

ESCAPE_TOKEN = '\\'
ALIAS_INDICATOR = '-->'

def normalize(string, token=None):
    """Returns a new string where multiple consecutive occurences of
    TOKEN have been replaced by a single occurence.  If TOKEN is None,
    it is interpreted as white-space.
    """
    return (token or ' ').join(string.split(token))

class EntryError(Exception):
    """Base class for errors in the entry module.
    """

class MissingAcronymExpansionError(EntryError):
    """This error occurrs when a main acronym entry is missing a
    full-form expansion.
    """
class MultipleAliasIndicatorsError(EntryError):
    """Multiple alias indicators ('%(ALIAS_INDICATOR)s') were
    detected.
    """

class Entry(object):
    paren_parser = ParenParser()
    
    # Define a number of class constants, each string will be defined
    # as an all-uppercase "constant".  That is 'this_value' is
    # assigned to __class__.THIS_VALUE.
    for constant in (
        # Different meta fields:
        'meta_complement_inflection',
        'meta_given_inflection',
        'meta_text_vs_index_hint',
        # Some inflection values:
        'inflection_plural',
        'inflection_singular',
        'inflection_none',
        # For capitalization support:
        'inflection_plural_capitalized',
        'inflection_singular_capitalized',
        'inflection_none_capitalized',
        # Meaning of placeholders:
        'placeholder_in_text_and_index',
        'placeholder_in_index_only',
        ):
        exec("%s='%s'" % (constant.upper(),
                          ''.join(constant.split('_', 1)[1:])))

    _capitalized = {
        INFLECTION_PLURAL: INFLECTION_PLURAL_CAPITALIZED,
        INFLECTION_SINGULAR: INFLECTION_SINGULAR_CAPITALIZED,
        INFLECTION_NONE: INFLECTION_NONE_CAPITALIZED,
        }
    
    _shorthand_inflection = {
        '+': INFLECTION_PLURAL,
        '-': INFLECTION_SINGULAR,
        '!': INFLECTION_NONE,
        }

    _complement_inflection = {
        INFLECTION_SINGULAR: INFLECTION_PLURAL,
        INFLECTION_PLURAL: INFLECTION_SINGULAR,
        INFLECTION_NONE: INFLECTION_NONE,
        }
    
    _unescape_re = re.compile(r'(?P<pre>.*?)[\\](?P<post>[%s])' \
                               % FIELD_SEPARATORS)
    
    # Regular expression for splitting inside meta-fields, but taking
    # care of not splitting on escaped "split-tokens".
    _meta_split_re = re.compile(r'''
    (?<![\\])              # If the previous token was not a "\", then
    %s                     # match a TOKEN_ENTRY_META_INFO.
    ''' % (TOKEN_ENTRY_META_INFO), re.VERBOSE)

    # Note that the order is significant (also when the pairs are
    # reversed below).
    _plural_to_singular = [
        ('ies', 'y'),
        ('ses', 's'),
        ('s', ''),
        ]

    _singular_to_plural = [(singular, plural)
                           for plural, singular in _plural_to_singular]

    _none_to_none = []
    
    _inflection_pair = {
        INFLECTION_SINGULAR: _plural_to_singular,
        INFLECTION_PLURAL: _singular_to_plural,
        INFLECTION_NONE: _none_to_none,
        }
    
    _placeholder_meaning = {
        '-':   PLACEHOLDER_IN_TEXT_AND_INDEX,
        '(-)': PLACEHOLDER_IN_INDEX_ONLY,
        }
    
    _hint_re = re.compile('(?P<placeholder>%s)' \
                          % '|'.join(map(re.escape, _placeholder_meaning)))

    # Different constants and defaults used for output formatting.
    _bold_on = '\033[1m'
    _bold_off = '\033[0m'

    # These parameters may (and should) be overridden in derived
    # classes.
    _label_width = len('typeset_in_index')
    _column_width = 28
    _line_format = '%(_bold_on)s%%%(_label_width)ds%(_bold_off)s ' \
                   '%%-%(_column_width)ds ' \
                   '%%-%(_column_width)ds' 
    
    def __init__(self, index, parent, meta):
        index.append(self)

        self._identity = (len(index) - 1)
        self._index = index
        self._parent = parent
        self._children = set()

        if self.parent:
            # Include ourselves among our parent's children.
            self.parent.add_child(self._identity)
        
        if meta:
            self._meta = self.parse_meta(meta.strip())
        else:
            self._meta = dict()

        # Define appropriate output formatting.
        mapping = dict((key, getattr(self, key)) for key in dir(self))
        self._line_format = self._line_format % mapping
        
    def bold_it(self, string):
        return self._bold_on + string + self._bold_off

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join('%s=%s' \
                                     % (attribute, getattr(self, attribute))
                                     for attribute in self._generated_fields))

    def generate_index_entries(self, page, typeset_page_number=None):
        raise NotImplementedError('This method must be implemented in '
                                  'derived classes.')

    def get_entry_type(self):
        return self.__class__.__name__[:- len('Entry')].lower()

    def generate_internal_macros(self, inflection):
        raise NotImplementedError('This method must be implemented in '
                                  'derived classes.')
    
    def parse_meta(self, meta):
        """Parse the metadata fields of an entry definition and return
        their interpretations.
        """
        parts = self._meta_split_re.split(meta)
        
        info = dict()
        
        assert(parts[0] == '')

        for part in parts[1:]:
            if not part:
                logging.error('Unsuspected data in meta directive.')
                
            if not part.startswith('#'):
                info[self.META_TEXT_VS_INDEX_HINT] = part
                continue
            
            if len(part) == 2:
                assert(part[-1] in self._shorthand_inflection)
                info[self.META_GIVEN_INFLECTION] = \
                                         self._shorthand_inflection[part[1:]]
                
            else:
                info[self.META_COMPLEMENT_INFLECTION] = part[1:]
                
        return info

    def get_alias_if_defined(self, string):
        parts = escape_aware_split(string, ALIAS_INDICATOR)

        if len(parts) < 2:
            return string, None
        elif len(parts) == 2:
            return parts[0].rstrip(), parts[1].lstrip()
        else:
            raise MultipleAliasIndicatorsError('string="%s"' % string) 
            
    def unescape(self, string, escaped_tokens=FIELD_SEPARATORS):
        """Unescapes escaped field separators.
        """
        # It must shrink or stay the same size.  It cannot grow.
        new = list(string) 
        
        previous_was_escape = False
        previous_token = None
        
        for i, token in reversed(list(enumerate(string))):
            if (token == ESCAPE_TOKEN) \
                   and (previous_token in escaped_tokens) \
                   and not (previous_token == ESCAPE_TOKEN):
                # If CONTIGUOUS_ESCAPES is zero or even.
                del new[i]
                
            previous_token = token
            
        return ''.join(new)
        #return self._unescape_re.sub('\g<pre>\g<post>', string)

    def get_complement_inflections(self, reference, typeset,
                                   current_inflection):
        result = []
        
        for words in [reference, typeset]:
            copy = words[:]        # Make a copy of the list of words.
            
            copy[-1] = self.change_inflection(copy[-1], current_inflection)
            
            result.append(copy)
            
        return result

    def get_inflection(self, word, inflection):
        for suffix, replacement in self._inflection_pair[inflection]:
            if word.endswith(suffix):
                offset = (- len(suffix)) or None
                return word[:offset] + replacement
            
        return word
    
    def change_inflection(self, word, current_inflection):
        return self.get_inflection(
            word, self._complement_inflection[current_inflection])

    def get_current_and_complement_inflection(self, meta):
        if Entry.META_GIVEN_INFLECTION in meta:
            # If a specific inflection was indicated through the
            # meta information, use that.
            current_inflection = meta[Entry.META_GIVEN_INFLECTION]
        else:
            # If not, use the DEFAULT_INFLECTION of the INDEX.
            current_inflection = self.index.default_inflection

        complement_inflection = self._complement_inflection[current_inflection]

        return current_inflection, complement_inflection

    def escape_aware_split(self, string, delimiter=None, maxsplit=None):
        parts = self.paren_parser.split(string, delimiter, maxsplit)

        for i, part in reversed(list(enumerate(parts))):
            if part[-1] == ESCAPE_TOKEN:
                parts[i] = delimiter.join((parts[i], parts[i + 1]))
                del parts[i + 1]
                
        return parts

    def format_reference_and_typeset(self, string, strip_parens=True):
        parts = self.paren_parser.split(string)
        
        if strip_parens:
            parts = [self.paren_parser.strip(part, '([') for part in parts]
            
        reference = []
        typeset = []
        
        for part in parts:
            # FIXME: At the time this was written (2007-07-05)
            # ParenParser.split did not honor its MAXSPLIT argument (1
            # below).
            alternatives = self.escape_aware_split(part, TOKEN_TYPESET_AS, 1)
            
            if strip_parens:
                alternatives = [self.paren_parser.strip(alternative, '([')
                                for alternative in alternatives]

            reference.append(alternatives[0])
            
            if len(alternatives) > 1:
                typeset.append(alternatives[1])
            else:
                typeset.append(alternatives[0])

        reference = flatten(self.escape_aware_split(part) for part in reference)
        typeset = flatten(self.escape_aware_split(part) for part in typeset)
        
        return reference, typeset

    def is_escaped(self, string, i):
        """Returns True if the token in STRING at position I is escaped.
        """
        if i > 0:
           for n, character in enumerate(string[(i - 1)::-1]):
               if character != ESCAPE_TOKEN:
                   break
        else:
            n = 0                 # The token can't have been escaped.

        return bool(n & 1)       # Is the number of escape tokens odd?

    def expand_sub_entry_part(self, template, is_last_token, inflection,
                              current_inflection, field):
        """

        Note: CURRENT_INFLECTION refers to the inflection given in the
        source file, while INFLECTION is the target inflection of the
        entry we are generating.
        """
        formatted = ''
        
        k = None

        for match in self._hint_re.finditer(template):
            placeholder = match.group('placeholder')
            i, j = match.span('placeholder')

            # Check if the PLACEHOLDER token is escaped or not.  If it
            # is, then do nothing.
            if self.is_escaped(template, i):
                continue

            # Select the approriate replacement phrase from the
            # parent, based on the target INFLECTION.
            if not is_last_token:
                source = getattr(self.parent, field)['singular']
            else:
                source = getattr(self.parent, field)[inflection]

            # Construct the new phrase.
            #if (self._placeholder_meaning[placeholder] \
            #    == self.PLACEHOLDER_IN_INDEX_ONLY) \
            #   and (field.startswith('typeset_in_index')):
            #    formatted += template[k:i] + '--'
            #print self._placeholder_meaning
            #print self._placeholder_meaning[placeholder]

            if field.startswith('typeset_in_index'):
                formatted += template[k:i] + '--'
            elif ((field == 'reference_short') \
                  or field.startswith('typeset_in_text')) \
                 and (self._placeholder_meaning[placeholder] \
                      == self.PLACEHOLDER_IN_INDEX_ONLY):
                formatted += template[k:i]
            else:
                formatted += template[k:i] + source

            k = j
            
            break
        else:
            # If nothing really got replaced.
            if is_last_token:
                if inflection == current_inflection:
                    formatted = template
                else:
                    formatted = self.get_inflection(template, inflection)
                    
                k = len(template)

        if k < len(template):
            formatted += template[k:]
            
        return formatted

    def expand_sub_entry(self, template, inflection, current_inflection,
                         field_variable_map, template_long=None):
        reference, typeset = self.format_reference_and_typeset(template, False)
        
        if template_long:
            sort_as_long, typeset_long \
                = self.format_reference_and_typeset(template_long, False)
            
        results = dict()
        variables = locals()

        #print template
        
        for field, variable in field_variable_map:
            if not variables.has_key(variable):
                continue
            
            parts = variables[variable]
            template_list = [
                self.expand_sub_entry_part(part, (pos == (len(parts) - 1)),
                                           inflection, current_inflection,
                                           field)
                for pos, part in enumerate(parts)]
            
            # Remove empty/blank elements.
            template_list = [part for part in template_list if part]
            
            results[field] = ' '.join(template_list)
            
        return results
    
    # Accessors for the 'identity' property (_-prefixed to force
    # access through the property):
    def _get_identity(self):
        return self._identity
        
    def _set_identity(self, identity):
        self._identity = identity
        
    identity = property(_get_identity, _set_identity, None,
                        'The identity of this entry.')

    # Accessors for the 'parent' property (_-prefixed to force
    # access through the property):
    def _get_parent(self):
        if self._parent == None:
            return None
        return self._index[self._parent]
        
    def _set_parent(self, parent):
        self._parent = parent
        
    parent = property(_get_parent, _set_parent, None,
                      'The parent of this entry.')

    def add_child(self, child_identity):
        self._children.add(child_identity)
        
    # Accessors for the 'children' property (_-prefixed to force
    # access through the property):
    def _get_children(self):
        return [self._index[child_id]
                for child_id in sorted(self._children)]
        
    children = property(_get_children, None, None,
                        'The children of this entry.')

    # Accessors for the 'index' property (_-prefixed to force
    # access through the property):
    def _get_index(self):
        return self._index

    index = property(_get_index, None, None,
                     'The index that this entry belongs to.')
    
    def to_latex(self):
        raise NotImplementedError

    @staticmethod
    def capitalize(string):
        for i, token in enumerate(string):
            if token.isalpha():
                return string[:i] + token.upper() + string[i + 1:]
            
        return string

def main():
    """Module mainline (for standalone execution).
    """
    pass

if __name__ == "__main__":
    main()
