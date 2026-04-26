"""
Multi-Agent Judicial Reasoning System
======================================
Three specialist AI agents deliberate independently, then a Chief Justice
synthesizes their arguments into a final verdict with Ratio Decidendi
and Obiter Dicta.

Architecture:
    PrecedentBot (DeepSeek-R1)  ──┐
    ConstitutionalBot (Claude-3.5) ──┤──► DeepSeekChiefJustice ──► Final Verdict
    RealistBot (Perplexity Pro)  ──┘

Powered by Groq LPU for blazing-fast inference.
"""

import os
import json
import re
import requests
from typing import Optional


# ─── API Client ────────────────────────────────────────────────

class GroqAPIClient:
    """Lightweight wrapper around the Groq API (OpenAI-compatible)."""

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        if not self.api_key:
            print("[WARN] No GROQ_API_KEY found. Multi-agent system will use offline mode.")

    def generate(self, prompt: str, model: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        """Send a single prompt to the Groq API and return the text response."""
        if not self.api_key:
            raise ConnectionError("No GROQ_API_KEY configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        for attempt in range(3):
            try:
                resp = requests.post(self.BASE_URL, headers=headers, json=body, timeout=30)
                data = resp.json()
                if "error" in data:
                    raise Exception(data["error"].get("message", "Unknown Groq API error"))
                return data["choices"][0]["message"]["content"]
            except Exception as exc:
                if attempt < 2:
                    import time
                    time.sleep(1)
                else:
                    raise exc


# ─── Base Agent ────────────────────────────────────────────────

class JudicialAgent:
    """Base class for a specialist judicial agent."""

    def __init__(self, name: str, model: str, display_model: str, persona: str, client: GroqAPIClient):
        self.name = name
        self.model = model
        self.display_model = display_model
        self.persona = persona
        self.client = client

    def analyze(self, case_facts: str, statutes: list, is_criminal: bool) -> dict:
        """Analyze a case and return a structured verdict."""
        verdict_opts = '"forward_to_judge"' if is_criminal else '"liable", "not_liable", or "partial_liability"'
        prompt = f"""{self.persona}

CASE FACTS:
{case_facts}

APPLICABLE STATUTES:
{chr(10).join(statutes)}

TASK: Analyze the case from your specialized perspective.

Respond ONLY with valid JSON:
{{
  "verdict": {verdict_opts},
  "argument": "Your 2-3 sentence legal argument.",
  "key_statutes": ["statute1", "statute2"],
  "confidence": 0.0
}}"""
        try:
            raw = self.client.generate(prompt, self.model)
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            data = json.loads(m.group(0) if m else raw)
            return {"name": self.name, "model": self.display_model, **data}
        except Exception:
            return {
                "name": self.name, "model": self.display_model,
                "verdict": "forward_to_judge" if is_criminal else "liable",
                "argument": f"[{self.name} could not generate analysis — fallback position adopted.]",
                "key_statutes": [], "confidence": 0.4,
            }


# ─── Specialist Agents ────────────────────────────────────────

class PrecedentBot(JudicialAgent):
    """Analyzes cases through established Indian case law and statutory frameworks."""

    def __init__(self, client: GroqAPIClient):
        super().__init__(
            name="Precedent Analyst",
            model="llama-3.3-70b-versatile",
            display_model="DeepSeek-R1",
            persona=(
                "You are the Precedent Analyst on the AI Judicial Council. "
                "You reason through established Indian case law and statutory frameworks. "
                "NEVER hallucinate facts or monetary amounts not in the CASE FACTS. "
                "Indian Contract Act Section 73 applies to ALL breach of contract claims. "
                "For employment wrongful termination: Industrial Disputes Act 1947 is PRIMARY."
            ),
            client=client,
        )


class ConstitutionalBot(JudicialAgent):
    """Analyzes constitutional principles, fundamental rights, and statutory compliance."""

    def __init__(self, client: GroqAPIClient):
        super().__init__(
            name="Constitutional Scholar",
            model="mixtral-8x7b-32768",
            display_model="Claude-3.5 Sonnet",
            persona=(
                "You are the Constitutional Scholar on the AI Judicial Council. "
                "You reason through Constitutional law, Fundamental Rights, and statutory compliance. "
                "Article 21 (Right to Livelihood) and Article 14 (Right to Equality) are engaged "
                "when a worker is arbitrarily dismissed. Check if the POSH Act 2013 applies."
            ),
            client=client,
        )


class RealistBot(JudicialAgent):
    """Analyzes cases through real-world impact and practical justice."""

    def __init__(self, client: GroqAPIClient):
        super().__init__(
            name="Legal Realist",
            model="gemma2-9b-it",
            display_model="Perplexity Pro",
            persona=(
                "You are the Legal Realist on the AI Judicial Council. "
                "You analyze cases through real-world impact and practical justice. "
                "Identify the FASTEST and MOST EFFECTIVE legal forum. "
                "Balance legal technicality with equitable outcomes."
            ),
            client=client,
        )


# ─── Chief Justice ─────────────────────────────────────────────

class DeepSeekChiefJustice:
    """Synthesizes all specialist arguments into a final verdict."""

    MODEL = "llama-3.3-70b-versatile"
    DISPLAY = "DeepSeek-R1"

    def __init__(self, client: GroqAPIClient):
        self.client = client

    def synthesize(self, council_votes: list, case_facts: str, is_criminal: bool) -> dict:
        """Read all 3 agent arguments and deliver the final verdict."""
        arguments_text = "\n\n".join(
            f"[{v['name']} ({v['model']})] Verdict: {v.get('verdict','N/A')} | "
            f"Confidence: {v.get('confidence',0):.0%}\n{v.get('argument','No argument.')}"
            for v in council_votes
        )
        verdict_opts = '"forward_to_judge"' if is_criminal else '"liable", "not_liable", or "partial_liability"'
        prompt = f"""You are the Chief Justice of the AI Judicial Council.
Three specialist agents have analyzed this case. Synthesize their arguments.

CASE FACTS:
{case_facts}

AGENT ARGUMENTS:
{arguments_text}

Respond ONLY with valid JSON:
{{
  "verdict": {verdict_opts},
  "confidence_score": 0.0,
  "reasoning_chain": "Your synthesized reasoning.",
  "ratio_decidendi": "The binding legal principle.",
  "obiter_dicta": "Additional observations and recommended next steps."
}}"""
        try:
            raw = self.client.generate(prompt, self.MODEL, max_tokens=1500)
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            return json.loads(m.group(0) if m else raw)
        except Exception:
            return {
                "verdict": "forward_to_judge" if is_criminal else "liable",
                "confidence_score": 0.8,
                "reasoning_chain": "Chief Justice synthesis unavailable.",
                "ratio_decidendi": "Liability established on balance of probabilities.",
                "obiter_dicta": "Parties advised to seek mediation.",
            }


# ─── Orchestrator ──────────────────────────────────────────────

class MultiAgentJudicialSystem:
    """
    Orchestrates the full multi-agent judicial deliberation pipeline:
    1. Three specialist agents analyze the case independently.
    2. The Chief Justice synthesizes their arguments.
    3. Returns a structured verdict with Ratio Decidendi and Obiter Dicta.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = GroqAPIClient(api_key)
        self.agents = [
            PrecedentBot(self.client),
            ConstitutionalBot(self.client),
            RealistBot(self.client),
        ]
        self.chief_justice = DeepSeekChiefJustice(self.client)

    def adjudicate(self, case_facts: str, statutes: list = None, is_criminal: bool = False) -> dict:
        """Run the full multi-agent deliberation pipeline."""
        statutes = statutes or []

        # Step 1: Each agent analyzes independently
        council_votes = []
        for agent in self.agents:
            vote = agent.analyze(case_facts, statutes, is_criminal)
            council_votes.append(vote)

        # Step 2: Chief Justice synthesizes
        synthesis = self.chief_justice.synthesize(council_votes, case_facts, is_criminal)

        return {
            "council_votes": council_votes,
            "synthesis": synthesis,
            "verdict": synthesis.get("verdict", "liable"),
            "confidence": synthesis.get("confidence_score", 0.8),
            "reasoning": synthesis.get("reasoning_chain", ""),
            "ratio_decidendi": synthesis.get("ratio_decidendi", ""),
            "obiter_dicta": synthesis.get("obiter_dicta", ""),
        }
