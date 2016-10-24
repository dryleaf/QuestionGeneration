#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Josimar H. Lopes,
# Master of EEIE, NUT

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from S1Tranform import QuestionGenerator

class Ranking:
    """This class receives all the features and trains a ranking model"""

    def __init__(self):
        """Beginning"""
        global qg
        qg = QuestionGenerator.QuestionGenerator()

if __name__ == '__main__':
    ranker = Ranking()
