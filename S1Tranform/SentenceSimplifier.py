#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Josimar H. Lopes,
# Master of EEIE, NUT


from subprocess import Popen, PIPE

import os
import re
import itertools
import sys
import nltk
import tempfile
from nltk.tree import ParentedTree
# adds the parent directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from S1Tranform import StanfordParserPT


class SentenceSimplifier:
    """Class to Get Penn Tree[Banks and Apply TRegex/TSurgeon and extract simplified sentences"""

    def __init__(self, encoding=None):

        self.__encoding = encoding
        path_to_treeBanks = "pennTreeBanks.txt"
        path_to_jar = "stanford-tregex-2015-04-20/stanford-tregex.jar"

        if not os.path.isfile(path_to_jar):
            raise IOError("Could not locate:: file %s not found" % path_to_jar)

        if not os.path.isfile(path_to_treeBanks):
            raise IOError("Could not locate:: file %s not found" % path_to_treeBanks)

        self.__stanfordtregex_jar = path_to_jar
        # self.__treeBanks = path_to_treeBanks
        self.__treeBanks, self.__treeBanks_path = tempfile.mkstemp(text=True)
        self.__unmvFlag = False
        self.__unmvTreeBanks = ""
        self.__answerFlag = False
        self.__answerTreeBanks = ""
        self.__numOfAnsPhrases = []
        self.__markedTreeBanks = []
        # self.__treeListOpr = []

    def setTreeBanks(self, treeBanks):

        self.__treeBanks = os.fdopen(self.__treeBanks, 'w')
        _input = ''.join('\n'.join(x) for x in treeBanks)

        if self.__encoding:
            _input = _input.encode(self.__encoding)
        self.__treeBanks.write(_input)
        self.__treeBanks.close()

        return self.markPossibleAnswerPhrases()

    def getTreeBanks(self):

        return self.__answerTreeBanks

    def getNumOfAnswers(self):

        return self.__numOfAnsPhrases

    def markUnmovablePhrases(self):
        """Method used to mark unmovable phrases."""

        tregex = ("NP $ VP << PP=unmv",
                "CP=unmv [ !> VP | $-- /,/ | < ADV ] & [!<, (C $.. S)]",
                "CP <, C < (S < (NP = unmv !$,, VP) | < (VP < NP=unmv))",
                "(/.*/ <, CONJ | <,(CONJ' < CONJ)) $--(NP|PP|VP=unmv) | <-(NP|PP|VP=unmv)",
                # "(/.*/ <, CONJ | <,(CONJ' < CONJ)) $--(NP|PP|N'|N|A|A'|VP|ADV'=unmv) | <-(NP|PP|N'|N|A|A'|VP|ADV'=unmv)"#
                "VP << (S=unmv $,, /,/)",
                # "S < PP|AP|ADVP=unmv"#,
                # "CONJP <, CONJ << NP|VP|ADVP|PP=unmv"#,
                "PP << PP=unmv",
                "VP|V' <+(VP|V') (V $ (NP=unmv < CL))"
                # "(/.*/ <, CONJ) $--(NP|PP|N'|N|A|VP=unmv) | <-(NP|PP|N'|N|A|VP=unmv)"#,
                # "S < (VP <+(VP) (V < é|era) << (VP|AP|PP|ADVP=unmv))"
                  )

        tsurgeon = "relabel unmv /^(.*)$/UNMOVABLE-$1/"

        self.runTSurgeonScript(tregex, tsurgeon)

    def propagateUnmvConstraint(self):

        self.__unmvFlag = True
        tregex = ("NP|PP|AP|ADVP|CP << NP|AP|ADVP|VP|N'|CP=unmv",
                  "@UNMOVABLE << NP|ADJP|VP|ADVP|PP|CONJP|AP|CP=unmv")
        tsurgeon = "relabel unmv /^(.*)$/UNMOVABLE-$1/"

        self.__treeBanks, self.__treeBanks_path = tempfile.mkstemp(text=True)
        self.__treeBanks = os.fdopen(self.__treeBanks, 'w')
        _input = ''.join('\n'.join(x) for x in self.__markedTreeBanks)

        # print "-treeFile:: ", self.__treeBanks_path

        if isinstance(_input, unicode) and self.__encoding:
            _input = _input.encode(self.__encoding)

        self.__treeBanks.write(_input)
        self.__treeBanks.close()

        self.runTSurgeonScript(tregex, tsurgeon)

    def markPossibleAnswerPhrases(self):
        """Method used to mark possible answer phrases"""

        self.markUnmovablePhrases()
        self.propagateUnmvConstraint() #NOW
        self.__answerFlag = True

        tregex = ("S < (NP|CP=ans $+ /,/ !$++ NP|CP)", "NP|PP=ans", "CP=ans !>> CP <, (C <: que) < (S < UNMOVABLE-NP|UNMOVABLE-VP|V|V')")
        tsurgeon = "relabel ans /^(.*)$/$1-ANS/"

        self.__treeBanks, self.__treeBanks_path = tempfile.mkstemp(text=True)
        self.__treeBanks = os.fdopen(self.__treeBanks, 'w')
        _input = ''.join('\n'.join(x) for x in self.__markedTreeBanks)

        # print "-treeFile:: ", self.__treeBanks_path

        if isinstance(_input, unicode) and self.__encoding:
            _input = _input.encode(self.__encoding)

        self.__treeBanks.write(_input)
        self.__treeBanks.close()

        self.runTSurgeonScript(tregex, tsurgeon) #NOW

        n = len(self.__answerTreeBanks)
        _tree = []

        for i in range(n):
            cnt = itertools.count()
            trees = self.__answerTreeBanks[i]
            # print "Original :: ", self.__answerTreeBanks[i]
            trees = re.sub(r'-ANS', lambda x: '-{}'.format(next(cnt)), trees)
            self.__answerTreeBanks[i] = trees
            self.__numOfAnsPhrases.append([])
            self.__numOfAnsPhrases[i] = next(cnt)
            # print i, "AP= ", self.__numOfAnsPhrases[i], " .:", self.__answerTreeBanks[i]
            _tree.append(nltk.Tree.fromstring(trees.decode(self.__encoding)))

        return _tree

    def runTSurgeonScript(self, tregex, tsurgeon):
        """Function that executes the TSurgeon expression and returns a result."""

        _input = ""
        #_tree = []
        self.__markedTreeBanks = []
        _tsurgeon = tsurgeon

        for _tregex in tregex:
            # self.__treeListOpr = []
            # temp = []
            # print "tr:: ", _tregex
            # print "ts:: ", _tsurgeon
            _CMD_TREGEX = ['java', '-mx100m', '-cp',
                                 self.__stanfordtregex_jar,
                          'edu.stanford.nlp.trees.tregex.tsurgeon.Tsurgeon',
                          '-s', '-treeFile',
                          self.__treeBanks_path,
                          '-po',
                          _tregex, _tsurgeon]

            process = Popen(_CMD_TREGEX, stdin=PIPE, stdout=PIPE)
            extractedSents, stderr = process.communicate()

            if self.__encoding:
                extractedSents = extractedSents.decode(self.__encoding)

            # Delete temporary file
            os.unlink(self.__treeBanks_path)

            self.__treeBanks, self.__treeBanks_path = tempfile.mkstemp(text=True)
            self.__treeBanks = os.fdopen(self.__treeBanks, 'w')
            _input = ''.join('\n'.join(x) for x in extractedSents)

            if isinstance(_input, unicode) and self.__encoding:
                _input = _input.encode(self.__encoding)

            self.__treeBanks.write(_input)
            self.__treeBanks.close()

            # for scriptTree in extractedSents.strip().split("\n"):
            #    scriptTree.encode(self.__encoding)
            #    print "scriptTree:: ", scriptTree
            #    temp.append(nltk.Tree.fromstring(scriptTree))
                # self.__treeListOpr.append(ParentedTree.fromstring(scriptTree))
            #_tree = temp

        self.__markedTreeBanks.append(_input.strip().split("\n"))
        if self.__unmvFlag:
            self.__unmvTreeBanks = _input.strip().split("\n")
            self.__unmvFlag = False
        elif self.__answerFlag:
            self.__answerTreeBanks = _input.strip().split("\n")
            self.__answerFlag = False
        # print "Marked:: ", self.__markedTreeBanks
        # return _tree

if __name__ == '__main__':

    parser = StanfordParserPT.StanfordParserPT(encoding="utf-8")
    treeBanks = parser.getTreeBanks()
    sent = SentenceSimplifier(encoding="utf-8")
    tree = sent.setTreeBanks(treeBanks)
    for t in tree:
        t.draw()
