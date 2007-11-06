#! /usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
"""
Copyright (C) 2007 by Martin Thorsen Ranang
"""
__author__ = "Martin Thorsen Ranang <mtr@ranang.org>"
__revision__ = "$Rev$"
__version__ = "@VERSION@"

from entry import Entry

from config import FIELD_SEPARATORS

class AcronymEntry(Entry):
    _generated_fields = [
        # The values of REFERENCE are how this entry will be
        # referred to in the text (\co{<reference>}).
        'reference',
        'reference_short',
        # The values of TYPESET_IN_TEXT determines how the entry
        # will be typeset in the text.  If it was referred to in
        # its plural form, the entry typeset will also be typeset
        # with plural inflection.
        'typeset_in_text_short',
        # The values of TYPESET_IN_INDEX defines how the entry will be
        # typeset in the index.
        'typeset_in_index_short',
        'sort_as_short',
        'typeset_in_text_long',
        'typeset_in_index_long',
        'sort_as_long',
        ]

    # Different constants used for output formatting.
    _label_width = len('typeset_in_index_short')
    
    def __init__(self, index, parent, acronym=None, indent_level=None,
                 full_form=None, meta=None, alias=None, **rest):
        # Set a couple of defining attributes before calling our base
        # constructor.
        for attribute in self._generated_fields:
            setattr(self, attribute, dict.fromkeys([Entry.INFLECTION_SINGULAR,
                                                    Entry.INFLECTION_PLURAL]))
            
        # Register this entry in the INDEX, set our PARENT and if we
        # do have a parent, add ourselves to that PARENT's set of
        # children.
        Entry.__init__(self, index, parent, meta)

        # If this entry is an alias for another entry, indicate that
        # here.
        self.alias = alias

        self._setup(acronym, full_form, self._meta, indent_level)

    def get_index_entry(self, length, inflection):
        sort_as = getattr(self, 'sort_as_' + length)[inflection]
        typeset_in_index = getattr(self,
                                   'typeset_in_index_' + length)[inflection]
        
        return '%(sort_as)s@%(typeset_in_index)s' % locals()
    
    def generate_index_entries(self, page, typeset_page_number=''):
        inflection = self.index_inflection
        
        sort_as_long = self.sort_as_long[inflection]
        sort_as_short = self.sort_as_short[inflection]
        
        typeset_in_index_long = self.typeset_in_index_long[inflection]
        typeset_in_index_short = self.typeset_in_index_short[inflection]

        parent = self.parent

        if parent:
            parent_sort_as_long = parent.sort_as_long[inflection]
            parent_typeset_in_index_long \
                = parent.typeset_in_index_long[inflection]

            parent_sort_as_short = parent.sort_as_short[inflection]
            parent_typeset_in_index_short \
                = parent.typeset_in_index_short[inflection]
            
            yield '\indexentry{' \
                  '%(parent_sort_as_long)s@%(parent_typeset_in_index_long)s!' \
                  '%(sort_as_long)s@%(typeset_in_index_long)s' \
                  '%(typeset_page_number)s}{%(page)s}' % locals()
            
            yield '\indexentry{' \
                  '%(parent_sort_as_short)s@%(parent_typeset_in_index_short)s!' \
                  '%(sort_as_short)s@%(typeset_in_index_short)s' \
                  '|see{---, %(typeset_in_index_long)s}}' \
                  '{0}' % locals()
            
        else:
            yield '\indexentry{' \
                  '%(sort_as_long)s@%(typeset_in_index_long)s' \
                  '%(typeset_page_number)s}' \
                  '{%(page)s}' % locals()
            
            yield '\indexentry{%(sort_as_short)s@' \
                  '%(typeset_in_index_short)s|see{%(typeset_in_index_long)s}}' \
                  '{0}' % locals()
            
    def generate_internal_macros(self, inflection):
        type_name = self.get_entry_type()
        reference = self.reference[inflection]
        typeset_in_text_short = self.typeset_in_text_short[inflection]
        typeset_in_text_full = self.typeset_in_text_long[inflection]
        
        yield '\\new%(type_name)s{%(reference)s}{%(typeset_in_text_short)s}' \
              '{%(typeset_in_text_full)s}' \
              % locals()

        if self.use_short_reference and self.reference_short[inflection]:
            reference = self.reference_short[inflection]
            
            yield '\\new%(type_name)s{%(reference)s}' \
                  '{%(typeset_in_text_short)s}' \
                  '{%(typeset_in_text_full)s}' \
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
        
    def _setup(self, concept, full_form, meta, indent_level):
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
            ('reference_short', 'reference_short'),
            ('sort_as_short', 'reference'),
            ('typeset_in_text_short', 'typeset'),
            ('typeset_in_index_short', 'typeset'),
            ('sort_as_long', 'sort_as_long'),
            ('typeset_in_text_long', 'typeset_long'),
            ('typeset_in_index_long', 'typeset_long'),
            ]
        
        if indent_level == 0:
            # Main entry.
            if not full_form:
                raise MissingAcronymExpansionError(concept)
                    
            reference, typeset = self.format_reference_and_typeset(concept)
            reference_short = [] # Only used for sub-entries.
            
            sort_as_long, typeset_long \
                = self.format_reference_and_typeset(full_form) 
            
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
                sort_as_long, typeset_long = \
                    self.get_complement_inflections(sort_as_long, typeset_long,
                                                    current_inflection)
            for field, variable in field_variable_map:
                value = ' '.join(locals()[variable])
                getattr(self, field)[complement_inflection] = value
                
        else:
            # Sub-entry.
            if full_form is None:
                full_form = concept
                
            for inflection in (current_inflection, complement_inflection):
                for field, value \
                    in self.expand_sub_entry(concept, inflection,
                                             current_inflection,
                                             field_variable_map,
                                             full_form).items():
                    value = self.unescape(value.strip(), FIELD_SEPARATORS + '-')
                    getattr(self, field)[inflection] = value
                    
        if current_inflection == Entry.INFLECTION_NONE:
            for (inflection, attribute) in cartesian(
                (Entry.INFLECTION_SINGULAR, Entry.INFLECTION_PLURAL, ),
                [field for field, variable in field_variable_map]):
                getattr(self, attribute)[inflection] = \
                    getattr(self, attribute)[Entry.INFLECTION_NONE]
