[![Build Status](https://secure.travis-ci.org/tos-kamiya/agec.png?branch=master)](http://travis-ci.org/tos-kamiya/agec)

agec
====

Agec, an arbitrary-granularity execution clone detection tool

Agec generates all possible execution sequences from Java bytecode(s)
to detect the same execution sub-sequences from the distinct places in source files.

## Usage

Agec's core programs are: 

**gen_ngram.py**, which generates n-grams of execution sequences of Java program.

**det_clone.py**, which identifies the same n-grams and reports them as code clones.

Agec also includes the following utilities:

**tosl_clone.py**, which converts locations of code clones (from byte-code index) to line numbers of source files.

**exp_clone.py**, which calculates some metrics from each code clone.

**run_disasy.py**, which disassembles a jar file (with 'javap' disassembler) and generate disassemble-result files.

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


