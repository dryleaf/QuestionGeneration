#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Josimar H. Lopes,
# Master of EEIE, NUT


from subprocess import Popen, PIPE

import os
import sys
import tempfile
import nltk


class StanfordParserPT:
    """Class to interface with the Stanford Parser, for compatibility with Portuguese"""

    def __init__(self, encoding=None, verbose=False):
        self.__sentence = ""
        if len(sys.argv) <= 1:
            self.__sentence = raw_input("$ ")
        elif not os.path.isfile(sys.argv[1]):
            raise IOError("Oops! Try Again! File %s not found" % sys.argv[1])
        else:
            self.fileName = sys.argv[1]

        path = os.getcwd()

        path_to_jar = path + "/stanford-parser-2010-11-30/stanford-parser.jar"
        path_to_model = path + "/stanford-parser-2010-11-30/cintil.ser.gz"

        if not os.path.isfile(path_to_jar):
            raise IOError("Oops! JAR file %s not found" % path_to_jar)

        if not os.path.isfile(path_to_model):
            raise IOError("Oops! Model file not found: %s" % path_to_model)

        self._stanfordparser_jar = path_to_jar
        self._stanfordparser_model = path_to_model
        self._encoding = encoding
        self._verbose = verbose
        self._treeBanks = []
        self._inputSent = []
        self.tokenize()

    def tokenize(self):

        sentWords = []

        if self.__sentence == "":
            fsents = open(self.fileName)
            sentences = ''.join(''.join(k) for k in fsents.readlines())
            fsents.close()
        else:
            sentences = self.__sentence
        self._inputSent = sentences
        # print "sentences :: ", sentences

        pTok = Popen(["Tokenizer/run-Tokenizer.sh"], stdin=PIPE, stdout=PIPE)
        tokSents, stderr = pTok.communicate(sentences)

        sentWords.append(tokSents.replace("*/", "").replace("\*", "").replace("\n\n", "\n").strip())
        # print "i :: \n", sentWords

        # return self.batch_parse([sentWords])
        self.batch_parse([sentWords])

    def batch_parse(self, sentences):

        encoding = self._encoding
        java_options = '-Xmx500m'

        # Create a temporary input file
        _input_fh, _input_file_path = tempfile.mkstemp(text=True)

        # Build the java command to run the parser
        _stanfordparser_cmd = ['java',
                               java_options,
                               '-cp',
                               self._stanfordparser_jar,
            'edu.stanford.nlp.parser.lexparser.LexicalizedParser',
            '-tokenized',
            '-sentences','newline',
            '-outputFormat', 'oneline',
            '-uwModel', 'edu.stanford.nlp.parser.lexparser.BaseUnknownWordModel',
            self._stanfordparser_model,
            _input_file_path
            ]

        # Write the actual sentences to the temporary input file
        _input_fh = os.fdopen(_input_fh, 'w')
        _input = ''.join('\n'.join(x) for x in sentences)  # + '\n'

        if isinstance(_input, unicode) and encoding:
            _input = _input.encode(encoding)

        # print "\ninput :: \n", _input
        _input_fh.write(_input)
        _input_fh.close()

        # Run the parser and get the output
        # print "stdout:: ", tempfile.
        process = Popen(_stanfordparser_cmd, stdout=PIPE, stderr=PIPE)
        stanfordparser_output, stderr = process.communicate()

        if self._verbose:
            verbose = stderr.decode(encoding).strip().split("\n")
            print "%s\n%s" % (verbose[0], verbose[-1])
        if encoding:
            stanfordparser_output = stanfordparser_output.decode(encoding)

        self._treeBanks = stanfordparser_output.replace("(PNT ,)", "(, ,)").replace("(PNT .)", "(. .)")

        # Delete the temporary file
        os.unlink(_input_file_path)

        # Output the parse trees
        parse_trees = []
        treeFile = ""

        try:
            treeFile = open("pennTreeBanks.txt", "w")
            for string_tree in stanfordparser_output.strip().split("\n"):
                # print "string :: ", string_tree.encode(encoding)
                # parse_trees.append(nltk.Tree.fromstring(string_tree.replace("(ROOT", "")[:-1]))
                parse_trees.append(nltk.Tree.fromstring(string_tree.replace("(PNT ,)", "(, ,)").replace("(PNT .)", "(. .)")))
                print >> treeFile, string_tree.encode(encoding).replace("(PNT ,)", "(, ,)").replace("(PNT .)", "(. .)")
        except IOError, message:
            print >> sys.stderr, "File could not be opened: ", message
        finally:
            treeFile.close()
        # return parse_trees

    def getTreeBanks(self):
        """Returns the tree banks"""
        return self._treeBanks

    def getSentences(self):
        """Returns the input sentences"""
        return self._inputSent

if __name__ == '__main__':

    parser = StanfordParserPT(encoding="utf-8")
    tree = parser.tokenize()
    # for t in tree:
    #    print t, '\n'
    #    t.draw()
