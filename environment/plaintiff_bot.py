class PlaintiffBot:
    """
    Simulated Plaintiff Agent for adversarial training.
    Argues FOR conviction/liability based on case facts.
    """
    def __init__(self, aggressiveness=0.8):
        self.aggressiveness = aggressiveness

    def generate_argument(self, case_facts: str, round_number: int) -> str:
        """
        In a real LLM setup, this would prompt a smaller LLM to argue the plaintiff's side.
        For hackathon demo purposes, this uses heuristic generation.
        """
        if "removed me from my job" in case_facts.lower() or "terminate" in case_facts.lower():
            return "The defendant explicitly breached employment law (Industrial Disputes Act 1947). The termination was unlawful, arbitrary, and caused significant financial distress. We demand full reinstatement and back wages."
            
        if "contract" in case_facts.lower() or "payment" in case_facts.lower():
            return "The facts clearly demonstrate a breach of contract by the defendant. We have suffered actual damages and are entitled to compensation under Section 73 of the Indian Contract Act."
            
        if "injury" in case_facts.lower() or "accident" in case_facts.lower():
            return "The defendant was negligent. Their actions directly caused harm to my client, making them strictly liable for all medical expenses and trauma."
            
        return "The facts provided establish a clear prima facie case against the defendant. They have failed in their legal duties and must be held fully liable."
