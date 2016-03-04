#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Josimar H. Lopes,
# Master of EEIE, NUT

import sys
from subprocess import check_output, Popen, PIPE
from itertools import izip
# from postag_maps import mwann_lx_map
# from spec_rules import tag_subst


class PortugueseParser():
    """Class to interface with the Stanford Parser, for compatibility with Portuguese"""

    # CMD_PRETOK = ["sed", "-ri", "s/-((l|n)?(a|o)s?|vos|te|me|se|lhes?)/- \\1/g", sys.argv[1]]
    # CMD_TAGGER = ["java", "-jar", "mWANN_Tagger/mwanntagger.jar", sys.argv[1], "mWANN_Tagger/Rede.ser", "mWANN_Tagger/Dicionario.ser"]
    CMD_PARSER = ["java", "-Xmx1024m", "-cp", "stanford-parser-2010-11-30/stanford-parser.jar", "edu.stanford.nlp.parser.lexparser.LexicalizedParser", "-tokenized", "-sentences", "newline", "-outputFormat", "oneline", "-tagSeparator", "/", "-uwModel", "edu.stanford.nlp.parser.lexparser.BaseUnknownWordModel", "stanford-parser-2010-11-30/cintil.ser.gz", "-"]

    def pos_tagging(self):
        # 1º passo: Classificação gramatical (POS-tagging) das palavras com o mWANN-tagger.
        check_output(self.CMD_PRETOK)
        docTags = check_output(self.CMD_TAGGER)

        return docTags

    def mWann2LXSubst(self, docTags):
        # 2º passo: Substituição das tags do mWANN-tagger pelas tags do LX-tagger para compatibilidade com o LX-parser.
        fSents = open(sys.argv[1])
        sentWords = []
        sentTags = []
        for sentTg in docTags.split("\n"):
            pTok = Popen(["Tokenizer/run-Tokenizer.sh"], stdin=PIPE, stdout=PIPE)
            tokSents, stderr = pTok.communicate(fSents.readline())
            print tokSents
            sentWords.append(tokSents.replace("*/", "").replace("\*", "").replace("\n", "").strip().split(" "))
            sentTags.append(sentTg.split(" "))

        fSents.close()

        taggedSents = []
        for (words, tags) in izip(sentWords, sentTags):
            if len(words) > 1:
                taggedSents.append(tag_subst(" ".join([word + "/" + mwann_lx_map[tag] for (word, tag) in izip(words, tags)])))

        return taggedSents, sentWords, sentTags

    def parsing(self, taggedSents):
        # 3º passo: Análise sintática (parsing) das sentenças com o LX-parser.
        pParse = Popen(self.CMD_PARSER, stdin=PIPE, stdout=PIPE)
        parsedSents, stderr = pParse.communicate("\n".join(taggedSents))

        return parsedSents

if __name__ == "__main__":
    portuguseParser = PortugueseParser()
    docTags = portuguseParser.pos_tagging()
    taggedSents, sentWords, sentTags = portuguseParser.mWann2LXSubst(docTags)
    parsedSents = portuguseParser.parsing(taggedSents)
    print parsedSents
