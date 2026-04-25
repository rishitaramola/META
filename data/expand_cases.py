import json
import os

cases_path = os.path.join(os.path.dirname(__file__), 'cases.json')

with open(cases_path, 'r', encoding='utf-8') as f:
    cases = json.load(f)

# 1. Replace Western Precedents
for case in cases:
    if 'precedents' in case:
        for p in case['precedents']:
            if 'Hadley v Baxendale' in p.get('case_name', ''):
                p['case_name'] = 'Satyabrata Ghose v Mugneeram Bangur (1954 SC)'
                p['rationale'] = 'Damages bounded by frustration of contract principles in Indian law.'
            if 'Donoghue v Stevenson' in p.get('case_name', ''):
                p['case_name'] = 'M.C. Mehta v Union of India (1987 SC)'
                p['rationale'] = 'Strict liability applies for inherent negligence causing harm.'

# 2. Add 30 New Cases (Mocked for Hackathon)
domains = ["criminal", "civil", "family", "labor", "constitutional"]
for i in range(15, 45):
    domain = domains[i % len(domains)]
    
    if domain == "criminal":
        fact = f"Incident {i}: The accused threatened the victim in a public space, brandishing a weapon, demanding money."
        stats = ["Bharatiya Nyaya Sanhita (BNS) 2023 Section 351"]
        verdict = "advisory_only"
        prec = [{"case_name": "State of Maharashtra v Madhurkar Narayan", "verdict": "guilty", "rationale": "Clear mens rea."}]
    elif domain == "labor":
        fact = f"Incident {i}: Employee was terminated without 1-month notice after refusing personal demands of the manager."
        stats = ["Industrial Disputes Act 1947 Section 25F", "POSH Act 2013"]
        verdict = "liable"
        prec = [{"case_name": "Vishaka v State of Rajasthan (1997 SC)", "verdict": "liable", "rationale": "Workplace harassment protection."}]
    elif domain == "constitutional":
        fact = f"Incident {i}: The municipal corporation demolished the petitioner's pavement dwelling without prior notice."
        stats = ["Article 21 - Right to Life and Livelihood"]
        verdict = "liable"
        prec = [{"case_name": "Olga Tellis v Bombay Municipal Corporation (1985 SC)", "verdict": "liable", "rationale": "Right to livelihood is part of Right to Life."}]
    elif domain == "family":
        fact = f"Incident {i}: Dispute over child custody and maintenance after mutual divorce filing."
        stats = ["Hindu Marriage Act 1955"]
        verdict = "partial_liability"
        prec = []
    else:
        fact = f"Incident {i}: Supplier failed to deliver goods due to sudden market price spike, claiming force majeure."
        stats = ["Indian Contract Act 1872 Section 73"]
        verdict = "liable"
        prec = [{"case_name": "Satyabrata Ghose v Mugneeram Bangur (1954 SC)", "verdict": "liable", "rationale": "Price rise is not force majeure."}]

    new_case = {
        "case_id": f"C{i:03d}",
        "domain": domain,
        "difficulty": "medium",
        "fact_pattern": fact,
        "statutes_applicable": stats,
        "precedents": prec,
        "evidence_flags": ["witness statement"],
        "gold_verdict": verdict,
        "gold_reasoning": "Standard IRAC application of the specified statute.",
        "court_level": "high"
    }
    cases.append(new_case)

with open(cases_path, 'w', encoding='utf-8') as f:
    json.dump(cases, f, indent=2)

print(f"Total cases now: {len(cases)}")
