InTeX for LaTeX
===============

About
-----

InTeX is a package that adds functionality to LaTeX that eases
typesetting and indexing of phrases, acronyms, and proper names in a
consistent manner throughout documents of arbitrary length.

`mkintex(1)` is a preprocessor that interprets index entries specified
in `.itx` files and generates appropriate entries for LaTeX and `makeindex(1)`.


Installation
------------

From source:

    $ git clone https://github.com/mtr/intex.git
    $ cd intex
    $ automake --add-missing
    $ autoconf
    $ configure
    $ make
    
Create a deb package:
    
    $ make deb
    
Install deb package:

    $ dpkg --install dist/intex_1.8.0-1_all.deb

Or, you may also install directly from source:

	$ make install  # might need a sudo


For furhter information about how to install this package, please consult the
file INSTALL, located in the top directory of the package.


Usage
-----

The `mkintex(1)` command takes the following options:

       --version
              show program's version number and exit

       -h, --help
              show this help message and exit

       -D, --debug
              whether or not to output debug information

       -V, --verbose
              whether or not to output verbose information

       -I, --only-build-index
              only build the internal model of the index

       -O <file>, --ito-file=<file>
              output  the  new  internal InTeX information to <file> (default:
              none)

       -o <file>, --index-file=<file>
              output the new indexing information to <file> (default: none)

       -a <file>, --acrodef-output=<file>
              output acronym definitions to <file> (default: none)

       -p <file>, --persondef-output=<file>
              output (person) name definitions to <file> (default: none)

Examples
--------

Let us assume that you have already written a `latex(1)` document,
named `<document_name>.tex`, that uses the `InTeX(5)` package.
Furthermore, we assume that you have defined a set of concepts,
acronyms, and proper nouns for indexing in a file named
`<document_name>.itx`.  Then, to run this program the standard way,
first process the document with `latex(1)` (or `pdflatex(1)`) by
issuing the command

    latex <document_name>

This will process the document once and generate both a DVI file
(`<document_name>.dvi`)---or a PDF file (`<document_name>.pdf`)---and
an auxiliary file (`<document_name>.aux`).

Next, run the `mkintex(1)` program

    mkintex <document_name> --index-file=<document_name>.rix

that will use as input both `<document_name>.aux` and
`<document_name>.itx` to produce two new output files. The first file
is `<document_name>.ito`, which will be used by `latex(1)` in
following compilations of `<document_name>.tex`, and
`<document_name>.rix`, which will be used by `makeindex(1)` to produce
a proper index for LaTeX to typeset:

    makeindex -o intex.rid intex.rix

After  that, we have to run `latex(1)` again to generate a version of the
document with the defined concepts, acronyms, and proper names properly
typeset and indexed:

    latex <document_name>

Please note that in the examples above, `<document_name>` is the name
of the main LaTeX document, without the `.tex` ending.

For more information and examples of how to use the `InTeX(5)`
`LaTeX(1)` package, please see the file
[latex/intex.pdf](https://github.com/mtr/intex/blob/master/latex/intex.pdf?raw=true).

You may also consult the `mkintex(1)` man page.


Licensing
---------

For information about this package's license, please see the file
COPYING in the top directory of the package.


-- Martin Thorsen Ranang, 2013-03-12
