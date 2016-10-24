#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Josimar H. Lopes,
# Master of EEIE, NUT

from subprocess import Popen, PIPE, check_output

import re
import os
import sys
import tempfile
import math

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import pylab as pl
import matplotlib.cm as cm
matplotlib.style.use('ggplot')

from udacityplots import *

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from S1Tranform import StanfordParserPT
from S1Tranform import SentenceSimplifier
from decimal import *
getcontext().prec = 3
getcontext().rounding = ROUND_HALF_UP


class QuestionGenerator:
    """Class to generate candidate questions from a declarative sentefnce."""

    def __init__(self):
        """Initializes all the premises"""
        self.__refsent = []
        self.__sents = []
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
        # print sentences
        for k in sentences.split('\n'):
            self.__sents.append(k.decode('utf-8'))
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
                    if '+' in line[2] and '+' in line[1]:
                        line1 = line[1].split('+')
                        line2 = line[2].split('+')
                        self.__sst[i].append("B-" + line1[0] + "." + line2[0])
                    else:
                        self.__sst[i].append("B-" + line[1] + "." + line[2])
                elif bool(re.search(r'^PP[0-3][CMF][SP][0N]00$', line[2])):
                    self.__sst[i].append("B-" + line[0] + ".PERSON")
                else:   # Trigger words condition to NER
                    if bool(line[1].encode(self.__encoding) in _twPER):
                        self.__sst[i].append("B-" + line[0] + ".PERSON")
                    elif bool(line[1].encode(self.__encoding) in _twLOC):
                        self.__sst[i].append("B-" + line[0] + ".LOCATION")
                    elif bool(line[1].encode(self.__encoding) in _twORG):
                        self.__sst[i].append("B-" + line[0] + ".ORGANIZATION")
                    elif bool(re.search(r'^W$', line[2])):
                        # print "Line.:", line
                        self.__sst[i].append("B-" + line[0] + ".TIME")
                    else:
                        self.__sst[i].append(line[2])
            self.__sst[i].append("0")
            i += 1
        print '\n'.join('[' + ', '.join(s) + ']' for s in self.__sst)

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

        # Verb Tenses
        verbTense = {'VMIP': 'Presente do Indicativo', 'VMII': 'Imperfeito do Indicativo',
                     'VMIS': 'Perfeito do Indicativo', 'VMIF': 'Futuro do Presente do Indicativo',
                     'VMIC': 'Futuro do Pretérito do Indicativo', 'VMSP': 'Presente do Subjuntivo',
                     'VMSI': 'Imperfeito do Subjuntivo', 'VMSF': 'Futuro do Subjuntivo',
                     'VAIP': 'Presente do Indicativo', 'VAII': 'Imperfeito do Indicativo',
                     'VAIS': 'Perfeito do Indicativo', 'VAIF': 'Futuro do Presente do Indicativo',
                     'VAIC': 'Futuro do Pretérito do Indicativo', 'VASP': 'Presente do Subjuntivo',
                     'VASI': 'Imperfeito do Subjuntivo', 'VASF': 'Futuro do Subjuntivo',
                     'VSIP': 'Presente do Indicativo', 'VSII': 'Imperfeito do Indicativo',
                     'VSIS': 'Perfeito do Indicativo', 'VSIF': 'Futuro do Presente do Indicativo',
                     'VSIC': 'Futuro do Pretérito do Indicativo', 'VSSP': 'Presente do Subjuntivo',
                     'VSSI': 'Imperfeito do Subjuntivo', 'VSSF': 'Futuro do Subjuntivo'}

        # Possible Preposition Combination
        ppc = {u'em_': u'n', u'de_': u'd', u'per_': u'pel', u'por_': u'pel'}
        spc = {u'a_': [u'a', u'\xe0']}

        # Save output
        corpus = []

        j = 0
        c_que = 0
        c_quem = 0
        c_quando = 0
        c_quanto = 0
        c_onde = 0
        c_qual = 0

        c_per = 0
        c_loc = 0
        c_org = 0
        c_time = 0

        ner_que = 0
        ner_quem = 0
        ner_quando = 0
        ner_quanto = 0
        ner_qual = 0
        ner_onde = 0

        p_que = 0
        p_quem = 0
        p_onde = 0

        for aptree in trees:
            # Case 1: Answer Phrase in the Subject
            n = nAnswes[j] + 1
            question.append([])
            qtags.append([])
            qp.append([])
            temp_vp.append([])
            temp_vtags.append([])
            # issubj = False
            for i in range(n + 1):  # n+1 includes the yes/no question.
                qtype = ""
                if i < n-1:
                    m = self.contains(ap[j][i], sents[j])
                question[j].append(sents[j][:])
                qtags[j].append(tags_sents[j][:])
                temp_vp[j].append(vp[j][:])
                temp_vtags[j].append(vtags[j][:])
                #print m
                issubj = False
                if i < n-1:
                    if self.inSubject(aptree, i):
                        issubj = True
                    else:
                        issubj = False

                    # print "jth = ", j, " + m = ", m, " + Q:: ", question[j], " + sst = ", self.__sst[j]
                    isperson = bool(re.search(r'\.PERSON|\.PRS', ' '.join(self.__sst[j][m[0]:m[1]])))
                    isorg = bool(re.search(r'\.ORGANIZATION', ' '.join(self.__sst[j][m[0]:m[1]])))
                    isloc = bool(re.search(r'\.LOCATION', ' '.join(self.__sst[j][m[0]:m[1]])))
                    istime = bool(re.search(r'\.TIME', ' '.join(self.__sst[j][m[0]:m[1]])))
                    isqual = bool(re.search('B-ser\.V', ' '.join(self.__sst[j][:])))
                    flag_art = True if ' '.join(art for art in tags[j][i]).startswith(u'ART') else False
                    # print "PERSON = ", isperson, " ORG = ", isorg, " LOC = ", isloc, " TIME = ", istime, " To Be = ", isqual, " ART = ", flag_art

                    if isperson:
                        c_per += 1
                        # print "PER"
                        # prepare 'Quem' question phrasek
                        if prep[j][i] == u'PP':
                            if tags[j][i][1] == u'V':
                                qtype = u'O que'
                                c_que += 1
                                ner_que += 1
                            elif tags[j][i][1] == u'CL' and isqual and not flag_art:
                                qtype = u'Qual'
                                c_qual += 1
                                ner_qual += 1
                            elif u'ADV' in tags[j][i]:
                                if tags[j][i].index(u'ADV') < tags[j][i].index(u'N'):
                                    qtype = u'O que'
                                    c_que += 1
                                    ner_que += 1
                                else:
                                    qtype = ap[j][i][0] + u' quem'
                                    c_quem += 1
                                    ner_quem += 1
                                    p_quem += 1
                            else:
                                qtype = ap[j][i][0] + u' quem'
                                c_quem += 1
                                ner_quem += 1
                                p_quem += 1
                            qtype = qtype.replace(u'_', u'')
                        elif prep[j][i] == u'CP':
                            qtype = u'O que'
                            c_que += 1
                            ner_que += 1
                        elif prep[j][i] == u'NP':
                            if not issubj:
                                if u'N' in tags[j][i]:
                                    if 'B-' + ap[j][i][tags[j][i].index(u'N')] + '.PERSON' not in self.__sst[j]:
                                        qtype = u'O que'
                                        c_que += 1
                                        ner_que += 1
                                    else:
                                        qtype = u'Quem'
                                        c_quem += 1
                                        ner_quem += 1
                                else:
                                    qtype = u'Quem'
                                    c_quem += 1
                                    ner_quem += 1

                            elif u'N' in tags[j][i]:
                                if 'B-' + ap[j][i][tags[j][i].index(u'N')] + '.PERSON' not in self.__sst[j]:
                                    qtype = u'O que'
                                    c_que += 1
                                    ner_que += 1
                                else:
                                    qtype = u'Quem'
                                    c_quem += 1
                                    ner_quem += 1
                            else:
                                    qtype = u'Quem'
                                    c_quem += 1
                                    ner_quem += 1
                        else:
                            qtype = u'Quem'
                            c_quem += 1
                            ner_quem += 1
                    elif isorg:
                        c_org += 1
                        # print "ORG"
                        # prepare 'O que' or 'Qual' question phrase
                        # case 'Qual':
                        # if
                        if prep[j][i] == u'PP':
                            if ap[j][i][1] == u'a' and tags[j][i][1] == u'ART' and ap[j][i][0] == u'a_':
                                qtype = ap[j][i][0] + u'onde'
                                c_onde += 1
                                ner_onde += 1
                                p_onde += 1
                            elif tags[j][i][1] == u'ART':
                                qtype = ap[j][i][0] + u' que'
                                c_que += 1
                                ner_que += 1
                                p_que += 1
                            else:
                                qtype = u'Onde'
                                c_onde += 1
                                ner_onde += 1
                            qtype = qtype.replace(u'_', u'')
                        else:
                        # case 'O que':
                            qtype = u'O que'
                            c_que += 1
                            ner_que += 1

                    elif isloc:
                        c_loc += 1
                        # print "LOC"
                        # case 'Onde':

                        if prep[j][i] == u'PP':
                            if u'N' in tags[j][i]:
                                if 'B-' + ap[j][i][tags[j][i].index(u'N')] + '.LOCATION' not in self.__sst[j]:
                                    qtype = ap[j][i][0] + u' que'
                                    c_que += 1
                                    ner_que += 1
                                    p_que += 1
                                    qtype = qtype.replace(u'_', u'')
                                elif (ap[j][i][0] == u'de_' or ap[j][i][0] == u'a_') and tags[j][i][1] == u'ART':
                                    qtype = ap[j][i][0] + u' onde'
                                    c_onde += 1
                                    ner_onde += 1
                                    p_onde += 1
                                    qtype = qtype.replace(u'_', u'')
                                elif ap[j][i][0] == u'de' and tags[j][i][1] == u'N':
                                    qtype = ap[j][i][0] + u' onde'
                                    c_onde += 1
                                    ner_onde += 1
                                    p_onde += 1
                                else:
                                    qtype = u'Onde'
                                    c_onde += 1
                                    ner_onde += 1
                            else:
                                qtype = u'Onde'
                                c_onde += 1
                                ner_onde += 1
                        # case 'Qual':
                        elif isqual and not flag_art:
                            qtype = u'Qual'
                            c_qual += 1
                            ner_qual += 1
                        # case 'O que':
                        else:
                            qtype = u'O que'
                            c_que += 1
                            ner_que += 1
                    elif istime:
                        c_time += 1
                        # case 'Quando'
                        if prep[j][i] == u'PP':
                            qtype = u'Quando'
                            c_quando += 1
                            ner_quando += 1
                        elif prep[j][i] == u'NP' and bool(tags[j][i].index(u'P')):
                            qtype = u'Quando'
                            c_quando += 1
                            ner_quando += 1
                        else:
                            qtype = u'O que'
                            c_que += 1
                            ner_que += 1
                    else:
                        # case 'Quanto'
                        if prep[j][i] == u'NP':
                            if tags[j][i][0] == u'CARD':
                                if u'N' in tags[j][i]:  # tags[j][i][1] == u'N'
                                    if u'NCMP000' in self.__sst[j][m[0]:m[1]]:
                                        qtype = u'Quantos ' + ap[j][i][1]
                                        c_quanto += 1
                                    elif u'NCFP000' in self.__sst[j][m[0]:m[1]]:
                                        qtype = u'Quantas ' + ap[j][i][1]
                                        c_quanto += 1
                                    elif u'NCCS000' in self.__sst[j][m[0]:m[1]] or u'NCCP000' in self.__sst[j][m[0]:m[1]]:
                                        qtype = u'O que'
                                        c_que += 1
                                    elif u'NCMS000' in self.__sst[j][m[0]:m[1]] or u'NCFS000' in self.__sst[j][m[0]:m[1]]:
                                        qtype = u'O que'
                                        c_que += 1
                                    else:
                                        qtype = u'Quantos'
                                        c_quanto += 1
                                else:
                                    qtype = u'Quantos'
                                    c_quanto += 1
                            elif isqual and not flag_art and tags[j][i][0] != u'DEM':
                                qtype = u'Qual'
                                c_qual += 1
                            else:
                                qtype = u'O que'
                                c_que += 1
                        elif prep[j][i] == u'PP':
                            if u'CARD' in tags[j][i]:
                                if tags[j][i][-1] == u'N':
                                    qtype = ap[j][i][0] + u' que ' + ap[j][i][-1]
                                    c_que += 1
                                    p_que += 1
                                else:
                                    qtype = ap[j][i][0] + u' que'
                                    c_que += 1
                                    p_que += 1
                            else:
                                if ap[j][i][0] == u'de' and tags[j][i][1] == u'N' \
                                        or ap[j][i][0] == u'de_' and tags[j][i][1] == u'ART'\
                                        or ap[j][i][0] == u'em_' and tags[j][i][1] == u'ART':
                                    qtype = ap[j][i][0] + u' que'
                                    c_que += 1
                                    p_que += 1
                                elif tags[j][i][0] == u'P' and tags[j][i][1] == u'DEM' and tags[j][i][-1] != u'DEM':
                                    qtype = ap[j][i][0] + u' que ' + ap[j][i][2]
                                    c_que += 1
                                elif ap[j][i][0] == u'em' and tags[j][i][1] == u'N' \
                                        and bool(re.search(r'[0-9]{4}', ''.join(ap[j][i][1]))) \
                                        and tags[j][i][1] == tags[j][i][-1]:
                                    qtype = u'Quando'
                                    c_quando += 1
                                else:
                                    qtype = ap[j][i][0] + u' que'
                                    c_que += 1
                                    p_que += 1
                            qtype = qtype.replace(u'_', u'')
                        else:
                            qtype = u'O que'
                            c_que += 1

                    if not issubj:
                        qtype = qtype.capitalize()
                        word = question[j][i][0]
                        prs = bool(re.search(r'DP[.]*', ''.join(self.__sst[j][0])))
                        # print "PRS = ", prs
                        if qtags[j][i][0] != u'N' or qtags[j][i][0] == u'N' and prs:
                            question[j][i][0] = word.lower()
                    qp[j].append(qtype)
                if i == n-1:
                    word = question[j][i][0]
                    question[j][i][0] = word.lower()

                if i < n-1 and issubj:  # and tags[j][i][0] == u'PRS':
                    # Verb Agreement Rules
                    # print "sst= ", self.__sst[j][:]

                    str1 = re.findall(r'B-\w+\.V[A-Z0-9]{6}', ' '.join(self.__sst[j][:]), re.UNICODE)[0]
                    str1 = str1.split('-')[1].split('.')
                    if str1[1][:4] in verbTense:
                        verbo = str1[0]
                        ln = 3
                        if (str1[1][4] == '1' or str1[1][4] == '2' or str1[1][4] == '3') and str1[1][5] == 'S':
                            ln = 3
                        elif (str1[1][4] == '1' or str1[1][4] == '2' or str1[1][4] == '3') and str1[1][5] == 'P':
                            ln = 6

                        tempo = verbTense[str1[1][:4]]
                        cmd_gconjugate = Popen(["conjugar", verbo], stdout=PIPE)
                        awk_gconjugate = Popen(["awk", "/^" + str(tempo) +
                                                       "$/{x = NR + " + str(ln) + "}NR == x{print $2}"],
                                               stdin=cmd_gconjugate.stdout, stdout=PIPE)
                        cmd_gconjugate.stdout.close()
                        output = awk_gconjugate.communicate()[0]
                        # print "CMD.: ", output
                        temp_vp[j][i][temp_vtags[j][i].index(u'V')] = str(output).decode('utf-8').strip('\n')
                if n > 1:
                    # print "question[j][i] = ", question[j][i]
                    cnt = len(temp_vtags[j][i])
                    prev = temp_vtags[j][i][0]
                    value = temp_vp[j][i][0]
                    for ind in range(1, cnt):
                        if prev == u'V' and temp_vtags[j][i][ind] == u'CL':
                            temp_vtags[j][i][ind-1] = temp_vtags[j][i][ind]
                            temp_vtags[j][i][ind] = prev
                            cl_temp = temp_vp[j][i][ind]
                            temp_vp[j][i][ind] = cl_temp.replace(u'-', u'')
                            temp_vp[j][i][ind-1] = temp_vp[j][i][ind]
                            temp_vp[j][i][ind] = value
                        else:
                            prev = temp_vtags[j][i][ind]
                            value = temp_vp[j][i][ind]
                # print "Ordered:: ", temp_vp[j][i], " Unordered:: ", vp[j]
                # print "Ordered_t:: ", temp_vtags[j][i], " Unordered_t:: ", vtags[j]
                # if n > 1:  # or temp_vtags[j][i][0] == u'ADV':
                    temp_qg = ' '.join(question[j][i])
                    temp_tag = ' '.join(qtags[j][i])
                    temp_qg = temp_qg.replace(' '.join(vp[j]).lower(), ' '.join(temp_vp[j][i]).lower())
                    # print "temp_qg::", temp_qg, ", vp.: ", ' '.join(vp[j]), " temp_vp.: ", ' '.join(temp_vp[j][i]).lower()
                    temp_tag = temp_tag.replace(' '.join(vtags[j]), ' '.join(temp_vtags[j][i]))
                    question[j][i] = temp_qg.split(' ')
                    # print "Question: ", question[j][i]
                    qtags[j][i] = temp_tag.split(' ')

                if i < n-1:
                    del question[j][i][m[0]:m[1]]
                    question[j][i].insert(m[0], qtype)
                question[j][i][-1] = u'?'

                if i < n-1:
                    del qtags[j][i][m[0]:m[1]]
                    qtags[j][i].insert(m[0], u'QP')

                    if not issubj:
                        # print "CUR_Q.: ", question[j][i]
                        # print "CUR_Q.: ", qtags[j][i]

                        # print "In question.: ", question[j][i]
                        vbindex = question[j][i].index(temp_vp[j][i][0].lower())
                        vfindex = question[j][i].index(temp_vp[j][i][-1].lower()) + 1
                        # print "vbindex = ", vbindex, " vfindex = ", vfindex

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

                    # remove ADV if it appears at the end of the sentence
                    if qtags[j][i][-2] == u'ADV':
                        del qtags[j][i][-2]
                        del question[j][i][-2]

                if i == n-1:
                    word = question[j][i][0]
                    question[j][i][0] = word.capitalize()

                # Post-processing
                if u'P' in qtags[j][i]:
                    nt = 0
                    for qtg in qtags[j][i]:
                        if qtg == u'P' and u'_' in question[j][i][nt]:
                            qval = question[j][i][nt]
                            if qval in ppc:
                                question[j][i][nt] = ppc[qval] + question[j][i][nt + 1]
                                qtags[j][i][nt] = u'P\''
                                del question[j][i][nt + 1]
                                del qtags[j][i][nt + 1]
                            elif qval in spc:
                                if qval in spc:
                                    qvalnext = question[j][i][nt + 1]
                                    if qvalnext.startswith('o'):
                                        question[j][i][nt] = spc[qval][0] + question[j][i][nt + 1]
                                        qtags[j][i][nt] = u'P\''
                                        del question[j][i][nt + 1]
                                        del qtags[j][i][nt + 1]
                                    elif qvalnext == u'a':
                                        question[j][i][nt] = spc[qval][1]
                                        qtags[j][i][nt] = u'P\''
                                        del question[j][i][nt + 1]
                                        del qtags[j][i][nt + 1]
                                    elif qvalnext.startswith('a'):
                                        question[j][i][nt] = spc[qval][1] + question[j][i][nt + 1][1:]
                                        qtags[j][i][nt] = u'P\''
                                        del question[j][i][nt + 1]
                                        del qtags[j][i][nt + 1]
                        nt += 1
                # if u'V' in qtags[j][i]:
                #    if question[j][i][qtags[j][i].index(u'V')] != question[j][i][-2] \
                #            and qtags[j][i][-2] == u'V' and (qtags[j][i][-3] == u'N' or qtags[j][i][-3] == u'ADV'):
                #        print qtags[j][i]
                #        del question[j][i][-2]
                #        del qtags[j][i][-2]
                # else:
                #    print question[j][i], " / ", sents[j][:]
                question[j][i][-2] = question[j][i][-2] + question[j][i][-1]
                del question[j][i][-1]
                del qtags[j][i][-1]

            j += 1
            # if j == len(self.__sst):
            #    break

        j = 0
        # save to file
        filename = 'test-OUT.txt'
        if len(sys.argv) == 2:
            filename = os.path.splitext(os.path.basename(sys.argv[1]))[0]
        outfile = open(filename + 'OUT.txt', 'w')
        print
        q_mean = []
        for spair in self.__sents:
            mean = 0
            for qpair in question[j][:-1]:
                pair = ' '.join(qpair) + '|' + spair + '\n'
                cpair = ' '.join(qpair)
                outfile.write(pair.encode('utf-8'))
                corpus.append(cpair + '\n')
                mean += len(cpair.split())
            if question[j] == question[-1]:
                break
            else:
                if nAnswes[j] == 0:
                    mean = Decimal(mean) / Decimal(nAnswes[j]+1)
                else:
                    mean = Decimal(mean) / Decimal(nAnswes[j])
                q_mean.append(float(mean))
                j += 1
        outfile.close()
        avg_ap = Decimal(sum(ith for ith in nAnswes)) / Decimal(len(ap))
        avg_len = Decimal(sum(len(c.split()) for c in corpus)) / Decimal(len(corpus))
        wordset = [len(w.split()) for w in corpus]
        word_tok = list(set(wordset))
        word_freq = [wordset.count(w) for w in word_tok]

        ans_tok = list(set(nAnswes))
        ans_freq = [nAnswes.count(a) for a in ans_tok]

        # print qp
        # print qtags
        # print "\n++++++++++++++++Generated Questions+++++++++++++++"
        print ''.join(c for c in corpus)
        # print "Quem = ", ner_quem, "\nQue = ", ner_que, "\nQual = ", ner_qual, "\nQuanto = ", ner_quanto, "\nQuando = ", ner_quando, "\nOnde = ", ner_onde
        # print "Quem = ", p_quem, "\nQue = ", p_que, "\nOnde = ", p_onde
        # print "corpus = ", len(corpus), "\navg_Q = ", avg_len, "\navg_ap = ", avg_ap
        # print '\n\n'.join('\n'.join(' '.join(qss) for qss in qs) for qs in question)
        # print '\n\n'.join('\n'.join('[' + ', '.join(qtt) + ']' for qtt in qt) for qt in qtags)
        # print question
        # print "\nn = ", len(q_mean), "\nmean = ", q_mean, "\nn = ", len(nAnswes), "\nnAnswers = ", nAnswes
        # self.simple(wordset, nAnswes)
        # wordset = sorted(wordset)
        # prt = open("csv.txt", "w")
        # prt.writelines('\n'.join(str(x) for x in wordset))
        # prt.close()
        # self.multipleplots(nAnswes, wordset)

        # self.simple(nAnswes, wordset)
        # print word_tok, "::", word_freq
        # print ans_tok, "::", ans_freq


    def contains(self, small, big):
        for i in xrange(len(big)-len(small)+1):
            for j in xrange(len(small)):
                if big[i+j] != small[j]:
                    break
            else:
                return i, i+len(small)
        return 0, 0

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
                        # r'\b[A-Z]+ \w+\b'
                        flag_all = bool(re.search(r'\b[A-Z]+ [-]?\w+[-\w]*\b', string[i+1:].decode('utf8'), re.UNICODE))
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
                        ap1 = ','.join(re.findall(r'([A-Z]+ \w+[-\w]*)', string[b:i+1].decode('utf8'), re.UNICODE))
                        # print "ap1 = ", ap1
                        # ap[index].append({cnt: re.sub(r'([A-Z]+ )', '', ap1).split(',')})
                        ap[index].append(re.sub(r'([A-Z]+ )', '', ap1).split(','))

                        # Sentence with tags
                        # 1:- SENTENCES
                        # print "UP.string = ", string[b:i+1]
                        t_s = ','.join(re.findall(r'([A-Z]+ [-]?\w+[-\w]*)', string[b:i+1].decode('utf8'), re.UNICODE))
                        s += ' '.join(re.sub(r'([A-Z]+ )', '', t_s).split(',')) + ' '

                        # 2:- TAGS
                        t += ''.join(t1.strip()) + ' '
                        # print "1. tags = ", t
                        flag_as = False

                    elif flag_all and level == savedlevel:
                        # Sentence with tags
                        # 1:- SENTENCES
                        # print "DOWN.string = ", string[b:i+1]
                        # r'\b[A-Z]+ [-]?\w+[-\w]*\b'
                        t_s = ','.join(re.findall(r'([A-Z]+ [-]?\w+[-\w]*)', string[b:i+1].decode('utf8'), re.UNICODE))
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
            vcnt = 0
            wcnt = 0
            s = s.split(' ')
            t = t.split(' ')
            # print "t = ", t, " s = ", s
            aplen = len(ap[index])
            first_flag = True
            # prev = ""
            for x in ap[index]:
                xi = len(x)
                i = 0
                for y in range(yj, len(s)):
                    # prev = t[y]
                    if x[i] == s[y]:
                        first_flag = False
                        yj += 1
                        if aplen != 1:
                            i += 1
                            if i == xi:
                                break
                        else:  # added this break else
                            if i < xi:
                                i += 1
                                if i == xi:
                                    i -= 1
                            else:
                                i -= 1
                            continue
                    else:
                        # print "t[y] = ", t[y]
                        # print "General:: ", s[y]
                        if vp[index] != [] and not first_flag:
                            # print "YES ", vp[index]
                            # if vtags[index] == [u'ADV']:
                                # advi = vtags[index].index(u'ADV')
                                # del vp[index][advi]
                                # del vtags[index][advi]
                                # vcnt == 0
                                # wcnt = 0
                            # else:
                            break
                        if t[y] == u'ADV' and t[y-1] != u'V' and t[y-1] != u'CL' """and t[y-1] != u'N' and t[y-1] != u'A'""" \
                                and vcnt == 0 or t[y] == u'V' or t[y] == u'CL':

                            if t[y] == u'ADV' and vcnt == 0 or wcnt < 3 and t[y] == u'CL' and t[y-1] == u'V' \
                                    or wcnt < 3 and t[y] == u'V' and t[y-1] == u'CL' or vcnt == 0 and (t[y] == u'CL' or t[y] == u'V'):
                                if t[y] == u'V':
                                    vcnt += 1
                                # print "True"
                                first_flag = True
                                vp[index].append(s[y])
                                vtags[index].append(t[y])
                        wcnt += 1
                        yj += 1
            index += 1

        print "AP = \n", '\n'.join(' '.join('[' + ', '.join(aa) + ']' for aa in a) for a in ap)
        print "Tags = \n", tags
        # print "AP:: ", ap
        print "VP:: \n", vp
        print "verb Tags:: \n", vtags
        # print "PREP = \n", prep
        # print "SENTENCES = \n", sents
        # print "Tags_Sentences = \n", tags_sents
        return ap, tags, prep, sents, tags_sents, vp, vtags


if __name__ == '__main__':
    question = QuestionGenerator()
