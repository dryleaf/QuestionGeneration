/**
	 *
	 * This method marks phrases in the tree that should not undergo WH movement
	 * and become answers to questions, either due to syntactic 
	 * constraints or some conservative restrictions used to avoid
	 * particular constructions that the system is not designed to handle.
	 * 
	 * E.g., 
	 * Sentence: Darwin studied how SPECIES evolve.
	 * Avoided Question: * What did Darwin study how evolve?
	 *
	 */
	private Tree markUnmovablePhrasesFull(Tree inputTree){
		Tree copyTree = inputTree.deeperCopy();

		//adjunct clauses under verb phrases (following commas)
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (VP < (S=unmovable $,, /,/))");
		
		//anything under a sentence level subordinate clause
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root < (S < PP|ADJP|ADVP|S|SBAR=unmovable)");

		//anything under a phrase directly dominating a conjunction
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (/\\.*/ < CC << NP|ADJP|VP|ADVP|PP=unmovable)");

		//adjunct clauses -- assume subordinate clauses that have a complementizer other than "that" (or empty) are adjuncts 
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (SBAR < (IN|DT < /[^that]/) << NP|PP=unmovable)");

		//anything under a WH phrase
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (SBAR < /^WH.*P$/ << NP|ADJP|VP|ADVP|PP=unmovable)");

		//"Complementizer-trace effect"
		//the subject of a complement phrase when an explicit complementizer is present (e.g., I knew that JOHN ran.)
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (SBAR <, IN|DT < (S < (NP=unmovable !$,, VP)))");

		//anything under a clause that is a predicate nominative (e.g., my favorite activity is to run in THE PARK)
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (S < (VP <+(VP) (VB|VBD|VBN|VBZ < be|being|been|is|are|was|were|am) <+(VP) (S << NP|ADJP|VP|ADVP|PP=unmovable)))");		
		
		//objects of prepositional phrases with prepositions other than "of" or "about".
		//"of" and "about" signal that the modifier is a complement rather than an adjunct. 
		//allows: "John visited the capital of Alaska." -> "What did John visit the capital of?"
		//disallows: "John visited a city in Alaska." -> ? "What did John visit a city in?"
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (NP << (PP=unmovable !< (IN < of|about)))");
		
		//nested prepositional phrases of any kind 
		//disallows: "Bill saw John in the hall of mirrors." -> * "What did Bill see John in the hall of?"
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (PP << PP=unmovable)");
		
		//prepositional phrases in subjects (e.g., disallows: "The capital of Alaska is Juneau." -> * "What is the capital of Juneau?")
		//Nothing can be moved out of subjects.
		//I think the generative account is that phrases can only be moved to the level of the verb
		//that governs them, and subjects (along with adjuncts) are not governed by the verb.
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (NP $ VP << PP=unmovable)");
		
		//subordinate clauses that are not complements of verbs
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (SBAR=unmovable [ !> VP | $-- /,/ | < RB ])");
		
		//adjunct subordinate clauses
		//"how", "whether", and "that" under IN or WHADVP nodes signal complements.
		//WHNP always signals a complement.
		//otherwise, the SBAR is an adjunct.
		//Note: we mark words like "where" as unmovable because they are potentially adjuncts. 
		//  e.g., "he knew where it was" has a complement, but "he went to college where he grew up" has an adjunct
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (SBAR=unmovable !< WHNP < (/^[^S].*/ !<< that|whether|how))"); //dominates a non-S node that doesn't include one of the unambiguous complementizers 
		
		//////////////////////////////////////////////////////////////
		//MARK SOME AS UNMOVABLE TO AVOID OBVIOUSLY BAD QUESTIONS
		//
		
		//existential there NPs
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (NP=unmovable < EX)");

		//phrases in quotations
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (/^S/ < `` << NP|ADJP|VP|ADVP|PP=unmovable)");
		
		//prepositional phrases that don't have NP objects
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (PP=unmovable !< /.*NP/)");

		//pronouns which are the subject of complement verb phrases
		//These would nearly always lead to silly/tricky questions (e.g., "GM says its profits will fall." -> "Whose profits did GM say will fall?") 
		//markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (VP < (SBAR < (S <<, (NP=unmovable < PRP))))");

		//both NPs that are under an S (MJH: we are punting on this).  
		//If there are multiple NPs, one may be a temporal modifier
		markMultipleNPsAsUnmovable(copyTree);
		/////////////////////////////////////////////////////////////////
		
		
		////////////////////////////////////////////////////////////////
		//PROPAGATE ABOVE CONSTRAINTS
		//any non-PP phrases under otherwise movable phrases (we assume movable phrases serve as islands)
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (NP|PP|ADJP|ADVP|PP << (NP|ADJP|VP|ADVP=unmovable))");
		
		//anything under an unmovable node
		markNodesAsUnmovableUsingPattern(copyTree, "ROOT=root << (@UNMOVABLE << NP|ADJP|VP|ADVP|PP=unmovable)");

		if(GlobalProperties.getDebug()) System.err.println("markUnmovablePhrases: "+copyTree.toString());
		return copyTree;
	}


	/**
	 * This method is used to mark noun phrases that are sisters of each other, 
	 * such as in double object dative constructions.  
	 * I could not figure out how to get Tsurgeon to do this easily, 
	 * so phrases are just marked using the stanford parser API instead.
	 * 
	 * E.g., 
	 * sentence: John gave Mary the book.
	 * avoided question: * Who did John give the book? (the system doesn't convert "indirect" objects to oblique arguments)
	 * 
	 * @param inputTree
	 */
	private void markMultipleNPsAsUnmovable(Tree inputTree){
		List<Pair<TregexPattern, TsurgeonPattern>> ops = new ArrayList<Pair<TregexPattern, TsurgeonPattern>>();
		List<TsurgeonPattern> ps = new ArrayList<TsurgeonPattern>();
		TregexPattern matchPattern;
		TsurgeonPattern p;

		String tregexOpStr = "(NP=unmovable $ @NP)";
		matchPattern = TregexPatternFactory.getPattern(tregexOpStr);
		ps.add(Tsurgeon.parseOperation("relabel unmovable NP-UNMOVABLE"));
		p = Tsurgeon.collectOperations(ps);
		ops.add(new Pair<TregexPattern,TsurgeonPattern>(matchPattern,p));		
		Tsurgeon.processPatternsOnTree(ops, inputTree);

		ops.clear();
		ps.clear();
		tregexOpStr = "NP-UNMOVABLE=unmovable";
		matchPattern = TregexPatternFactory.getPattern(tregexOpStr);
		ps.add(Tsurgeon.parseOperation("relabel unmovable UNMOVABLE-NP"));
		p = Tsurgeon.collectOperations(ps);
		ops.add(new Pair<TregexPattern,TsurgeonPattern>(matchPattern,p));
		Tsurgeon.processPatternsOnTree(ops, inputTree);
	}

