#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Josimar H. Lopes,
# Master of EEIE, NUT

from subprocess import Popen, PIPE
from nltk.tree import ParentedTree

import re
import os
import sys
import tempfile
import nltk_tgrep

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from S1Tranform import StanfordParserPT
from S1Tranform import SentenceSimplifier


class QuestionGenerator:
    """Class to generate candidate questions from a declarative sentefnce."""

    def __init__(self):
        """Initializes all the premises"""
        self.__refsent = []
        global stanfordparser
        stanfordparser = StanfordParserPT.StanfordParserPT(encoding="utf-8")

        global sentsimplifier
        sentsimplifier = SentenceSimplifier.SentenceSimplifier(encoding="utf-8")

        sentences = stanfordparser.getSentences()
        treeBanks = stanfordparser.getTreeBanks()
        self.begin(treeBanks, encoding="utf-8", sentences=sentences)


    def begin(self, treeBanks, encoding=None, sentences=None):

        self.__encoding = encoding
        path_to_cfg = "/usr/local/share/freeling/config/pt.cfg"

        if not os.path.isfile(path_to_cfg):
            raise IOError("Could not locate:: file %s not found" % path_to_cfg)

        self.__nec_pt_cfg = path_to_cfg
        self.__sentences, self.__sentences_path = tempfile.mkstemp(text=True)
        self.__sentences = os.fdopen(self.__sentences, 'w')
        _input = ''.join('\n'.join(x) for x in sentences)

        if isinstance(_input, unicode) and self.__encoding:
            _input = _input.encode(self.__encoding)
        self.__sentences.write(_input)
        self.__sentences.close()
        self.__sst = []

        # Trigger words to NER
        self.__twPER = open("NERtw/twPER.dat")
        self.__twLOC = open("NERtw/twLOC.dat")
        self.__twORG = open("NERtw/twORG.dat")

        self.annotateNER()
        print sentences
        for k in sentences.split('\n'):
            k = k.replace('.', ' .')
            self.__refsent.append(k.split(' '))
        self.setTreeBanks(treeBanks)

        sentsimplifier.setTreeBanks(treeBanks)  # tree = sentsimplifier.setTreeBanks(treeBanks)
        #for t in tree:
        #    t.draw()
        # generate questions
        self.generateQuestions()


    def annotateNER(self):

        CMD_ANALYZE = ['analyze', '-f', self.__nec_pt_cfg,
                       '--force', 'retok', '--nec']

        self.__sentences = open(self.__sentences_path)

        process = Popen(CMD_ANALYZE, stdin=self.__sentences, stdout=PIPE)
        extractedNEC, stderr = process.communicate()

        if self.__encoding:
            extractedNEC = extractedNEC.decode(self.__encoding).replace(". . Fp 1", "")

        self.__necStats = extractedNEC
        self.__sentences.close()
        os.unlink(self.__sentences_path)
        self.annotateSST()

    def annotateSST(self):

        i = 0
        _twPER = [w.strip() for w in self.__twPER.readlines()]
        _twLOC = [w.strip() for w in self.__twLOC.readlines()]
        _twORG = [w.strip() for w in self.__twORG.readlines()]

        for nec in self.__necStats.strip().split("\n\n"):

            self.__sst.append([])

            for line in nec.strip().split("\n"):
                line = line.split(' ')

                if "NP00SP0" in line:
                    if '_' in line[0]:
                        bi = True
                        for x in line[0].split('_'):
                            if bi:
                                self.__sst[i].append("B-" + x + ".PERSON")
                                bi = False
                            else:
                                self.__sst[i].append("I-" + x + ".PERSON")
                    else:
                        self.__sst[i].append("B-" + line[0] + ".PERSON")
                elif "NP00G00" in line:
                    if '_' in line[0]:
                        bi = True
                        for x in line[0].split('_'):
                            if bi:
                                self.__sst[i].append("B-" + x + ".LOCATION")
                                bi = False
                            else:
                                self.__sst[i].append("I-" + x + ".LOCATION")
                    else:
                        self.__sst[i].append("B-" + line[0] + ".LOCATION")
                elif "NP00O00" in line:
                    if '_' in line[0]:
                        bi = True
                        for x in line[0].split('_'):
                            if bi:
                                self.__sst[i].append("B-" + x + ".ORGANIZATION")
                                bi = False
                            else:
                                self.__sst[i].append("I-" + x + ".ORGANIZATION")
                    else:
                        self.__sst[i].append("B-" + line[0] + ".ORGANIZATION")
                elif "NP00V00" in line:
                    if '_' in line[0]:
                        bi = True
                        for x in line[0].split('_'):
                            if bi:
                                self.__sst[i].append("B-" + x + ".OTHER")
                                bi = False
                            else:
                                self.__sst[i].append("I-" + x + ".OTHER")
                    else:
                        self.__sst[i].append("B-" + line[0] + ".OTHER")
                elif line[2].startswith("V"):
                    self.__sst[i].append("B-" + line[1] + "." + line[2])
                elif bool(re.search(r'^PP[0-3][CMF][SP][0N]00$', line[2])):
                    self.__sst[i].append("B-" + line[2] + ".PRS")
                else:   # Trigger words condition to NER

                    if bool(line[0].encode(self.__encoding) in _twPER):
                        self.__sst[i].append("B." + line[0] + ".PERSON")
                    elif bool(line[0].encode(self.__encoding) in _twLOC):
                        self.__sst[i].append("B." + line[0] + ".LOCATION")
                    elif bool(line[0].encode(self.__encoding) in _twORG):
                        self.__sst[i].append("B." + line[0] + ".ORGANIZATION")
                    elif bool(re.search(r'^W$', line[2])):
                        # print "Line.:", line
                        self.__sst[i].append("B." + line[0] + ".TIME")
                    else:
                        self.__sst[i].append(line[2])
            self.__sst[i].append("0")
            i += 1
        print '\n'.join('[' + ', '.join(s) + ']' for s in self.__sst)
        # print "NER\n", self.__sst
        self.__twPER.close()
        self.__twLOC.close()
        self.__twORG.close()

    def search(self, word, text):
        """To search for word in File"""
        return bool(re.search(r'\b{}\b'.format(re.escape(word)), text))

    def setTreeBanks(self, treeBanks):
        """Set a reference to Original Tree Banks"""

        _trees = ''.join('\n'.join(x) for x in treeBanks)
        self.__treeBanks = _trees.splitlines()

        if isinstance(self.__treeBanks, unicode) and self.__encoding:
            self.__treeBanks = self.__treeBanks.encode(self.__encoding)

    def generateQuestions(self):
        """Generates questions according to its types"""

        trees = sentsimplifier.getTreeBanks()
        ap, tags, prep, sents, tags_sents, vp, vtags = self.extractAnswerPhrases(trees, r'^[NPC]P-[0-9]+')
        nAnswes = sentsimplifier.getNumOfAnswers()
        question = []
        qtags = []
        qp = []
        temp_vp = []
        temp_vtags = []
        issubj = False

        j = 0
        for aptree in trees:
            # Case 1: Answer Phrase in the Subject
            n = nAnswes[j] + 1
            question.append([])
            qtags.append([])
            qp.append([])
            temp_vp.append([])
            temp_vtags.append([])
            # issubj = False
            for i in range(n):
                qtype = ""
                if i != n-1:
                    m = self.contains(ap[j][i], sents[j])
                question[j].append(sents[j][:])
                qtags[j].append(tags_sents[j][:])
                temp_vp[j].append(vp[j][:])
                temp_vtags[j].append(vtags[j][:])
                # print m
                issubj = False
                if i != n-1:
                    if self.inSubject(aptree, i):
                        issubj = True
                    else:
                        issubj = False

                    isperson = bool(re.search(r'\.PERSON|\.PRS', ' '.join(self.__sst[j][m[0]:m[1]])))
                    isorg = bool(re.search(r'\.ORGANIZATION', ' '.join(self.__sst[j][m[0]:m[1]])))
                    isloc = bool(re.search(r'\.LOCATION', ' '.join(self.__sst[j][m[0]:m[1]])))
                    istime = bool(re.search(r'\.TIME', ' '.join(self.__sst[j][m[0]:m[1]])))
                    isqual = bool(re.search('B-ser\.V', ' '.join(self.__sst[j][:])))
                    flag_art = True if ' '.join(art for art in tags[j][i]).startswith(u'ART') else False
                    # print "PERSON = ", isperson, " ORG = ", isorg, " LOC = ", isloc, " TIME = ", istime, " To Be = ", isqual, " ART = ", flag_art

                    if isperson:
                        # print "PER"
                        # prepare 'Quem' question phrasek
                        if prep[j][i] == u'PP':
                            if tags[j][i][1] == u'V':
                                qtype = u'O que'
                            elif tags[j][i][1] == u'CL' and isqual and not flag_art:
                                qtype = u'Qual'
                            else:
                                qtype = ap[j][i][0] + u' quem'
                        elif prep[j][i] == u'CP':
                            qtype = u'O que'
                        else:
                            qtype = u'Quem'
                    elif isorg:
                        # print "ORG"
                        # prepare 'O que' or 'Qual' question phrase
                        # case 'Qual':
                        # if
                        if prep[j][i] == u'PP':
                            qtype = ap[j][i][0] + u' onde'
                        else:
                        # case 'O que':
                            qtype = u'O que'

                    elif isloc:
                        # print "LOC"
                        # case 'Onde':

                        if prep[j][i] == u'PP':
                            qtype = u'Onde'
                        # case 'Qual':
                        elif isqual and not flag_art:
                            qtype = u'Qual'
                        # case 'O que':
                        else:
                            qtype = u'O que'
                    elif istime:
                        # case 'Quando'
                        if prep[j][i] == u'PP':
                            qtype = u'Quando'
                        else:
                            qtype = u'O que'
                    else:
                        # case 'Quanto'
                        if prep[j][i] == u'NP':
                            if tags[j][i][0] == u'CARD':
                                if tags[j][i][1] == u'N':
                                    if u'NCMS000' in self.__sst[j][m[0]:m[1]] or u'NCMP000' in self.__sst[j][m[0]:m[1]]:
                                        qtype = u'Quantos ' + ap[j][i][1]
                                    elif u'NCFS000' in self.__sst[j][m[0]:m[1]] or u'NCFP000' in self.__sst[j][m[0]:m[1]]:
                                        qtype = u'Quantas ' + ap[j][i][1]
                                    else:
                                        qtype = u'Quantos'
                                else:
                                    qtype = u'Quantos'
                            elif isqual and not flag_art:
                                qtype = u'Qual'
                            else:
                                qtype = u'O que'
                        elif prep[j][i] == u'PP':
                            if u'CARD' in tags[j][i]:
                                if tags[j][i][-1] == u'N':
                                    qtype = ap[j][i][0] + u' que ' + ap[j][i][-1]
                                else:
                                    qtype = ap[j][i][0] + u' que'
                            else:
                                if tags[j][i][-1] == u'N':
                                    qtype = u'Quando'
                                else:
                                    qtype = ap[j][i][0] + u' que'
                        else:
                            qtype = u'O que'

                    if not issubj:
                        qtype = qtype.capitalize()
                        word = question[j][i][0]
                        if qtags[j][i][0] != u'N':
                            question[j][i][0] = word.lower()

                    qp[j].append(qtype)

                cnt = len(temp_vtags[j][i])
                prev = temp_vtags[j][i][0]
                value = temp_vp[j][i][0]
                for ind in range(1, cnt):
                    if prev == u'V' and temp_vtags[j][i][ind] == u'CL':
                        temp_vtags[j][i][ind-1] = temp_vtags[j][i][ind]
                        temp_vtags[j][i][ind] = prev
                        temp_vp[j][i][ind-1] = temp_vp[j][i][ind]
                        temp_vp[j][i][ind] = value
                    else:
                        prev = temp_vtags[j][i][ind]
                        value = temp_vp[j][i][ind]
                # print "Ordered:: ", temp_vp[j][i], " Unordered:: ", vp[j]
                # print "Ordered_t:: ", temp_vtags[j][i], " Unordered_t:: ", vtags[j]

                temp_qg = ' '.join(question[j][i])
                temp_tag = ' '.join(qtags[j][i])
                temp_qg = temp_qg.replace(' '.join(vp[j]), ' '.join(temp_vp[j][i]))
                # print "temp_qg::", temp_qg, ", vp.: ", ' '.join(vp[j]), " temp_vp.: ", ' '.join(temp_vp[j][i])
                temp_tag = temp_tag.replace(' '.join(vtags[j]), ' '.join(temp_vtags[j][i]))
                question[j][i] = temp_qg.split(' ')
                qtags[j][i] = temp_tag.split(' ')

                if i != n-1:
                    del question[j][i][m[0]:m[1]]
                    question[j][i].insert(m[0], qtype)
                question[j][i][-1] = u'?'

                if i != n-1:
                    del qtags[j][i][m[0]:m[1]]
                    qtags[j][i].insert(m[0], u'QP')

                    if not issubj:
                        print "CUR_Q.: ", question[j][i]
                        print "CUR_Q.: ", qtags[j][i]

                        vbindex = question[j][i].index(temp_vp[j][i][0])
                        vfindex = question[j][i].index(temp_vp[j][i][-1]) + 1
                        print "vbindex = ", vbindex, " vfindex = ", vfindex

                        qpindex = qtags[j][i].index(u'QP')
                        qptag = qtags[j][i][qpindex]
                        qpval = question[j][i][qpindex]
                        del qtags[j][i][qpindex]
                        del question[j][i][qpindex]


                        vtag = qtags[j][i][vbindex:vfindex]
                        qpverb = question[j][i][vbindex:vfindex]
                        # print "vtag.: ", vtag, " qpverb.: ", qpverb
                        del qtags[j][i][vbindex:vfindex]
                        del question[j][i][vbindex:vfindex]

                        vlen = len(vtag)
                        for b in range(vlen):
                            if vtag[b] == u'CL':
                                qpverb[b] = u''.join(qpverb[b])
                            qtags[j][i].insert(b, vtag[b])
                            question[j][i].insert(b, qpverb[b])

                        qtags[j][i].insert(0, qptag)
                        question[j][i].insert(0, qpval)
                if i == n-1:
                    word = question[j][i][0]
                    if qtags[j][i][0] != u'N':
                        question[j][i][0] = word.lower()
                    vtag = qtags[j][i][vbindex:vfindex]
                    qpverb = question[j][i][vbindex:vfindex]
                    # print "vtag.: ", vtag, " qpverb.: ", qpverb
                    del qtags[j][i][vbindex:vfindex]
                    del question[j][i][vbindex:vfindex]
                    vlen = len(vtag)
                    for b in range(vlen):
                        if vtag[b] == u'CL':
                            qpverb[b] = u''.join(qpverb[b])
                        qtags[j][i].insert(b, vtag[b])
                        question[j][i].insert(b, qpverb[b])
                    word = question[j][i][0]
                    question[j][i][0] = word.capitalize()

            j += 1

        print qp
        # print qtags
        print "\n++++++++++++++++Generated Questions+++++++++++++++"
        print '\n\n'.join('\n'.join('[' + ', '.join(ss) + ']' for ss in s) for s in question)
        # print question

    def contains(self, small, big):
        for i in xrange(len(big)-len(small)+1):
            for j in xrange(len(small)):
                if big[i+j] != small[j]:
                    break
            else:
                return i, i+len(small)
        return False

    def inSubject(self, inputTree, i):
        """Returns true or false"""
        pattern1 = r"^\(ROOT \(S \(NP-" + str(i)
        pattern2 = r"^\(ROOT \(S \(S \(NP-" + str(i)
        return bool(re.match(pattern1, inputTree) or re.match(pattern2, inputTree))

    def moveQuestionPhrase(self):
        """Replaces the Answer Phrase with the corresponding Question Phrase"""

    def subjectAuxiliaryInversion(self):
        """Performs subject-auxiliary inversion"""

    def verbConjugationAgreement(self):
        """Checks if the verb has been conjugated properly with respect to Question phrase insertion"""

    def generate(self):
        """Begins the generation process"""

    def extractAnswerPhrases(self, anstrees, pattern):
        """Extract answer phrases from sentences."""

        # prepositions, tags and answer phrases
        prep = []
        ap = []
        tags = []
        # sentences and tags
        sents = []
        tags_sents = []
        vp = []
        vtags = []

        index = 0
        for string in anstrees:
            n = len(string)
            flag_as = False
            flag_all = False
            level = 0
            b = 0
            savedlevel = 0
            ap.append([])
            prep.append([])
            tags.append([])
            vp.append([])
            vtags.append([])
            s = ""
            t = ""
            for i in range(n):
                if string[i] == '(':
                    level += 1
                    if not flag_as or not flag_all:
                        flag_as = bool(re.search(pattern, string[i+1:]))
                        flag_all = bool(re.search(r'\b[A-Z]+ \w+\b', string[i+1:].decode('utf8'), re.UNICODE))
                        if flag_as or flag_all:
                            b = i
                            savedlevel = level
                elif string[i] == ')':
                    # print "string2 ::", string[b:i+1]
                    # print "Flag: ", flag_as, "lev: ",  level, "slev: ", savedlevel
                    if flag_as and level == savedlevel:
                        # Still need to split this into Prep, tags and Answer Phrases
                        # 1 :- PREPOSITION
                        p1 = ''.join(re.findall(r'\b[NPC]P-[0-9]+\b', string[b:i+1].decode('utf8'), re.UNICODE))
                        prep[index].append(re.sub(r'-[0-9]+', '', p1))

                        # 2:- TAGS
                        t1 = ''.join(re.findall(r'\b[A-Z]+ \b', string[b:i+1].decode('utf8'), re.UNICODE))
                        # tags[index].append({cnt: t1.strip().split(' ')})
                        tags[index].append(t1.strip().split(' '))

                        # 3:- ANSWER PHRASES
                        ap1 = ','.join(re.findall(r'\b[A-Z]+ \w+[-\w]*\b', string[b:i+1].decode('utf8'), re.UNICODE))
                        # print "ap1 = ", ap1
                        # ap[index].append({cnt: re.sub(r'([A-Z]+ )', '', ap1).split(',')})
                        ap[index].append(re.sub(r'([A-Z]+ )', '', ap1).split(','))

                        # Sentence with tags
                        # 1:- SENTENCES
                        t_s = ','.join(re.findall(r'\b[A-Z]+ [-]?\w+[-\w]*\b', string[b:i+1].decode('utf8'), re.UNICODE))
                        s += ' '.join(re.sub(r'([A-Z]+ )', '', t_s).split(',')) + ' '

                        # 2:- TAGS
                        t += ''.join(t1.strip()) + ' '
                        # print "1. tags = ", t
                        flag_as = False

                    elif flag_all and level == savedlevel:
                        # Sentence with tags
                        # 1:- SENTENCES
                        t_s = ','.join(re.findall(r'\b[A-Z]+ [-]?\w+[-\w]*\b', string[b:i+1].decode('utf8'), re.UNICODE))
                        s += ' '.join(re.sub(r'([A-Z]+ )', '', t_s).split(',')) + ' '

                        # 2:- TAGS
                        t1 = ''.join(re.findall(r'([A-Z]+ )', string[b:i+1].decode('utf8'), re.UNICODE))
                        t += ''.join(t1.strip()) + ' '

                        # print "2.tags = ", t
                        flag_all = False
                    level -= 1

            s += '.'
            t += 'PNT'
            # print "sentence = ", s.split(' ')
            sents.append(s.split(' '))
            tags_sents.append(t.split(' '))

            yj = 0
            s = s.split(' ')
            t = t.split(' ')
            aplen = len(ap[index])
            prev = ""
            for x in ap[index]:
                xi = len(x)
                i = 0
                for y in range(yj, len(s)):
                    # prev = t[y]
                    if x[i] == s[y]:
                        yj += 1
                        if aplen != 1:
                            i += 1
                            if i == xi:
                                break
                    else:
                        if t[y] == u'ADV' and t[y-1] != u'V' and t[y-1] != u'CL' or t[y] == u'V' or t[y] == u'CL':
                            vp[index].append(s[y])
                            vtags[index].append(t[y])
                        yj += 1
            index += 1

        print "AP = \n", '\n'.join(' '.join('[' + ', '.join(aa) + ']' for aa in a) for a in ap)
        # print "AP:: ", ap
        print "VP:: \n", vp
        print "verb Tags:: \n", vtags
        # print "Tags = \n", tags
        print "PREP = \n", prep
        # print "SENTENCES = \n", sents
        # print "Tags_Sentences = \n", tags_sents
        return ap, tags, prep, sents, tags_sents, vp, vtags


if __name__ == '__main__':
    question = QuestionGenerator()
