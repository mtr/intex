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
from parenparser import ParenParser, cartesian

def normalize(string, token=None):
    """Returns a new string where multiple consecutive occurences of
    TOKEN have been replaced by a single occurence.  If TOKEN is None,
    it is interpreted as white-space.
    """
    return (token or ' ').join(string.split(token))

class Entry(dict):
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
        # Meaning of placeholders:
        'placeholder_in_text_and_index',
        'placeholder_in_text_only',
        ):
        exec("%s='%s'" % (constant.upper(),
                          ''.join(constant.split('_', 1)[1:])))

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
                info[self.META_COMPLEMENT_INFLECTION] = part[1:]
                
        return info

    def unescape(self, string):
        """Unescapes escaped field separators.
        """
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

    _none_to_none = []
    
    _inflection_pair = {
        Entry.INFLECTION_SINGULAR: _plural_to_singular,
        Entry.INFLECTION_PLURAL: _singular_to_plural,
        Entry.INFLECTION_NONE: _none_to_none,
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
            # Unescape escaped field separators.  Other escaped tokens
            # are kept in escaped form.
            concept = self.unescape(concept.strip())
        else:
            concept = ''
            
        if meta:
            meta = self.parse_meta(meta.strip())
        else:
            meta = dict()
            
        self._setup(concept, meta)

        print self.get_plain_header()
        print self
        print

    # Different constants used for output formatting.
    _bold_on = '\033[1m'
    _bold_off = '\033[0m'
        
    _label_width = len('typeset_in_index')
    _column_width = 28
    _line_format = '%(_bold_on)s%%%(_label_width)ds%(_bold_off)s ' \
                   '%%-%(_column_width)ds ' \
                   '%%-%(_column_width)ds' % locals()

    def bold_it(self, string):
        return self._bold_on + string + self._bold_off

    def get_plain_header(self):
        return self._line_format \
               % ('',
                  self.bold_it('singular'.center(self._column_width)),
                  self.bold_it('plural'.center(self._column_width)))
    
    def __str__(self):
        return '\n'.join([self._line_format \
                          % (attribute,
                             getattr(self, attribute)['singular'],
                             getattr(self, attribute)['plural'],)
                          for attribute in ['reference',
                                            'typeset_in_text',
                                            'typeset_in_index',]])
    

    def get_inflection(self, word, inflection):
        for suffix, replacement in self._inflection_pair[inflection]:
            if word.endswith(suffix):
                offset = (- len(suffix)) or None
                return word[:offset] + replacement
            
        return word
    
    def change_inflection(self, word, current_inflection):
        return self.get_inflection(
            word, self._complement_inflection[current_inflection])
    
    def escape_aware_split(self, string, delimiter=None, maxsplit=None):
        parts = self.paren_parser.split(string, delimiter, maxsplit)

        for i, part in reversed(list(enumerate(parts))):
            if part[-1] == '\\':
                parts[i] = '@'.join((parts[i], parts[i + 1]))
                del parts[i + 1]
                
        return parts
    
    def _format_reference_and_typeset(self, string, strip_parens=True):
        parts = [strip_parens and self.paren_parser.strip(part, '([') or part
                 for part in self.paren_parser.split(string)]
        
        reference = []
        typeset = []
        
        for part in parts:
            # FIXME: At the time this was written (2007-07-05)
            # ParenParser.split did not honor its MAXSPLIT argument (1
            # below).
            alternatives = [(strip_parens \
                             and self.paren_parser.strip(alternative, '([') \
                             or alternative)
                            for alternative
                            in self.escape_aware_split(part,
                                                       TOKEN_TYPESET_AS, 1)]
            reference.append(alternatives[0])
            if len(alternatives) > 1:
                typeset.append(alternatives[1])
            else:
                typeset.append(alternatives[0])
                
        return reference, typeset
    
    def _get_complement_inflections(self, reference, typeset,
                                    current_inflection):
        result = []
        
        for words in [reference, typeset]:
            copy = words[:]        # Make a copy of the list of words.
            
            copy[-1] = self.change_inflection(copy[-1], current_inflection)
            
            result.append(copy)
            
        return result

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

    def is_escaped(self, string, i):
        if i > 0:
           for n, character in enumerate(string[(i - 1)::-1]):
               if character != '\\':
                   break
        else:
            n = 0                 # The token can't have been escaped.

        return bool(n & 1)       # Is the number of escape tokens odd?
    
    def expand_sub_entry_part(self, template, is_last_token, inflection, current_inflection,
            field):
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
            if (self._placeholder_meaning[placeholder] \
                == self.PLACEHOLDER_IN_TEXT_ONLY) \
               and (field == 'typeset_in_index'):
                formatted += template[k:i] + '--'
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
        
    def _expand_sub_entry(self, template, inflection, current_inflection):
        reference, typeset = self._format_reference_and_typeset(template, False)
        
        results = dict()
        
        for parts, field in [
            (reference, 'reference'),
            (typeset, 'typeset_in_text'),
            (typeset, 'typeset_in_index')]:
            template_list = [
                self.expand_sub_entry_part(part, (pos == (len(parts) - 1)),
                                           inflection, current_inflection,
                                           field)
                for pos, part in enumerate(parts)]
            results[field] = ' '.join(template_list)
            
        return results
    
    def _setup(self, concept, meta):
        # Trying to figure out the most appropriate features to
        # represent a concept entry:

        for attribute in [
            # The values of REFERENCE are how this entry will be
            # referred to in the text (\co{<reference>}).
            'reference',
            # The values of TYPESET_IN_TEXT determines how the entry
            # will be typeset in the text.  If it was referred to in
            # its plural form, the entry typeset will also be typeset
            # with plural inflection.
            'typeset_in_text',
            # The values of TYPESET_IN_INDEX defines how the entry
            # will be typeset in the index.
            'typeset_in_index',
            ]:
            setattr(self, attribute, dict.fromkeys([Entry.INFLECTION_SINGULAR,
                                                    Entry.INFLECTION_PLURAL]))

        (current_inflection, complement_inflection) = \
            self.get_current_and_complement_inflection(meta)
            
        # The ORDER_BY value defines how the entry should be sorted in
        # the index.  The value is determined by the value of
        # INDEX.DEFAULT_INFLECTION and the given inflection of the
        # current entry.
        self.order_by = current_inflection

        print meta

        if concept:
            # If CONCEPT, then the current entry is a main entry.
            reference, typeset = self._format_reference_and_typeset(concept)

            self.reference[current_inflection]        = ' '.join(reference)
            self.typeset_in_text[current_inflection]  = ' '.join(typeset)
            self.typeset_in_index[current_inflection] = ' '.join(typeset)

            if meta.has_key(Entry.META_COMPLEMENT_INFLECTION):
                reference, typeset \
                    = self._format_reference_and_typeset(\
                    meta[Entry.META_COMPLEMENT_INFLECTION])
            else:
                reference, typeset = \
                    self._get_complement_inflections(reference, typeset,
                                                     current_inflection)
            
            self.reference[complement_inflection]        = ' '.join(reference)
            self.typeset_in_text[complement_inflection]  = ' '.join(typeset)
            self.typeset_in_index[complement_inflection] = ' '.join(typeset)
            
        else:
            # If not CONCEPT, then the current entry is a sub-entry.
            if meta[self.META_TEXT_VS_INDEX_HINT]:
                template = meta[self.META_TEXT_VS_INDEX_HINT]
                
                for inflection in (current_inflection, complement_inflection):
                    for field, value \
                        in self._expand_sub_entry(template, inflection,
                                                  current_inflection).items():
                        getattr(self, field)[inflection] = value
                        
        if current_inflection == Entry.INFLECTION_NONE:
            for (inflection, attribute) in cartesian(
                (Entry.INFLECTION_SINGULAR, Entry.INFLECTION_PLURAL, ),
                ('reference', 'typeset_in_text', 'typeset_in_index', )):
                getattr(self, attribute)[inflection] = \
                    getattr(self, attribute)[Entry.INFLECTION_NONE]
                
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
