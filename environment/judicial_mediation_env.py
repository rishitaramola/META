import json

class JudicialMediationEnv:
    """
    OpenEnv-style Multi-Agent environment for Judicial Mediation.
    Supports multi-turn deliberation:
      1. Plaintiff argues
      2. Defendant argues
      3. Judge decides
    """
    def __init__(self, domain="contract", difficulty="easy"):
        self.domain = domain
        self.difficulty = difficulty
        self.current_step = 0
        self.max_steps = 4
        self.current_case = None
        self.plaintiff_args = ""
        self.defendant_args = ""
    
    def reset(self, case_dict=None):
        """Initialize a new mediation session."""
        self.current_step = 0
        if case_dict:
            self.current_case = case_dict
        else:
            self.current_case = {
                "fact_pattern": "A standard contract dispute over non-payment of Rs 50,000.",
                "domain": self.domain,
                "statutes_applicable": ["Indian Contract Act 1872 Section 73"]
            }
        
        # Reset arguments
        self.plaintiff_args = ""
        self.defendant_args = ""
        
        return self._get_observation()
        
    def _get_observation(self):
        """Returns the current state to the Judge Agent."""
        return {
            "case_facts": self.current_case["fact_pattern"],
            "statutes": self.current_case.get("statutes_applicable", []),
            "plaintiff_argument": self.plaintiff_args,
            "defendant_argument": self.defendant_args,
            "turn": self.current_step
        }
        
    def step(self, action: str):
        """
        The Judge takes an action. 
        In multi-turn, actions could be "request_arguments" or a final JSON verdict.
        """
        self.current_step += 1
        
        # Mocking the bot responses for now. In a full run, this calls the actual bots.
        if self.current_step == 1:
            self.plaintiff_args = "The defendant explicitly breached the contract and owes damages."
            reward = 0.0
            done = False
            
        elif self.current_step == 2:
            self.defendant_args = "We deny liability due to force majeure."
            reward = 0.0
            done = False
            
        else:
            # Final turn: Evaluate Judge's verdict
            from reward.rubric import JudicialRubric
            rubric = JudicialRubric()
            
            reward = rubric.score(action, self.current_case, turns=self.current_step)
            done = True
            
        info = {
            "plaintiff_args": self.plaintiff_args,
            "defendant_args": self.defendant_args
        }
            
        return self._get_observation(), reward, done, False, info
