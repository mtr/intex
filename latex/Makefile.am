doc_root = intex
dtx_src = $(doc_root).dtx
internal = $(doc_root).rix
index = $(doc_root).rid

mkintex = ../src/mkintex.py
flags = --debug --index-file=$(internal)

pdf: 
	pdflatex $(dtx_src)
	PYTHONPATH=../lib python $(mkintex) $(flags) $(doc_root) 
	makeindex $(doc_root)
	makeindex -o $(index) $(internal)
	pdflatex $(dtx_src)

all: pdf
