import json
import re
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.multi_agent_system import GroqAPIClient
from debate.prompts import JUDGE_EVALUATION_PROMPT

class DebateEvaluator:
    def __init__(self, transcript: List[Dict], case_facts: str, gold_verdict: str = None, client: GroqAPIClient = None):
        self.transcript = transcript
        self.case_facts = case_facts
        self.gold_verdict = gold_verdict
        self.client = client or GroqAPIClient()
        self.eval_model = "llama-3.3-70b-versatile"

    def evaluate(self) -> Dict:
        """
        Uses LLM-as-Judge to score the debate on multiple dimensions.
        Falls back to rule-based evaluation if the API fails.
        """
        transcript_str = json.dumps(self.transcript, ensure_ascii=False, indent=2)
        
        prompt = JUDGE_EVALUATION_PROMPT.format(
            case_facts=self.case_facts,
            transcript=transcript_str
        )
        
        try:
            # We enforce JSON response format
            raw_output = self.client.generate(prompt, self.eval_model, max_tokens=1500)
            raw_output = re.sub(r'<think>.*?</think>', '', raw_output, flags=re.DOTALL).strip()
            raw_output = raw_output.replace("```json", "").replace("```", "").strip()
            m = re.search(r'\{.*\}', raw_output, re.DOTALL)
            
            eval_data = json.loads(m.group(0) if m else raw_output)
            
            # Compute overall score if missing or 0
            if "overall_score" not in eval_data or eval_data.get("overall_score") == 0:
                s = eval_data.get("scores", {})
                eval_data["overall_score"] = round(
                    0.30 * s.get("legal_accuracy", 0) + 
                    0.25 * s.get("irac_quality", 0) + 
                    0.15 * s.get("factual_grounding", 0) + 
                    0.15 * s.get("rebuttal_effectiveness", 0) + 
                    0.10 * s.get("persuasiveness", 0) + 
                    0.05 * s.get("professionalism", 0), 
                2) * 10 # scale to 100
                
            return eval_data
            
        except Exception as e:
            print(f"LLM-as-Judge evaluation failed: {e}. Falling back to rule-based evaluation.")
            return self._rule_based_fallback()

    def _rule_based_fallback(self) -> Dict:
        """Simple heuristic fallback if LLM evaluation fails."""
        
        plaintiff_args = [m["content"] for m in self.transcript if m["role"] == "Plaintiff"]
        defendant_args = [m["content"] for m in self.transcript if m["role"] == "Defendant"]
        
        all_text = " ".join(plaintiff_args + defendant_args).lower()
        
        # Check for IRAC keywords
        irac_score = 5.0
        if "issue" in all_text: irac_score += 1.0
        if "rule" in all_text or "section" in all_text or "act" in all_text: irac_score += 1.0
        if "apply" in all_text or "application" in all_text or "because" in all_text: irac_score += 1.0
        if "conclude" in all_text or "conclusion" in all_text or "therefore" in all_text: irac_score += 1.0
        if "held" in all_text or "liable" in all_text: irac_score += 1.0
        
        # Check citations
        citations = []
        for msg in self.transcript:
            citations.extend(msg.get("citations", []))
            
        has_bns = any("bns" in c.lower() or "bharatiya nyaya" in c.lower() for c in citations)
        has_const = any("article" in c.lower() or "constitution" in c.lower() for c in citations)
        
        legal_accuracy = 6.0
        if has_bns: legal_accuracy += 2.0
        if has_const: legal_accuracy += 1.0
        if len(citations) > 3: legal_accuracy += 1.0
        
        overall = round((legal_accuracy * 0.3 + irac_score * 0.25 + 7.0 * 0.45) * 10, 2)
        
        return {
            "evaluation_summary": "Rule-based fallback evaluation due to LLM error.",
            "scores": {
                "legal_accuracy": legal_accuracy,
                "irac_quality": irac_score,
                "factual_grounding": 7.0,
                "rebuttal_effectiveness": 7.0,
                "persuasiveness": 7.0,
                "professionalism": 8.0,
                "judge_neutrality": 8.0,
                "judge_synthesis": 8.0
            },
            "overall_score": overall,
            "hallucination_count": 0,
            "hallucinated_items": [],
            "verdict_assessment": {
                "supported_outcome": "Unknown (Rule-based)",
                "justification_strength": 7.0,
                "alignment_with_law": 7.0
            },
            "strengths": ["Basic structure identified"],
            "weaknesses": ["Deep analysis missing due to API fallback"],
            "recommended_improvements": "Ensure API key is configured for LLM-as-Judge.",
            "metadata": {
                "transcript_length": len(self.transcript)
            }
        }
