import sqlite3
import json
import os
from pathlib import Path

# Setup paths
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "cases.db"
SCHEMA_PATH = DB_DIR / "schema.sql"
CASES_JSON_PATH = DB_DIR.parent / "data" / "cases.json"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with the schema."""
    conn = get_db_connection()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def seed_from_json():
    """Populate cases table from data/cases.json if empty."""
    if not CASES_JSON_PATH.exists():
        print(f"Warning: {CASES_JSON_PATH} not found. Cannot seed database.")
        return

    conn = get_db_connection()
    # Check if cases already exist
    count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    if count > 0:
        print(f"Database already contains {count} cases. Skipping seed.")
        conn.close()
        return

    with open(CASES_JSON_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    inserted = 0
    for c in cases:
        # Handle old and new formats
        title = c.get("title", f"Case {c.get('case_id', 'Unknown')}")
        facts = c.get("fact_pattern", c.get("facts", ""))
        domain = c.get("domain", "")
        difficulty = c.get("difficulty", "")
        
        statutes = c.get("applicable_statutes", c.get("statutes_applicable", []))
        precedents = c.get("precedents", c.get("key_precedents", []))
        
        gold_verdict = c.get("gold_label_verdict", c.get("gold_verdict", c.get("expert_verdict", "")))
        evidence = c.get("evidence_flags", [])

        conn.execute("""
            INSERT INTO cases (title, facts, domain, applicable_statutes, key_precedents, gold_verdict, difficulty, evidence_flags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, 
            facts, 
            domain, 
            json.dumps(statutes), 
            json.dumps(precedents), 
            gold_verdict, 
            difficulty,
            json.dumps(evidence)
        ))
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Seeded {inserted} cases into database.")

def load_case(case_id: int):
    """Load a specific case by DB ID."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
    conn.close()
    
    if row:
        case = dict(row)
        # Parse JSON fields
        for field in ['applicable_statutes', 'key_precedents', 'evidence_flags']:
            if case.get(field):
                try:
                    case[field] = json.loads(case[field])
                except:
                    case[field] = []
        return case
    return None

def list_cases(domain=None, difficulty=None):
    """List cases, optionally filtered by domain and difficulty."""
    conn = get_db_connection()
    query = "SELECT id, title, domain, difficulty, gold_verdict FROM cases WHERE 1=1"
    params = []
    
    if domain:
        query += " AND domain=?"
        params.append(domain)
    if difficulty:
        query += " AND difficulty=?"
        params.append(difficulty)
        
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_debate(case_id: int, transcript: list, verdict: dict, evaluation: dict):
    """Save a debate run to the database."""
    conn = get_db_connection()
    
    overall_score = evaluation.get("overall_score", 0.0)
    hallucination_count = evaluation.get("hallucination_count", 0)
    confidence = verdict.get("confidence_score", verdict.get("confidence", 0.0))
    
    conn.execute("""
        INSERT INTO debates (case_id, transcript, final_verdict, evaluation_json, judge_confidence, overall_score, hallucination_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        case_id, 
        json.dumps(transcript), 
        json.dumps(verdict), 
        json.dumps(evaluation), 
        confidence, 
        overall_score,
        hallucination_count
    ))
    conn.commit()
    conn.close()

def load_debate(debate_id: int):
    """Load a specific debate by ID."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM debates WHERE id=?", (debate_id,)).fetchone()
    conn.close()
    
    if row:
        debate = dict(row)
        for field in ['transcript', 'final_verdict', 'evaluation_json']:
            if debate.get(field):
                try:
                    debate[field] = json.loads(debate[field])
                except:
                    pass
        return debate
    return None

def list_debates():
    """List all debates."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT d.id, d.case_id, c.title, d.overall_score, d.hallucination_count, d.created_at 
        FROM debates d 
        JOIN cases c ON d.case_id = c.id 
        ORDER BY d.id DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()
    seed_from_json()
