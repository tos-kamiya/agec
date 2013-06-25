[![Build Status](https://secure.travis-ci.org/tos-kamiya/agec.png?branch=master)](http://travis-ci.org/tos-kamiya/agec)

# agec

Agec, an arbitrary-granularity execution clone detection tool

Agec generates all possible execution sequences from Java byte code(s)
to detect the same execution sub-sequences from the distinct places in source files.

## Usage

Agec's core programs are:

**gen_ngram.py**. Generates n-grams of execution sequences of Java program.

**det_clone.py**. Identifies the same n-grams and reports them as code clones.

Agec also includes the following utilities:

**tosl_clone.py**. Converts locations of code clones (from byte-code index) to line numbers of source files.

**exp_clone.py**. Calculates some metrics from each code clone.

**run_disasy.py**. Disassembles a jar file (with 'javap' disassembler) and generate disassemble-result files.

### gen_ngram.py

gen_ngram.py reads given (disassembled) Java byte-code files, 
generates n-grams of method invocations from them and outputs n-grams to the standard output.

usage: gen_ngram.py asmdir -n size

Here, 'asmdir' is a directory which contains the disassemble result files (*.asm).
'size' is a length of each n-gram (default value is 6).

Note that a disassemble file need to be generated from *.class file with a command
'javap -c -p -l -constants', because gen_ngram.py requires a line number of each byte code.

### det_clone.py

det_clone.py reads a n-gram file, identifies the same n-grams, 
and outputs them as code clones to the standard output.

usage: det_clone.py ngramfile

Here, 'ngramfile' is a n-gram file, which has been generated with gen_ngram.py.

Each location in the result is shown in byte-code index.
In order to convert locations to line numbers of source files, use tosl_clone.py.

### tosl_clone.py

tosl_clone.py reads Java byte-code files and a code-clone detection result, 
converts each location of code clone into line number, 
and ouptuts the converted code-clone data to the standard output.

usage: tosl_clone.py asmdir cloneindex

Here, 'asmdir' is a directory containing disassembled result files and
'cloneindex' is the code-clone detection result that has been generated with
det_clone.py.

## A Small Example

This sample is to detect code clones from a Java file: ShowWeekday.java.

```bash
$ javac ShowWeekday.java
$ javap -c -p -l -constants ShowWeekday > disasm/ShowWeekday.asm
$ gen_ngram.py disasm > ngrams.txt
$ det_clone.py ngrams.txt > clone-indices.txt
$ tosl_clone.py clone-indices.txt > clone-linenums.txt
```

## Publish

* Toshihiro Kamiya, "Agec: An Execution-Semantic Clone Detection Tool," Proc. IEEE ICPC 2013, pp. 227-229 [link to the paper](http://toshihirokamiya.com/docs/p227-kamiya.pdf).

## License

Agec is distributed under [MIT License](http://opensource.org/licenses/mit-license.php).



