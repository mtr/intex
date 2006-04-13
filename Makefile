# test: test.tex
# 	latex test
# 	./makeintex test *.intex -o test.rix -a acronyms.tex -p persons.tex
# 	makeindex test
# 	makeindex -o test.rid test.rix
# 	latex test

intex: intex.dtx intex.itx
	latex $@.dtx
	./makeintex $@ $@.itx --feedback=$@.ito --index-output=$@.rix --acrodef-output=acronyms.tex --persondef-output=persons.tex
	makeindex $@
	makeindex -o $@.rid $@.rix
	#latex $@.dtx
	#./makeintex $@ $@.itx -o $@.rix -a acronyms.tex -p persons.tex
	#makeindex $@
	#makeindex -o $@.rid $@.rix

all: intex