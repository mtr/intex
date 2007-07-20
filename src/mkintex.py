#! /usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
from __future__ import with_statement
"""
Copyright (C) 2007 by Martin Thorsen Ranang
"""
__version__ = "@VERSION@"
__author__ = "Martin Thorsen Ranang <mtr@ranang.org>"

from contextlib import nested
from itertools import count, imap

import logging
import optparse
import os
import re
import sys

from intex.config import INTEX_DEFAULT_INDEX, INTEX_INPUT_EXT, INTEX_OUTPUT_EXT

from intex.index import Index
        
def parse_command_line(command_line_options, usage):
    """Parse the command line according to the possible
    COMMAND_LINE_OPTIONS.
    """
    parser = optparse.OptionParser(usage=usage,
                                   version='%%prog %s' % (__version__))
    for option, description in command_line_options:
        parser.add_option(*option, **description)
        
    # Parse the command line.
    return parser.parse_args()

def resolve_auxiliary_and_args(args):
    """Resolve the name of the current LaTeX auxiliary file (.aux)
    based on the supplied arguments and the current working directory.
    """
    aux_re = re.compile('^.*\.aux$', re.IGNORECASE)
    auxiliary = [arg for arg in args
                 if aux_re.match(arg) and os.path.exists(arg)]
    args = [arg for arg in args if arg not in auxiliary]

    attempts = count(-2)
    
    while attempts.next():
        if len(auxiliary) > 1:
            logging.error('Please explicitly specify the ' \
                          'LaTeX auxiliary (.aux) file to use.')
            sys.exit(1)
            
        elif not auxiliary:
            auxiliary = ['%s.aux' % (arg) for arg in args
                         if os.path.exists('%s.aux' % (arg))]
            args = [arg for arg in args if '%s.aux' % (arg) not in auxiliary]
            
        else:
            auxiliary = auxiliary[0]
            break
        
    return auxiliary, args

        
def main():
    """Module mainline (for standalone execution).
    """
    command_line_options = [
        (['-D', '--debug'],
         {'dest': 'debug',
          'default': False,
          'action': 'store_true',
          'help': 'whether or not to output debug information'}),
        (['-V', '--verbose'],
         {'dest': 'verbose',
          'default': False,
          'action': 'store_true',
          'help': 'whether or not to output verbose information'}),
        (['-I', '--only-build-index'],
         {'dest': 'only_build_index',
          'default': False,
          'action': 'store_true',
          'help': 'only build the internal model of the index'}),
        (['-O', '--ito-file'],
         {'dest': 'ito_filename',
          'default': None,
          'metavar': 'FILE',
          'help': 'output the new internal InTeX information to FILE ' \
          '(default: %default)'}),
        (['-o', '--index-file'],
         {'dest': 'index_filename',
          'default': None,
          'metavar': 'FILE',
          'help': 'output the new indexing information to FILE ' \
          '(default: %default)'}),
        (['-a', '--acrodef-output'],
         {'dest': 'acrodef_output',
          'default': None,
          'metavar': 'FILE',
          'help': 'output acronym definitions to FILE ' \
          '(default: %default)'}),
        (['-p', '--persondef-output'],
         {'dest': 'persondef_output',
          'default': None,
          'metavar': 'FILE',
          'help': 'output (person) name definitions to FILE ' \
          '(default: %default)'}),
        ]

    # Parse the command line options.
    options, args = parse_command_line(command_line_options,
                                       usage='%prog [options] ' \
                                       '<index> [index ...]',)
    
    # Sort out the name for the basic log.
    logging.root.name = os.path.basename(__file__)

    log_level = None
    
    if options.verbose:
        log_level = logging.INFO
    if options.debug:
        log_level = logging.DEBUG
        
    # Configure the logging module.
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s',
                        level=log_level)
    
    auxiliary, args = resolve_auxiliary_and_args(args)
    if not auxiliary:
        logging.warning('No LaTeX auxiliary file specified; exiting.')
        sys.exit(1)

    if len(args) == 0:
        suffix_re = re.compile('^.*\.%s$' % (INTEX_INPUT_EXT))
        
        filenames = [filename
                     for filename in os.listdir(os.getcwd())
                     if suffix_re.match(filename)]
    else:
        filenames = args

    # If no ITO file was explicitly stated, deduce the implied name.
    if options.ito_filename is None:
        options.ito_filename = (os.path.splitext(auxiliary)[0] \
                                + os.path.extsep + 'ito')
        
    for filename in filenames:
        if not os.path.exists(filename):
            logging.error('Input file "%s" not found', filename)
            sys.exit(1)

    if options.verbose:
        logging.info('Will use LaTeX auxiliary file: "%s"', auxiliary)
        logging.info('Will use InTeX input files: %s',
                     ', '.join(imap('"%s"'.__mod__, filenames)))
        
    # Instatiate one Index object per file specified on the command
    # line.
    logging.info('Generating index...')
    indices = [Index.from_file(filename) for filename in filenames]
    
    # Generate all reference indices. 
    for index in indices:
        index.generate_reference_index()
        
    logging.info('... done (index generated).')
    
    if options.debug:
        for index in indices:
            logging.debug('\n%s', index)
            
    if options.only_build_index:
        return

    with nested(open(options.ito_filename, 'w'),
                open(options.index_filename, 'w')) \
        as (internal_file, index_file):
        not_found = index.interpret_auxiliary(auxiliary, internal_file,
                                              index_file)

    for reference, page in not_found:
        logging.warn('On page %s, reference to "%s" was not found '
                     'in the index.', page, reference)
    
if __name__ == "__main__":
    main()
