CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    facts TEXT NOT NULL,
    domain TEXT,                    -- Contract, Tort, Property, Criminal (BNS), etc.
    applicable_statutes TEXT,       -- JSON array e.g. ["BNS 302", "Indian Evidence Act 1872 s.32"]
    key_precedents TEXT,            -- JSON array of citations
    gold_verdict TEXT,              -- Optional reference verdict for evaluation
    difficulty TEXT,                -- easy/medium/hard
    evidence_flags TEXT,            -- JSON array of evidence flags
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS debates (
    id INTEGER PRIMARY KEY,
    case_id INTEGER,
    transcript TEXT,                -- Full debate log as JSON
    final_verdict TEXT,
    evaluation_json TEXT,           -- Full evaluation JSON
    judge_confidence REAL,
    overall_score REAL,             -- From evaluation
    hallucination_count INTEGER,    -- Count of hallucinations from evaluation
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);
