import json
import random
import os
from typing import List, Optional
from pydantic import BaseModel

class JudicialObservation(BaseModel):
    case_id: str
    fact_pattern: str
    statutes: List[str]
    precedents: List[dict]
    evidence_flags: List[str]
    domain: str
    difficulty: str

class JudicialAction(BaseModel):
    verdict: str
    confidence_score: float
    reasoning_chain: str
    cited_precedents: List[str]

class JudicialReward(BaseModel):
    logic_score: float
    accuracy_score: float
    fairness_score: float
    citation_score: float
    composite: float

class JudicialEnv:
    def __init__(self, domain: str = None, difficulty: str = None):
        self.domain = domain
        self.difficulty = difficulty
        self.current_case = None
        self.verdict_history = []
        self.done = False
        self._load_cases()

    def _load_cases(self):
        data_path = os.path.join(os.path.dirname(__file__), "data", "cases.json")
        with open(data_path, "r") as f:
            all_cases = json.load(f)
        self.cases = [
            c for c in all_cases
            if (self.domain is None or c["domain"] == self.domain)
            and (self.difficulty is None or c["difficulty"] == self.difficulty)
        ]

    def reset(self) -> JudicialObservation:
        self.done = False
        self.current_case = random.choice(self.cases)
        return JudicialObservation(
            case_id=self.current_case["case_id"],
            fact_pattern=self.current_case["fact_pattern"],
            statutes=self.current_case["applicable_statutes"],
            precedents=self.current_case["precedents"],
            evidence_flags=self.current_case["evidence_flags"],
            domain=self.current_case["domain"],
            difficulty=self.current_case["difficulty"]
        )

    def step(self, action: JudicialAction):
        if self.done:
            raise RuntimeError("Episode done. Call reset().")

        reward = self._compute_reward(action)
        self.verdict_history.append({
            "case_id": self.current_case["case_id"],
            "verdict": action.verdict
        })
        self.done = True

        info = {
            "logic_score": reward.logic_score,
            "accuracy_score": reward.accuracy_score,
            "fairness_score": reward.fairness_score,
            "citation_score": reward.citation_score,
            "composite_reward": reward.composite
        }

        return self.reset(), reward.composite, self.done, info

    def state(self) -> dict:
        return {
            "current_case_id": self.current_case["case_id"] if self.current_case else None,
            "done": self.done,
            "verdict_history_length": len(self.verdict_history)
        }

    def _compute_reward(self, action: JudicialAction) -> JudicialReward:
        accuracy = self._accuracy_score(action)
        citation = self._citation_score(action)
        fairness = self._fairness_score(action)
        logic = min(action.confidence_score, 1.0) * 0.8 + (0.2 if len(action.reasoning_chain) > 100 else 0.0)

        # Penalize hallucinated precedents
        valid_ids = [p["case_id"] for p in self.current_case["precedents"]]
        hallucination_penalty = 0.0
        for cited in action.cited_precedents:
            if cited not in valid_ids:
                hallucination_penalty += 0.2
        hallucination_penalty = min(hallucination_penalty, 0.4)

        composite = (0.3 * logic + 0.4 * accuracy + 0.2 * fairness + 0.1 * citation) - hallucination_penalty
        composite = max(0.0, min(1.0, composite))

        return JudicialReward(
            logic_score=round(logic, 4),
            accuracy_score=round(accuracy, 4),
            fairness_score=round(fairness, 4),
            citation_score=round(citation, 4),
            composite=round(composite, 4)
        )

    def _accuracy_score(self, action: JudicialAction) -> float:
        gold = self.current_case["gold_label_verdict"]
        return 1.0 if action.verdict == gold else 0.0

    def _citation_score(self, action: JudicialAction) -> float:
        valid_ids = [p["case_id"] for p in self.current_case["precedents"]]
        if not action.cited_precedents:
            return 0.0
        hits = sum(1 for c in action.cited_precedents if c in valid_ids)
        return round(hits / max(len(action.cited_precedents), 1), 4)

    def _fairness_score(self, action: JudicialAction) -> float:
        same_domain = [v for v in self.verdict_history if v["case_id"].startswith(self.current_case["case_id"][0])]
        if len(same_domain) < 2:
            return 1.0
        verdicts = [v["verdict"] for v in same_domain]
        consistency = verdicts.count(verdicts[0]) / len(verdicts)
        return round(consistency, 4)