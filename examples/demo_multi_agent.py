"""
Demo: Multi-Agent Judicial Reasoning System
=============================================
Run this script to see the full pipeline in action:
  1. Three specialist agents analyze a case
  2. Anti-hallucination guardrails validate the reasoning
  3. Verification links are auto-generated
  4. Chief Justice delivers the final verdict

Usage:
    export GROQ_API_KEY=your_key_here
    python examples/demo_multi_agent.py
"""

import json
import sys
import os

# Add parent dir to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.multi_agent_system import MultiAgentJudicialSystem
from guardrails.anti_hallucination import AntiHallucinationGuardRails
from database_integration.verification_links import LiveVerificationLinksGenerator


def main():
    print("=" * 60)
    print("⚖️  JUSTICE AI — Multi-Agent Judicial Reasoning Demo")
    print("=" * 60)

    # ── Sample Case ──────────────────────────────────────────
    case_facts = (
        "I was admitted to City General Hospital on March 12, 2026, "
        "for a routine appendectomy performed by Dr. Vikrant Mehta. "
        "Post-surgery, I complained of severe abdominal pain and fever. "
        "An examination at another facility revealed that a surgical sponge "
        "had been left inside the abdominal cavity. This negligence led to "
        "a severe infection and required an emergency corrective surgery."
    )
    statutes = [
        "Consumer Protection Act 2019",
        "Indian Medical Council Regulations 2002",
        "BNS Section 125 (Grievous Hurt by Negligence)",
        "Law of Torts — Duty of Care (Bolam Test)",
    ]

    # ── Step 1: Multi-Agent Deliberation ─────────────────────
    print("\n🏛️  Convening the AI Judicial Council...\n")
    system = MultiAgentJudicialSystem()

    try:
        result = system.adjudicate(case_facts, statutes, is_criminal=False)
    except Exception as e:
        print(f"❌ API Error: {e}")
        print("   Make sure GROQ_API_KEY is set in your environment.")
        return

    print("─" * 60)
    for vote in result["council_votes"]:
        print(f"  🧑‍⚖️ {vote['name']} ({vote['model']})")
        print(f"     Verdict: {vote.get('verdict', 'N/A')}")
        print(f"     Confidence: {vote.get('confidence', 0):.0%}")
        print(f"     Argument: {vote.get('argument', 'N/A')[:120]}...")
        print()

    print("─" * 60)
    print(f"  👨‍⚖️ CHIEF JUSTICE SYNTHESIS")
    print(f"     Final Verdict: {result['verdict']}")
    print(f"     Confidence: {result['confidence']:.0%}")
    print(f"     Ratio Decidendi: {result['ratio_decidendi'][:150]}...")
    print(f"     Obiter Dicta: {result['obiter_dicta'][:150]}...")
    print()

    # ── Step 2: Anti-Hallucination Check ─────────────────────
    print("🛡️  Running Anti-Hallucination Guard Rails...\n")
    guard_rails = AntiHallucinationGuardRails()
    verification = guard_rails.verify_reasoning(
        result["reasoning"],
        {"confidence_score": result["confidence"], "domain": "tort"},
    )

    for detail in verification["details"]:
        status = "✅" if detail["passed"] else "❌"
        print(f"  {status} {detail['guard_rail']}: {detail['message']}")

    print(f"\n  Result: {verification['passed_checks']}/{verification['total_checks']} checks passed.")

    # ── Step 3: Verification Links ───────────────────────────
    print("\n🔗  Generating Verification Links...\n")
    links_gen = LiveVerificationLinksGenerator()
    links = links_gen.generate_links_for_verdict(
        result["reasoning"],
        cited_authorities=["Vishaka v State of Rajasthan", "M.C. Mehta v Union of India"],
        applicable_statutes=statutes,
    )
    print(f"  Generated {links['total_links']} verification links.")
    print(f"  General search: {links['general_search']}")

    print("\n" + "=" * 60)
    print("✅ Demo complete. The AI Judicial Council has deliberated.")
    print("=" * 60)


if __name__ == "__main__":
    main()
