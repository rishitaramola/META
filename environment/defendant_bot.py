class DefendantBot:
    """
    Simulated Defendant Agent for adversarial training.
    Argues AGAINST conviction/liability based on case facts.
    """
    def __init__(self, defensiveness=0.8):
        self.defensiveness = defensiveness

    def generate_argument(self, case_facts: str, plaintiff_argument: str, round_number: int) -> str:
        """
        In a real LLM setup, this would prompt a smaller LLM to argue the defendant's side.
        For hackathon demo purposes, this uses heuristic generation.
        """
        if "removed me from my job" in case_facts.lower() or "terminate" in case_facts.lower():
            return "The termination was strictly due to poor performance and within the bounds of the employment contract. The plaintiff is misrepresenting the facts. We deny all claims of unlawful dismissal."
            
        if "contract" in case_facts.lower() or "payment" in case_facts.lower():
            return "We deny liability. The plaintiff failed to fulfill their obligations first, which constitutes a prior breach. Any damages claimed are remote and unforeseeable."
            
        if "injury" in case_facts.lower() or "accident" in case_facts.lower():
            return "The plaintiff was contributorily negligent. We took all reasonable precautions, and the incident was an unforeseeable accident. We cannot be held strictly liable."
            
        return "We deny all allegations made by the plaintiff. The evidence is circumstantial and insufficient to establish liability under the law."
