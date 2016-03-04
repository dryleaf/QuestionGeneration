markPossibleAnswerPhrases: (ROOT (S (NP-0 (UNMOVABLE-NP (DT the) (NN capital)) (UNMOVABLE-PP (IN of) (UNMOVABLE-NP (NNP Russia)))) (VP (VBZ is) (NP-1 (NNP Moscow))) (. .)))
Number of Possible WH questions: 2

moveWHPhrase: inputTree:(ROOT (S (NP-0 (UNMOVABLE-NP (DT the) (NN capital)) (UNMOVABLE-PP (IN of) (UNMOVABLE-NP (NNP Russia)))) (VP (VBZ is) (NP-1 (NNP Moscow))) (. .)))
moveWHPhrase: inputTree:(ROOT (SQ (NP-0 (UNMOVABLE-NP (DT the) (NN capital)) (UNMOVABLE-PP (IN of) (UNMOVABLE-NP (NNP Russia)))) (VP (VBZ is) (NP-1 (NNP Moscow))) (. .)))
moveWHPhrase: tregexOpStr:ROOT=root < (SQ=qclause << /^(NP|PP|SBAR)-0$/=answer < VP=predicate)
getWHPhraseSubtrees: phraseToMove: (NP (NP (DT the) (NN capital)) (PP (IN of) (NP (NNP Russia))))
moveWHPhrase: whPhraseSubtree:(WHNP (WHNP (WRB what)))
moveLeadingAdjuncts:(ROOT (SBARQ (WHNP (WHNP (WRB what))) (SQ (VP (VBZ is) (NP (NNP Moscow))) (. .))))
moveLeadingAdjuncts(out):(ROOT (SBARQ (WHNP (WHNP (WRB what))) (SQ (VP (VBZ is) (NP (NNP Moscow))) (. .))))
moveWHPhrase: (ROOT (SBARQ (WHNP (WHNP (WRB what))) (SQ (VP (VBZ is) (NP (NNP Moscow))) (. .))))
Loading language model from config/anc-v2-written.lm.gz...done.

moveWHPhrase: inputTree:(ROOT (S (NP-0 (UNMOVABLE-NP (DT the) (NN capital)) (UNMOVABLE-PP (IN of) (UNMOVABLE-NP (NNP Russia)))) (VP (VBZ is) (NP-1 (NNP Moscow))) (. .)))
decomposePredicate: (ROOT (S (NP-0 (UNMOVABLE-NP (DT the) (NN capital)) (UNMOVABLE-PP (IN of) (UNMOVABLE-NP (NNP Russia)))) (VP (VBZ is) (NP-1 (NNP Moscow))) (. .)))
subjectAuxiliaryInversion: (ROOT (S (VBZ is) (NP-0 (UNMOVABLE-NP (DT the) (NN capital)) (UNMOVABLE-PP (IN of) (UNMOVABLE-NP (NNP Russia)))) (VP (NP-1 (NNP Moscow))) (. .)))
moveWHPhrase: inputTree:(ROOT (SQ (VBZ is) (NP-0 (UNMOVABLE-NP (DT the) (NN capital)) (UNMOVABLE-PP (IN of) (UNMOVABLE-NP (NNP Russia)))) (VP (NP-1 (NNP Moscow))) (. .)))
moveWHPhrase: tregexOpStr:ROOT=root < (SQ=qclause << /^(NP|PP|SBAR)-1$/=answer < VP=predicate)
getWHPhraseSubtrees: phraseToMove: (NP (NNP Moscow))
moveWHPhrase: whPhraseSubtree:(WHNP (WHNP (WRB what)))
moveLeadingAdjuncts:(ROOT (SBARQ (WHNP (WHNP (WRB what))) (SQ (VBZ is) (NP (NP (DT the) (NN capital)) (PP (IN of) (NP (NNP Russia)))) (. .))))
moveLeadingAdjuncts(out):(ROOT (SBARQ (WHNP (WHNP (WRB what))) (SQ (VBZ is) (NP (NP (DT the) (NN capital)) (PP (IN of) (NP (NNP Russia)))) (. .))))
moveWHPhrase: (ROOT (SBARQ (WHNP (WHNP (WRB what))) (SQ (VBZ is) (NP (NP (DT the) (NN capital)) (PP (IN of) (NP (NNP Russia)))) (. .))))

decomposePredicate: (ROOT (S (NP-0 (UNMOVABLE-NP (DT the) (NN capital)) (UNMOVABLE-PP (IN of) (UNMOVABLE-NP (NNP Russia)))) (VP (VBZ is) (NP-1 (NNP Moscow))) (. .)))
subjectAuxiliaryInversion: (ROOT (S (VBZ is) (NP (NP (DT the) (NN capital)) (PP (IN of) (NP (NNP Russia)))) (VP (NP (NNP Moscow))) (. .)))
moveLeadingAdjuncts:(ROOT (SQ (VBZ is) (NP (NP (DT the) (NN capital)) (PP (IN of) (NP (NNP Russia)))) (VP (NP (NNP Moscow))) (. .)))
moveLeadingAdjuncts(out):(ROOT (SQ (VBZ is) (NP (NP (DT the) (NN capital)) (PP (IN of) (NP (NNP Russia)))) (VP (NP (NNP Moscow))) (. .)))

