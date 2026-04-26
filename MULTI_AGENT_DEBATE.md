# Judicial Debate Arena

The Judicial Debate Arena is an extension of the `JudicialMediationEnv` that simulates realistic Indian courtroom-style adversarial debates using a multi-agent AI system. 

It pits a **Plaintiff Advocate** and a **Defendant Advocate** against each other across multiple rounds of argumentation, while a **Neutral Judge** synthesizes the transcript into an IRAC-structured final verdict.

## Key Features

1. **Shared Legal Database**: Uses a persistent SQLite database (`cases.db`) to store 75+ Indian legal cases, as well as full debate logs, transcripts, and evaluation scores.
2. **Multi-Agent Simulation**: Three LLM-powered agents engage in multi-turn argumentation, ensuring adversarial rigor before reaching a verdict.
3. **Structured IRAC Reasoning**: Enforces the Issue-Rule-Application-Conclusion structure expected in professional Indian legal contexts.
4. **LLM-as-Judge Evaluation**: Scores debates across multiple dimensions (Legal Accuracy, IRAC Quality, Factual Grounding, Rebuttal Effectiveness, Persuasiveness, Professionalism) to automatically calculate an overall score (0-100).
5. **Anti-Hallucination Guardrails**: Implements strict penalty systems for hallucinated citations, ensuring the agents rely on real Indian statutes (BNS, BNSS, IPC equivalents, Constitution, etc.) and valid precedents.
6. **Gradio UI**: A user-friendly web interface to select cases, choose the number of debate rounds, and view the live streaming transcript and final evaluation.

## Directory Structure

```
judicial-reasoning-env/
├── database/                  # SQLite DB layer
│   ├── schema.sql             # Table schemas (cases, debates)
│   ├── db_utils.py            # DB access & seeding functions
│   └── cases.db               # (Auto-generated) SQLite DB
├── debate/                    # Multi-Agent Debate Logic
│   ├── agents.py              # LLM wrappers for Plaintiff, Defendant, Judge
│   ├── debate_orchestrator.py # Multi-round simulation loop
│   ├── evaluation.py          # LLM-as-Judge & rule-based grading
│   └── prompts.py             # System prompts tailored for Indian law
├── ui/                        # Web Interface
│   └── app.py                 # Gradio dashboard
├── debate_demo.py             # CLI application
└── MULTI_AGENT_DEBATE.md      # This documentation
```

## Quick Start

### 1. Initialize the Database
The CLI tool will automatically initialize and seed the database on its first run.
```bash
python debate_demo.py --list
```
This lists all available cases seeded from `data/cases.json`.

### 2. Run a Debate via CLI
To start a 2-round debate on Case ID 1:
```bash
python debate_demo.py --case 1 --rounds 2
```
The debate transcript, final verdict, and evaluation metrics will be printed to the console and saved to `database/cases.db`.

### 3. Launch the Web UI
The Gradio UI provides a visual, interactive way to run debates.
```bash
python ui/app.py
```
Access the dashboard at `http://localhost:7861` (default port).

## Evaluation Metrics

The `DebateEvaluator` (`debate/evaluation.py`) generates a comprehensive JSON report containing:

- **overall_score** (0-100): Weighted average of individual dimensions.
- **legal_accuracy** (0-10): Accuracy of cited Indian statutes and precedents.
- **irac_quality** (0-10): Completeness of Issue, Rule, Application, Conclusion.
- **factual_grounding** (0-10): Adherence to the given case facts (no hallucination of new details).
- **rebuttal_effectiveness** (0-10): Direct engagement with opposing arguments.
- **persuasiveness** (0-10): Clarity and persuasiveness to an Indian judge.
- **professionalism** (0-10): Courtroom decorum and respectful tone.
- **hallucination_count**: Explicit tracking of fabricated legal rules or precedents.

## Future Enhancements
- **Human-in-the-Loop**: Allow users to step in as the Plaintiff or Defendant advocate.
- **RAG Integration**: Connect the agents directly to a vector database of Indian Kanoon rulings for real-time precedent retrieval.
- **Adaptive Rounds**: Automatically stop the debate early if the Judge detects consensus.
- **Training Data**: Export high-scoring debate transcripts as preference data for GRPO fine-tuning.
