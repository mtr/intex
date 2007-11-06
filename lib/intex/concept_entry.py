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

from config import FIELD_SEPARATORS
from paren_parser import cartesian
from entry import Entry

class ConceptEntry(Entry):
    _generated_fields = [
        # The values of REFERENCE are how this entry will be referred
        # to in the text (\co{<reference>}).
        'reference',
        'reference_short',
        # The values of TYPESET_IN_TEXT determines how the entry will
        # be typeset in the text.  If it was referred to in its plural
        # form, the entry typeset will also be typeset with plural
        # inflection.
        'typeset_in_text',
        # The values of TYPESET_IN_INDEX defines how the entry will be
        # typeset in the index.
        'typeset_in_index',
        ]
    
    def __init__(self, index, parent, concept=None, indent_level=None,
                 plural=None, index_as=None, sort_as=None, meta=None,
                 alias=None, **rest):
        # Set a couple of defining attributes before calling our base
        # constructor.
        for attribute in self._generated_fields:
            setattr(self, attribute, dict.fromkeys([Entry.INFLECTION_SINGULAR,
                                                    Entry.INFLECTION_PLURAL]))

        # Call the base constructor.
        Entry.__init__(self, index, parent, meta)

        # If this entry is an alias for another entry, indicate that
        # here.
        self.alias = alias
        
        if concept:
            # Unescape escaped field separators.  Other escaped tokens
            # are kept in escaped form.
            concept = self.unescape(concept.strip())
        else:
            concept = ''
            
        self._setup(concept, self._meta, indent_level)

    def generate_index_entries(self, page, typeset_page_number=''):
        inflection = self.index_inflection

        sort_as = self.reference[inflection]
        typeset_in_index = self.typeset_in_index[inflection]

        # If this is an alias entry, the index entries are affected.
        # Generate the index entries accordingly.
        if self.alias:
            concept, _inflection = self.index.references[self.alias]
            for entry in concept.generate_index_entries(page,
                                                        typeset_page_number):
                yield entry

            orig_typeset_in_index = concept.typeset_in_index[inflection]
            yield '\indexentry{%(sort_as)s@' \
                  '%(typeset_in_index)s|see{%(orig_typeset_in_index)s}}' \
                  '{0}' % locals()
                
            return                   # Skip the regular index entries.
        
        parent = self.parent
        
        if parent:
            parent_sort_as = parent.reference[inflection]
            parent_typeset_in_index = parent.typeset_in_index[inflection]
            
            yield '\indexentry{' \
                  '%(parent_sort_as)s@%(parent_typeset_in_index)s!' \
                  '%(sort_as)s@%(typeset_in_index)s' \
                  '%(typeset_page_number)s}{%(page)s}' % locals()
        else:
            yield '\indexentry{%(sort_as)s@%(typeset_in_index)s' \
                  '%(typeset_page_number)s}{%(page)s}' \
                  % locals()

    def generate_internal_macros(self, inflection):
        type_name = self.get_entry_type()
        reference = self.reference[inflection]
        typeset_in_text = self.typeset_in_text[inflection]
        
        yield '\\new%(type_name)s{%(reference)s}{%(typeset_in_text)s}' \
              '{XC.0}' \
              % locals()
        
        if self.use_short_reference and self.reference_short[inflection]:
            reference = self.reference_short[inflection]
            
            yield '\\new%(type_name)s{%(reference)s}{%(typeset_in_text)s}' \
                  '{XC.1}' \
                  % locals()
        
    
    def get_plain_header(self):
        return self._line_format \
               % ('',
                  self.bold_it('singular'.center(self._column_width)),
                  self.bold_it('plural'.center(self._column_width)))

    def __str__(self):
        if self.alias:
            alias_line = '\n' + self._line_format % ('alias', self.alias, '', )
        else:
            alias_line = ''

        return '\n'.join([self._line_format \
                          % (attribute,
                             getattr(self, attribute)['singular'],
                             getattr(self, attribute)['plural'],)
                          for attribute in self._generated_fields]) \
                + alias_line
    
    def _setup(self, concept, meta, indent_level):
        # Trying to figure out the most appropriate features to
        # represent a concept entry:
        (current_inflection, complement_inflection) = \
            self.get_current_and_complement_inflection(meta)
            
        # The INDEX_INFLECTION value defines how the entry should be
        # sorted in the index.  The value is determined by the value
        # of INDEX.DEFAULT_INFLECTION and the given inflection of the
        # current entry.
        self.index_inflection = current_inflection

        field_variable_map = [
            ('reference', 'reference'),
            ('reference_short', 'reference'),
            ('typeset_in_text', 'typeset'),
            ('typeset_in_index', 'typeset')]

        if indent_level == 0:
            # If CONCEPT, then the current entry is a main entry.
            reference, typeset = self.format_reference_and_typeset(concept)
            reference_short = []        # Only used for sub-entries.
            
            for field, variable in field_variable_map:
                value = ' '.join(locals()[variable])
                getattr(self, field)[current_inflection] = value

            if meta.has_key(Entry.META_COMPLEMENT_INFLECTION):
                reference, typeset \
                    = self.format_reference_and_typeset(\
                    meta[Entry.META_COMPLEMENT_INFLECTION])
            else:
                reference, typeset = \
                    self.get_complement_inflections(reference, typeset,
                                                    current_inflection)

            for field, variable in field_variable_map:
                value = ' '.join(locals()[variable])
                getattr(self, field)[complement_inflection] = value
            
        else:
            # This is a sub-entry.
            for inflection in (current_inflection, complement_inflection):
                for field, value \
                    in self.expand_sub_entry(concept, inflection,
                                             current_inflection,
                                             field_variable_map).items():
                    getattr(self, field)[inflection] = value
                    
        for (inflection, attribute) in cartesian(
            (Entry.INFLECTION_SINGULAR, Entry.INFLECTION_PLURAL, ),
            [field for field, variable in field_variable_map]):
            concept = getattr(self, attribute)[inflection]
            getattr(self, attribute)[inflection] \
                = self.unescape(concept.strip(), FIELD_SEPARATORS + '-')

            if current_inflection == Entry.INFLECTION_NONE:
                getattr(self, attribute)[inflection] = \
                    getattr(self, attribute)[Entry.INFLECTION_NONE]
                
        #logging.debug('self = %s', self)
