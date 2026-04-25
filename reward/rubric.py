import json
import re

class JudicialRubric:
    """
    OpenEnv Rubric for the Multi-Agent Judicial Environment.
    R = 0.35·legal_accuracy 
      + 0.25·neutrality 
      + 0.20·reasoning_quality 
      + 0.10·citation_validity 
      + 0.10·efficiency
      - 0.30·(per hallucinated citation, capped at -0.60)
      + 0.15·(majority consensus bonus if 3-LLM panel agrees)
    """

    def __init__(self):
        self.weights = {
            "accuracy": 0.35,
            "neutrality": 0.25,
            "reasoning": 0.20,
            "citation": 0.10,
            "efficiency": 0.10
        }

    def parse_action(self, completion: str) -> dict:
        try:
            # Simple JSON extraction in case there's markdown wrapping
            match = re.search(r'\{.*\}', completion, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(completion)
        except:
            return None

    def score_accuracy(self, action: dict, gold_verdict: str) -> float:
        if not action or "verdict" not in action:
            return 0.0
        
        pred = str(action.get("verdict")).lower()
        gold = str(gold_verdict).lower()
        
        # Exact match
        if pred == gold:
            return 1.0
            
        # Adjacency for civil cases
        civil_adjacent = {"liable": "partial_liability", "not_liable": "partial_liability", "partial_liability": "liable"}
        if pred in civil_adjacent and civil_adjacent[pred] == gold or \
           gold in civil_adjacent and civil_adjacent[gold] == pred:
            return 0.5
            
        # Adjacency for criminal cases
        crim_adjacent = {"guilty": "partial_liability", "not_guilty": "partial_liability", "partial_liability": "guilty"}
        if pred in crim_adjacent and crim_adjacent[pred] == gold or \
           gold in crim_adjacent and crim_adjacent[gold] == pred:
            return 0.5
            
        return 0.0

    def score_neutrality(self, action: dict) -> float:
        """
        In full setup this runs demographic swaps. 
        For now, penalizes biased/charged keywords.
        """
        if not action or "reasoning_chain" not in action:
            return 0.0
        
        reasoning = str(action.get("reasoning_chain", "")).lower()
        charged_words = ["obviously guilty", "clearly wrong", "stupid", "idiotic", "maliciously", "evil"]
        
        if any(word in reasoning for word in charged_words):
            return 0.0
        return 1.0

    def score_reasoning(self, action: dict) -> float:
        """IRAC Structure check"""
        if not action or "reasoning_chain" not in action:
            return 0.0
            
        reasoning = str(action.get("reasoning_chain", "")).lower()
        
        score = 0.0
        if "issue:" in reasoning or "issue" in reasoning: score += 0.25
        if "rule:" in reasoning or "section" in reasoning or "act" in reasoning: score += 0.25
        if "application:" in reasoning or "because" in reasoning or "given that" in reasoning: score += 0.25
        if "conclusion:" in reasoning or "therefore" in reasoning or action.get("verdict", "") in reasoning: score += 0.25
        
        return score

    def score_citation(self, action: dict) -> float:
        if not action or "cited_precedents" not in action:
            return 0.0
        
        citations = action.get("cited_precedents", [])
        if not citations:
            return 0.0
            
        # Basic check for now - in full version calls IndianKanoon API
        valid = 0
        for cite in citations:
            if " v " in cite or " vs " in cite or "SC" in cite or "AIR" in cite:
                valid += 1
                
        return min(1.0, valid / max(1, len(citations)))

    def calculate_hallucination_penalty(self, action: dict) -> float:
        if not action or "cited_precedents" not in action:
            return 0.0
            
        # Basic mock for hallucination check
        citations = action.get("cited_precedents", [])
        fake_count = 0
        for cite in citations:
            if len(cite) < 5 or "fake" in cite.lower():
                fake_count += 1
                
        penalty = fake_count * 0.30
        return min(0.60, penalty)  # Capped at 0.60

    def score(self, completion: str, case: dict, turns: int = 1, panel_agreed: bool = False) -> float:
        """Computes the final composite reward for GRPO"""
        action = self.parse_action(completion)
        if not action:
            return -0.5 # Malformed output penalty
            
        acc = self.score_accuracy(action, case.get("gold_verdict", ""))
        neut = self.score_neutrality(action)
        reas = self.score_reasoning(action)
        cite = self.score_citation(action)
        
        # Efficiency: penalize long turn counts
        eff = max(0.0, 1.0 - (turns * 0.1))
        
        hallucination_penalty = self.calculate_hallucination_penalty(action)
        
        base_reward = (
            self.weights["accuracy"] * acc +
            self.weights["neutrality"] * neut +
            self.weights["reasoning"] * reas +
            self.weights["citation"] * cite +
            self.weights["efficiency"] * eff
        )
        
        final_reward = base_reward - hallucination_penalty
        
        if panel_agreed:
            final_reward += 0.15
            
        return max(0.001, min(0.999, final_reward)) # Clamp for stability
