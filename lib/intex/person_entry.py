#! /usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
"""
Copyright (C) 2007, 2008 by Martin Thorsen Ranang

This file is part of InTeX.

InTeX is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your
option) any later version.

InTeX is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License
along with InTeX.  If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = "Martin Thorsen Ranang <mtr@ranang.org>"
__revision__ = "$Rev$"
__version__ = "@VERSION@"

from utils import escape_aware_split
from entry import Entry


class PersonEntry(Entry):
    _generated_fields = [
        # The values of REFERENCE are how this entry will be referred
        # to in the text (\co{<reference>}).
        'reference',
        'reference_short',
        # The values of TYPESET_IN_TEXT determines how the entry will
        # be typeset in the text.  If it was referred to in its plural
        # form, the entry typeset will also be typeset with plural
        # inflection.
        'typeset_in_text_first',
        'typeset_in_text_last',
        # The values of TYPESET_IN_INDEX defines how the entry will be
        # typeset in the index.
        'typeset_in_index',
        ]
    
    # Different constants used for output formatting.
    _label_width = len('typeset_in_text_first')
    _column_width = 40
    _line_format = '%(_bold_on)s%%%(_label_width)ds%(_bold_off)s ' \
                   '%%-%(_column_width)ds'
    
    def __init__(self, index, parent, initials=None, name=None,
                 index_as=None, sort_as=None, meta=None, alias=None,
                 **rest):
        
        for attribute in self._generated_fields:
            setattr(self, attribute, dict.fromkeys([Entry.INFLECTION_NONE,]))
            
        Entry.__init__(self, index, parent, meta)

        # If this entry is an alias for another entry, indicate that
        # here.
        self.alias = alias

        names = escape_aware_split(name, ',')
        
        if len(names) > 1:
            last_name, first_name = names
        else:
            last_name, first_name = names[0], ''

        # Remove any preceding commas (',') and surrounding
        # whitespace.
        first_name = first_name.lstrip(',').strip()
        
        field_variable_map = [
            ('reference', 'reference'),
            ('typeset_in_text_first', 'first_name'),
            ('typeset_in_text_last', 'last_name'),
            ('typeset_in_index', 'typeset_formal'),]

        # Prepare the different local variables.
        reference = initials

        if first_name:
            typeset_formal = '%s, %s' % (last_name, first_name)
        else:
            typeset_formal = last_name

        for particle in ['the', 'von', 'van', 'van der']:
            if first_name.endswith(particle):
                last_name = ' '.join([first_name[-len(particle):], last_name])
                first_name = first_name[:-len(particle)]
                break          # Will avoid the following else-clause.
            
        variables = locals()
        
        for field, variable in field_variable_map:
            getattr(self, field)[Entry.INFLECTION_NONE] = variables[variable]

        self.index_inflection = Entry.INFLECTION_NONE
        
    def get_plain_header(self):
        return self._line_format \
               % ('', self.bold_it('value'.center(self._column_width)))

    def __str__(self):
        if self.alias:
            alias_line = '\n' + self._line_format % ('alias', self.alias, )
        else:
            alias_line = ''
            
        return '\n'.join([self._line_format \
                          % (attribute,
                             getattr(self, attribute)['none'],
                             )
                          for attribute in self._generated_fields]) \
                + alias_line

    def generate_index_entries(self, page, typeset_page_number=''):
        inflection = self.index_inflection

        typeset_in_index = self.typeset_in_index[inflection]
        sort_as = typeset_in_index
        
        # If this is an alias entry, the index entries are affected.
        # Generate the index entries accordingly.
        if self.alias:
            concept, _inflection = self.index.references[self.alias]
            for entry in concept.generate_index_entries(page,
                                                        typeset_page_number):
                yield entry
                
            return                   # Skip the regular index entries.
        
        yield '\indexentry{%(sort_as)s@%(typeset_in_index)s' \
              '%(typeset_page_number)s}{%(page)s}' \
              % locals()

    def generate_internal_macros(self, inflection):
        type_name = self.get_entry_type()
        reference = self.reference[inflection]
        typeset_in_text_first = self.typeset_in_text_first[inflection]
        typeset_in_text_last = self.typeset_in_text_last[inflection]
        
        yield '\\new%(type_name)s{%(reference)s}' \
              '{%(typeset_in_text_first)s}' \
              '{%(typeset_in_text_last)s}' \
              % locals()
        
        if self.use_short_reference and self.reference_short[inflection]:
            reference = self.reference_short[inflection]
            
            yield '\\new%(type_name)s{%(reference)s}{%(typeset_in_text)s}' \
                  '{XC.1}' \
                  % locals()
