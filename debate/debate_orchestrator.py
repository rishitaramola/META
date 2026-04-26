import json
from typing import Dict, List
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.multi_agent_system import GroqAPIClient
from debate.agents import PlaintiffAdvocate, DefendantAdvocate, DebateJudge
from debate.evaluation import DebateEvaluator

class DebateOrchestrator:
    def __init__(self, case: Dict, num_rounds: int = 3):
        self.case = case
        self.rounds = num_rounds
        self.transcript = []
        
        # Initialize Groq client
        self.client = GroqAPIClient()
        
        # Initialize agents
        self.plaintiff = PlaintiffAdvocate(self.client)
        self.defendant = DefendantAdvocate(self.client)
        self.judge = DebateJudge(self.client)

    def add_message(self, round_num: int, role: str, content: str, citations: List[str] = None):
        self.transcript.append({
            "round": round_num,
            "role": role,
            "content": content,
            "citations": citations or []
        })

    def run_debate(self, progress_callback=None) -> Dict:
        """Runs the full debate loop."""
        
        case_facts = self.case.get("facts", self.case.get("fact_pattern", ""))
        
        for r in range(1, self.rounds + 1):
            if progress_callback:
                progress_callback(f"Starting Round {r}: Plaintiff's turn...")
                
            # Plaintiff Turn
            p_response = self.plaintiff.generate_response(case_facts, self.transcript)
            p_arg = p_response.get("argument", "No argument provided.")
            p_citations = p_response.get("cited_statutes", [])
            self.add_message(r, "Plaintiff", p_arg, p_citations)
            
            if progress_callback:
                progress_callback(f"Starting Round {r}: Defendant's turn...")
                
            # Defendant Turn
            d_response = self.defendant.generate_response(case_facts, self.transcript)
            d_arg = d_response.get("argument", "No argument provided.")
            d_citations = d_response.get("cited_statutes", [])
            self.add_message(r, "Defendant", d_arg, d_citations)

        # Judge Deliberation
        if progress_callback:
            progress_callback("Judge is deliberating...")
            
        verdict = self.judge.synthesize_verdict(case_facts, self.transcript)
        
        # Evaluation
        if progress_callback:
            progress_callback("Evaluating debate quality...")
            
        evaluator = DebateEvaluator(self.transcript, case_facts, self.case.get("gold_verdict"), self.client)
        evaluation = evaluator.evaluate()

        return {
            "transcript": self.transcript,
            "verdict": verdict,
            "evaluation": evaluation,
            "overall_score": evaluation.get("overall_score", 0)
        }
