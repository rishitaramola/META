import json
import re
from typing import Dict, List, Optional
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.multi_agent_system import GroqAPIClient
from debate.prompts import PLAINTIFF_SYSTEM_PROMPT, DEFENDANT_SYSTEM_PROMPT, JUDGE_SYSTEM_PROMPT

class DebateAgent:
    def __init__(self, role: str, model: str, system_prompt: str, client: GroqAPIClient):
        self.role = role
        self.model = model
        self.system_prompt = system_prompt
        self.client = client

    def generate_response(self, case_facts: str, transcript: List[Dict]) -> Dict:
        # Format the transcript for the LLM
        transcript_text = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in transcript])
        
        prompt = f"""{self.system_prompt}

CASE FACTS:
{case_facts}

DEBATE TRANSCRIPT SO FAR:
{transcript_text if transcript_text else "This is the opening round."}

Based on the facts and the transcript, provide your next argument.
"""
        
        try:
            # We want JSON output as per the prompts
            raw = self.client.generate(prompt, self.model, max_tokens=1000)
            # Clean reasoning models (like deepseek-r1)
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            data = json.loads(m.group(0) if m else raw)
            return data
        except Exception as e:
            print(f"Error generating response for {self.role}: {e}")
            return {
                "argument": f"[{self.role} could not formulate an argument due to an error.]",
                "cited_statutes": [],
                "confidence": 0.5
            }

class PlaintiffAdvocate(DebateAgent):
    def __init__(self, client: GroqAPIClient):
        # Llama 3.3 70b is good for structured argumentation
        super().__init__(
            role="Plaintiff", 
            model="llama-3.3-70b-versatile", 
            system_prompt=PLAINTIFF_SYSTEM_PROMPT, 
            client=client
        )

class DefendantAdvocate(DebateAgent):
    def __init__(self, client: GroqAPIClient):
        # Mixtral for different perspective/style
        super().__init__(
            role="Defendant", 
            model="mixtral-8x7b-32768", 
            system_prompt=DEFENDANT_SYSTEM_PROMPT, 
            client=client
        )

class DebateJudge(DebateAgent):
    def __init__(self, client: GroqAPIClient):
        # High reasoning model for final verdict synthesis
        super().__init__(
            role="Judge", 
            model="llama-3.3-70b-versatile", 
            system_prompt=JUDGE_SYSTEM_PROMPT, 
            client=client
        )
        
    def synthesize_verdict(self, case_facts: str, transcript: List[Dict]) -> Dict:
        # Format the transcript for the LLM
        transcript_text = "\n\n".join([f"{msg['role']} (Round {msg['round']}): {msg['content']}" for msg in transcript])
        
        prompt = f"""{self.system_prompt}

CASE FACTS:
{case_facts}

FULL DEBATE TRANSCRIPT:
{transcript_text}

Provide your final synthesized verdict based on the arguments presented.
"""
        try:
            raw = self.client.generate(prompt, self.model, max_tokens=1500)
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            data = json.loads(m.group(0) if m else raw)
            return data
        except Exception as e:
            print(f"Error generating verdict for Judge: {e}")
            return {
                "verdict": "Mixed",
                "reasoning_chain": "The judge could not synthesize a verdict due to an error.",
                "cited_precedents": [],
                "confidence_score": 0.5,
                "ratio_decidendi": "Unknown",
                "obiter_dicta": "Error during synthesis."
            }
