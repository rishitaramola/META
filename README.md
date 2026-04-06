---
title: Judicial Reasoning Env
emoji: ⚖️
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# Judicial Reasoning RL Environment

An RL environment where an LLM agent acts as a judge, reasoning through legal cases to deliver structured verdicts.

## Tasks
- **Task 1 (Easy):** Contract dispute resolution
- **Task 2 (Medium):** Tort and negligence reasoning  
- **Task 3 (Hard):** Property and inheritance dispute

## Observation Space
- Fact pattern
- Applicable statutes
- Past precedents (2-5)
- Evidence flags

## Action Space
- Verdict (liable/not_liable/guilty/not_guilty)
- Confidence score
- Reasoning chain
- Cited precedents

## Reward Function
R = α·logic + β·accuracy + γ·fairness + δ·citation

## Baseline Scores
- task1_contract: 0.9680
- task2_tort: 0.6853
- task3_property: 0.5520
- Overall: 0.7351

## Setup
```bash
docker build -t judicial-env .
docker run judicial-env
```