#! /usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
"""
Copyright (C) 2007 by Linpro AS
"""
__author__ = "Martin Thorsen Ranang <mtr@linpro.no>"
__revision__ = "$Rev$"
__version__ = "@VERSION@"

from functools import partial
import logging
import re

from config import FIELD_SEPARATORS, TOKEN_ENTRY_META_INFO, TOKEN_TYPESET_AS
from parenparser import ParenParser, remove_inner_scopes

def normalize(string, token=None):
    """Returns a new string where multiple consecutive occurences of
    TOKEN have been replaced by a single occurence.  If TOKEN is None,
    it is interpreted as white-space.
    """
    return (token or ' ').join(string.split(token))

class Entry(object):
    parenparser = ParenParser()
    
    # Define a number of class constants, each string will be defined
    # as an all-uppercase "constant".  That is 'this_value' is
    # assigned to __class__.THIS_VALUE.
    for constant in (
        # Different meta fields:
        'meta_plural_form',
        'meta_given_inflection',
        'meta_text_vs_index_hint',
        # Some inflection values:
        'inflection_plural',
        'inflection_singular',
        # Meaning of placeholders:
        'placeholder_in_text_and_index',
        'placeholder_in_text_only',
        ):
        exec("%s='%s'" % (constant.upper(),
                          ''.join(constant.split('_', 1)[1:])))

    _shorthand_inflection = {
        '+': INFLECTION_PLURAL,
        '-': INFLECTION_SINGULAR,
        }
    
    _unescape_re = re.compile(r'(?P<pre>.*?)[\\](?P<post>[%s])' \
                               % FIELD_SEPARATORS)

    # Regular expression for splitting inside meta-fields, but taking
    # care of not splitting on escaped "split-tokens".
    _meta_split_re = re.compile(r'''
    (?<![\\])              # If the previous token was not a "\", then
    %s                     # match a TOKEN_ENTRY_META_INFO.
    ''' % (TOKEN_ENTRY_META_INFO), re.VERBOSE)
    
    def __init__(self, index, parent):
        index.append(self)
        self._identity = (len(index) - 1)
        self._index = index
        self._parent = parent
        self._children = set()

        if self.parent:
            # Include ourselves among our parent's children.
            self.parent.add_child(self._identity)

    def parse_meta(self, meta):
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
                info[self.META_PLURAL_FORM] = part[1:]
                
        return info

    def unescape(self, string):
        return self._unescape_re.sub('\g<pre>\g<post>', string)
    
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

class AcronymEntry(Entry):

    def __init__(self, index, parent, acronym=None,
                 full_form=None, typeset_as=None, plural=None,
                 index_as=None, sort_as=None, meta=None, **rest):
        # Register this entry in the INDEX, set our PARENT and if we
        # do have a parent, add ourselves to that PARENT's set of
        # children.
        Entry.__init__(self, index, parent)
        
        self._acronym = acronym
        self._full_form = full_form
        self._typeset_as = typeset_as

class ConceptEntry(Entry):
    # Note that the order is significant (also when the pairs are
    # reversed below).
    _plural_to_singular = [
        ('ies', 'y'),
        ('ses', 's'),
        ('s', ''),
        ]

    _singular_to_plural = [(singular, plural)
                           for plural, singular in _plural_to_singular]

    _inflection_pair = {
        Entry.INFLECTION_PLURAL:   _plural_to_singular,
        Entry.INFLECTION_SINGULAR: _singular_to_plural,
        }
    
    _placeholder_meaning = {
        '-':   Entry.PLACEHOLDER_IN_TEXT_AND_INDEX,
        '(-)': Entry.PLACEHOLDER_IN_TEXT_ONLY,
        }

    _hint_re = re.compile('(?P<placeholder>%s)' \
                           % '|'.join(map(re.escape, _placeholder_meaning)))
        
    def __init__(self, index, parent, concept=None,
                 plural=None, index_as=None, sort_as=None, meta=None,
                 **rest):
        Entry.__init__(self, index, parent)

        if concept:
            concept = self.unescape(concept.strip())
        else:
            concept = ''
            
        if meta:
            meta = self.parse_meta(meta.strip())
        else:
            meta = dict()
            
        #self._in_text = []
        #self._typeset_in_text = []
        #self._in_index = []
        #self._typeset_in_index = []

        self._setup(concept, meta)
        
        #logging.info('concept: "%s".', self._concept)
        
        #print self
        
    def __str__(self):
        return '\n'.join(description + ': {' \
                         + ', '.join(map(repr, variants)) + '}'
                         for description, variants \
                         in [('in_text', self._in_text),
                             ('in_index', self._in_index),])

    def change_inflection(self, word, inflection_pairs):
        for suffix, replacement in inflection_pairs:
            if word.endswith(suffix):
                offset = (- len(suffix)) or None
                return word[:offset] + replacement
            
        return word

    def generate_reference_and_typeset(self, string):
        print string
        scopes = sorted(self.parenparser.get_scope_spans(string))

        outer_scopes = dict(remove_inner_scopes(scopes))
        
        for n, token in enumerate(string):
            if token == TOKEN_TYPESET_AS:
                if (n + 1) in outer_scopes:
                    j = outer_scopes[(n + 1)]
                    print string[n+1:j]
            
        print outer_scopes
        
    def _setup(self, concept, meta):
        # Trying to figure out the most appropriate features to
        # represent a concept entry:
        
        # The values of REFERENCE are how this entry will be referred
        # to in the text (\co{<reference>}).
        self.reference = dict.fromkeys([Entry.INFLECTION_SINGULAR,
                                        Entry.INFLECTION_PLURAL])

        # The values of TYPESET_IN_TEXT determines how the entry will
        # be typeset in the text.  If it was referred to in its plural
        # form, the entry typeset will also be typeset with plural
        # inflection.
        self.typeset_in_text = dict.fromkeys([Entry.INFLECTION_SINGULAR,
                                              Entry.INFLECTION_PLURAL])

        # The values of TYPESET_IN_INDEX defines how the entry will be
        # typeset in the index.
        self.typeset_in_index = dict.fromkeys([Entry.INFLECTION_SINGULAR,
                                               Entry.INFLECTION_PLURAL])

        # The ORDER_BY value defines how the entry should be sorted in
        # the index.  The value is determined by the value of
        # INDEX.DEFAULT_INFLECTION and the given inflection of the
        # current entry.
        self.order_by = None

        # If not CONCEPT, then the current entry is a sub-entry.
        if concept:
            self.generate_reference_and_typeset(concept)
            #self._in_text.append(concept)
            
            # If a specific inflection was indicated through the meta
            # information, use that.  If not, use the
            # DEFAULT_INFLECTION of the INDEX.
            if Entry.META_GIVEN_INFLECTION in meta:
                current_inflection = meta[Entry.META_GIVEN_INFLECTION]
            else:
                current_inflection = self.index.default_inflection
                
            inflection_pairs = self._inflection_pair[current_inflection]
            
            #self._in_text.append(self.change_inflection(concept,
            #                                            inflection_pairs))
            
            #self.reference[
            
#         elif self._meta[self.META_TEXT_VS_INDEX_HINT]:
#             template = self._meta[self.META_TEXT_VS_INDEX_HINT]
#             for match in self._hint_re.finditer(template):
#                 placeholder = match.group('placeholder')
#                 i, j = match.span('placeholder')
#                 for variant in  self.parent._in_text:
#                     # Construct the new phrase.
#                     phrase = template[:i] + variant + template[j:]
                    
#                     # Add the new phrase to the in-text variants.
#                     self._in_text.append(phrase)
                    
#                     if self._placeholder_meaning[placeholder] \
#                            == self.PLACEHOLDER_IN_TEXT_AND_INDEX:
#                         self._in_index.append(phrase)
#                     else:
#                         normalized = normalize(template[:i] + template[j:])
#                         self._in_index.append(normalized)
                        
#                 print template[i:j]
                
class PersonEntry(Entry):
    def __init__(self, index, parent, initials=None,
                 last_name=None, first_name=None, index_as=None,
                 sort_as=None, meta=None, **rest):
        Entry.__init__(self, index, parent)
        
        self._initials = initials
        self._last_name = last_name
        self._first_name = first_name


def main():
    """Module mainline (for standalone execution).
    """
    pass

if __name__ == "__main__":
    main()
