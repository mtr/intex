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

from config import FIELD_SEPARATORS, TOKEN_ENTRY_META_INFO

def normalize(string, token=None):
    """Returns a new string where multiple consecutive occurences of
    TOKEN have been replaced by a single occurence.  If TOKEN is None,
    it is interpreted as white-space.
    """
    return (token or ' ').join(string.split(token))

class IndexEntry(object):
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

    __shorthand_inflection = {
        '+': INFLECTION_PLURAL,
        '-': INFLECTION_SINGULAR,
        }
    
    __unescape_re = re.compile(r'(?P<pre>.*?)[\\](?P<post>[%s])' \
                               % FIELD_SEPARATORS)

    # Regular expression for splitting inside meta-fields, but taking
    # care of not splitting on escaped "split-tokens".
    __meta_split_re = re.compile(r'''
    (?<![\\])              # If the previous token was not a "\", then
    %s                     # match a TOKEN_ENTRY_META_INFO.
    ''' % (TOKEN_ENTRY_META_INFO), re.VERBOSE)
    
    def __init__(self, index, parent):
        index.append(self)
        self.__identity = (len(index) - 1)
        self.__index = index
        self.__parent = parent
        self.__children = set()

        if self.parent:
            # Include ourselves among our parent's children.
            self.parent.add_child(self.__identity)

    def parse_meta(self, meta):
        parts = self.__meta_split_re.split(meta)
        
        info = dict()
        
        assert(parts[0] == '')

        for part in parts[1:]:
            if not part:
                logging.error('Unsuspected data in meta directive.')
                
            if not part.startswith('#'):
                info[self.META_TEXT_VS_INDEX_HINT] = part
                continue
            
            if len(part) == 2:
                assert(part[-1] in self.__shorthand_inflection)
                info[self.META_GIVEN_INFLECTION] = \
                            self.__shorthand_inflection[part[1:]]
                
            else:
                info[self.META_PLURAL_FORM] = part[1:]
            
        return info

    def unescape(self, string):
        return self.__unescape_re.sub('\g<pre>\g<post>', string)
    
    # Accessors for the 'identity' property (__-prefixed to force
    # access through the property):
    def __get_identity(self):
        return self.__identity
        
    def __set_identity(self, identity):
        self.__identity = identity
        
    identity = property(__get_identity, __set_identity, None,
                        'The identity of this entry.')

    # Accessors for the 'parent' property (__-prefixed to force
    # access through the property):
    def __get_parent(self):
        if self.__parent == None:
            return None
        return self.__index[self.__parent]
        
    def __set_parent(self, parent):
        self.__parent = parent
        
    parent = property(__get_parent, __set_parent, None,
                      'The parent of this entry.')

    def add_child(self, child_identity):
        self.__children.add(child_identity)
        
    # Accessors for the 'children' property (__-prefixed to force
    # access through the property):
    def __get_children(self):
        return [self.__index[child_id]
                for child_id in sorted(self.__children)]
        
    children = property(__get_children, None, None,
                        'The children of this entry.')

    # Accessors for the 'index' property (__-prefixed to force
    # access through the property):
    def __get_index(self):
        return self.__index

    index = property(__get_index, None, None,
                     'The index that this entry belongs to.')
    
    def to_latex(self):
        raise NotImplementedError

class AcronymEntry(IndexEntry):

    def __init__(self, index, parent, acronym=None,
                 full_form=None, typeset_as=None, plural=None,
                 index_as=None, sort_as=None, meta=None, **rest):
        # Register this entry in the INDEX, set our PARENT and if we
        # do have a parent, add ourselves to that PARENT's set of
        # children.
        IndexEntry.__init__(self, index, parent)
        
        self.__acronym = acronym
        self.__full_form = full_form
        self.__typeset_as = typeset_as

class ConceptEntry(IndexEntry):
    # Note that the order is significant (also when the pairs are
    # reversed below).
    __plural_singular = [
        ('ies', 'y'),
        ('ses', 's'),
        ('s', ''),
        ]

    __singular_plural = [(singular, plural)
                         for plural, singular in __plural_singular]

    __inflection_pair = {
        IndexEntry.INFLECTION_PLURAL:   __plural_singular,
        IndexEntry.INFLECTION_SINGULAR: __singular_plural,
        }

    __placeholder_meaning = {
        '-':   IndexEntry.PLACEHOLDER_IN_TEXT_AND_INDEX,
        '(-)': IndexEntry.PLACEHOLDER_IN_TEXT_ONLY,
        }

    __hint_re = re.compile('(?P<placeholder>%s)' \
                           % '|'.join(map(re.escape, __placeholder_meaning)))
        
    def __init__(self, index, parent, concept=None,
                 plural=None, index_as=None, sort_as=None, meta=None,
                 **rest):
        IndexEntry.__init__(self, index, parent)

        if concept:
            self.__concept = self.unescape(concept.strip())
        else:
            self.__concept = ''

        if meta:
            self.__meta = self.parse_meta(meta.strip())
        else:
            self.__meta = dict()
            
        self.__in_text = []
        self.__typeset_in_text = []
        self.__in_index = []
        self.__typeset_in_index = []
        
        self.__setup()
        
        print self
        
    def __str__(self):
        return '\n'.join(description + ': {' \
                         + ', '.join(map(repr, variants)) + '}'
                         for description, variants \
                         in [('in_text', self.__in_text),
                             ('in_index', self.__in_index),])

    def change_inflection(self, word, inflection_pairs):
        for suffix, replacement in inflection_pairs:
            if word.endswith(suffix):
                offset = (- len(suffix)) or None
                return word[:offset] + replacement
            
        return word

    def __setup(self):
        if self.__concept:
            self.__in_text.append(self.__concept)
            
            if self.META_GIVEN_INFLECTION in self.__meta:
                current_inflection = self.__meta[self.META_GIVEN_INFLECTION]
            else:
                current_inflection = self.index.default_inflection

            inflection_pairs = self.__inflection_pair[current_inflection]
            
            self.__in_text.append(\
                    self.change_inflection(self.__in_text[0],
                                           inflection_pairs))
            
        elif self.__meta[self.META_TEXT_VS_INDEX_HINT]:
            template = self.__meta[self.META_TEXT_VS_INDEX_HINT]
            for match in self.__hint_re.finditer(template):
                placeholder = match.group('placeholder')
                i, j = match.span('placeholder')
                for variant in  self.parent.__in_text:
                    # Construct the new phrase.
                    phrase = template[:i] + variant + template[j:]
                    
                    # Add the new phrase to the in-text variants.
                    self.__in_text.append(phrase)
                    
                    if self.__placeholder_meaning[placeholder] \
                           == self.PLACEHOLDER_IN_TEXT_AND_INDEX:
                        self.__in_index.append(phrase)
                    else:
                        normalized = normalize(template[:i] + template[j:])
                        self.__in_index.append(normalized)
                        
                print template[i:j]
                
class PersonEntry(IndexEntry):
    def __init__(self, index, parent, initials=None,
                 last_name=None, first_name=None, index_as=None,
                 sort_as=None, meta=None, **rest):
        IndexEntry.__init__(self, index, parent)
        
        self.__initials = initials
        self.__last_name = last_name
        self.__first_name = first_name


def main():
    """Module mainline (for standalone execution).
    """
    pass

if __name__ == "__main__":
    main()
