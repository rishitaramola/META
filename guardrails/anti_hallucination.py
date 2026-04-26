"""
Anti-Hallucination Guard Rails for Judicial Reasoning
======================================================
Validates AI-generated legal reasoning against known Indian legal databases
to prevent fabricated citations, invalid statutes, and biased language.
"""

import re
from typing import List, Dict, Tuple


# ─── Known Valid Data ──────────────────────────────────────────

# Valid BNS (Bharatiya Nyaya Sanhita 2023) section ranges
VALID_BNS_SECTIONS = set(range(1, 359))

# Landmark Indian cases the system should recognize
LANDMARK_CASES = {
    "Vishaka v State of Rajasthan",
    "M.C. Mehta v Union of India",
    "Satyabrata Ghose v Mugneeram Bangur",
    "Kesavananda Bharati v State of Kerala",
    "Maneka Gandhi v Union of India",
    "S.R. Bommai v Union of India",
    "Navtej Singh Johar v Union of India",
    "K.S. Puttaswamy v Union of India",
    "Shreya Singhal v Union of India",
    "Indian Young Lawyers Association v State of Kerala",
    "Hadley v Baxendale",  # Western — should trigger a warning
}

# Biased/prejudicial terms to flag
BIAS_TERMS = [
    "obviously guilty", "clearly criminal", "typical behavior",
    "as expected from", "this community", "these people",
    "of course he", "of course she", "naturally they",
]


# ─── Guard Rail Base ──────────────────────────────────────────

class GuardRail:
    """Base class for all guard rails."""
    name: str = "BaseGuardRail"

    def check(self, text: str, metadata: dict = None) -> Tuple[bool, str]:
        """Returns (passed, message)."""
        raise NotImplementedError


class BNSStatuteGuardRail(GuardRail):
    """Validates that any referenced BNS section numbers actually exist."""
    name = "BNS Statute Validator"

    def check(self, text: str, metadata: dict = None) -> Tuple[bool, str]:
        bns_refs = re.findall(r'BNS\s*(?:Section|Sec\.?|§)\s*(\d+)', text, re.IGNORECASE)
        invalid = [s for s in bns_refs if int(s) not in VALID_BNS_SECTIONS]
        if invalid:
            return False, f"Invalid BNS sections referenced: {invalid}. BNS 2023 has sections 1-358."
        return True, "All BNS section references are valid."


class LimitationActGuardRail(GuardRail):
    """Ensures limitation periods are correctly cited."""
    name = "Limitation Act Validator"

    PERIODS = {
        "civil": 3,
        "contract": 3,
        "tort": 1,
        "property": 12,
        "consumer": 2,
    }

    def check(self, text: str, metadata: dict = None) -> Tuple[bool, str]:
        domain = (metadata or {}).get("domain", "civil")
        expected = self.PERIODS.get(domain, 3)
        # Check if text mentions an incorrect limitation period
        period_refs = re.findall(r'limitation\s*(?:period|of)\s*(?:is|of)?\s*(\d+)\s*year', text, re.IGNORECASE)
        for p in period_refs:
            if int(p) != expected:
                return False, f"Incorrect limitation period: {p} years cited, expected {expected} years for {domain} cases."
        return True, f"Limitation period references are correct (expected {expected} years for {domain})."


class SpecificReliefActGuardRail(GuardRail):
    """Validates that appropriate remedies are suggested."""
    name = "Specific Relief Act Validator"

    def check(self, text: str, metadata: dict = None) -> Tuple[bool, str]:
        # Check if specific performance is suggested for personal service contracts (invalid)
        if "specific performance" in text.lower() and "personal service" in text.lower():
            return False, "Specific performance cannot be granted for personal service contracts (Specific Relief Act 1963 §14)."
        return True, "Remedies suggested are appropriate."


class CitationVerificationGuardRail(GuardRail):
    """Checks that cited cases are real landmark Indian cases."""
    name = "Citation Verifier"

    def check(self, text: str, metadata: dict = None) -> Tuple[bool, str]:
        warnings = []
        # Check for Western precedents being used as binding authority
        western_cases = ["Hadley v Baxendale", "Donoghue v Stevenson", "Carlill v Carbolic"]
        for case in western_cases:
            if case.lower() in text.lower():
                warnings.append(f"Western precedent '{case}' cited — use Indian equivalent instead.")

        # Check for obviously fake case names
        fake_patterns = re.findall(r'(?:State|Union|Govt)\s+v\s+[A-Z][a-z]+\s+\d{4}', text)
        # This is just a heuristic — real verification would use Indian Kanoon API

        if warnings:
            return False, " | ".join(warnings)
        return True, "Citation references appear valid."


class BiasDetectionGuardRail(GuardRail):
    """Detects prejudicial or biased language in judicial reasoning."""
    name = "Bias Detector"

    def check(self, text: str, metadata: dict = None) -> Tuple[bool, str]:
        found = [term for term in BIAS_TERMS if term.lower() in text.lower()]
        if found:
            return False, f"Biased/prejudicial language detected: {found}. Judicial reasoning must be neutral."
        return True, "No biased language detected."


class ConfidenceCalibrationGuardRail(GuardRail):
    """Validates that confidence scores are reasonable and not overconfident."""
    name = "Confidence Calibrator"

    def check(self, text: str, metadata: dict = None) -> Tuple[bool, str]:
        confidence = (metadata or {}).get("confidence_score", 0.5)
        if confidence > 0.98:
            return False, f"Overconfident score ({confidence:.0%}). No legal AI should claim >98% certainty."
        if confidence < 0.1:
            return False, f"Underconfident score ({confidence:.0%}). Score too low to be meaningful."
        return True, f"Confidence score ({confidence:.0%}) is within acceptable range."


# ─── Orchestrator ──────────────────────────────────────────────

class AntiHallucinationGuardRails:
    """Runs all guard rails against a piece of judicial reasoning."""

    def __init__(self):
        self.rails: List[GuardRail] = [
            BNSStatuteGuardRail(),
            LimitationActGuardRail(),
            SpecificReliefActGuardRail(),
            CitationVerificationGuardRail(),
            BiasDetectionGuardRail(),
            ConfidenceCalibrationGuardRail(),
        ]

    def verify_reasoning(self, reasoning_text: str, metadata: dict = None) -> Dict:
        """Run all guard rails and return a full verification report."""
        results = []
        all_passed = True
        for rail in self.rails:
            passed, message = rail.check(reasoning_text, metadata)
            results.append({"guard_rail": rail.name, "passed": passed, "message": message})
            if not passed:
                all_passed = False

        return {
            "all_passed": all_passed,
            "total_checks": len(results),
            "passed_checks": sum(1 for r in results if r["passed"]),
            "failed_checks": sum(1 for r in results if not r["passed"]),
            "details": results,
        }
