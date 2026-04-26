import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_utils import init_db, seed_from_json, load_case, list_cases
from debate.debate_orchestrator import DebateOrchestrator

def main():
    parser = argparse.ArgumentParser(description="Run a Judicial Debate simulation via CLI")
    parser.add_argument("--case", type=int, help="Case ID from the database", default=1)
    parser.add_argument("--rounds", type=int, help="Number of debate rounds", default=2)
    parser.add_argument("--list", action="store_true", help="List all available cases")
    args = parser.parse_args()

    # Initialize DB if needed
    if not os.path.exists("database/cases.db"):
        print("Initializing database...")
        init_db()
        seed_from_json()
        
    if args.list:
        cases = list_cases()
        print("Available Cases:")
        for c in cases:
            print(f"[{c['id']}] {c['title']} (Domain: {c['domain']})")
        return

    case = load_case(args.case)
    if not case:
        print(f"Error: Case {args.case} not found.")
        return

    print("="*60)
    print("JUDICIAL DEBATE ARENA")
    print(f"Case: {case['title']}")
    print(f"Domain: {case['domain']}")
    print(f"Difficulty: {case['difficulty']}")
    print("="*60)
    print(f"Facts: {case.get('facts', 'No facts provided')}")
    print("="*60)
    
    def progress_callback(msg):
        print(f"\n[SYSTEM] {msg}")

    orchestrator = DebateOrchestrator(case, num_rounds=args.rounds)
    result = orchestrator.run_debate(progress_callback=progress_callback)
    
    print("\n" + "="*60)
    print("DEBATE TRANSCRIPT")
    print("="*60)
    for msg in result["transcript"]:
        print(f"\n--- Round {msg['round']} | {msg['role']} ---")
        print(msg['content'])
        if msg.get('citations'):
            print(f"Citations: {', '.join(msg['citations'])}")

    print("\n" + "="*60)
    print("FINAL VERDICT")
    print("="*60)
    verdict = result["verdict"]
    print(f"Verdict: {verdict.get('verdict', 'Unknown').upper()}")
    print(f"Confidence: {verdict.get('confidence_score', 0):.0%}")
    print(f"Ratio Decidendi: {verdict.get('ratio_decidendi', 'N/A')}")
    print(f"\nReasoning:\n{verdict.get('reasoning_chain', 'N/A')}")
    
    print("\n" + "="*60)
    print("LLM-AS-JUDGE EVALUATION")
    print("="*60)
    eval_data = result["evaluation"]
    print(f"Overall Score: {eval_data.get('overall_score', 0)}/100")
    print(f"Summary: {eval_data.get('evaluation_summary', 'N/A')}")
    print("\nScores:")
    for k, v in eval_data.get("scores", {}).items():
        print(f"  {k}: {v}/10")
        
    print(f"\nHallucinations: {eval_data.get('hallucination_count', 0)}")
    
    # Save to DB
    try:
        from database.db_utils import save_debate
        save_debate(args.case, result["transcript"], verdict, eval_data)
        print("\n[SYSTEM] Debate saved to database successfully.")
    except Exception as e:
        print(f"\n[SYSTEM] Failed to save debate to database: {e}")

if __name__ == "__main__":
    main()
