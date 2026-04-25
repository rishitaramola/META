import os
import json
import torch
from datasets import Dataset

# Safe imports for local testing vs Colab execution
try:
    from trl import GRPOConfig, GRPOTrainer
    from unsloth import FastLanguageModel, PatchFastRL
    PatchFastRL("GRPO", FastLanguageModel)
    TRAINING_AVAILABLE = True
except ImportError:
    TRAINING_AVAILABLE = False
    print("Warning: TRL or Unsloth not found. Run this on Colab for full training.")

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reward.rubric import JudicialRubric

# Load cases
def load_cases(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def format_case_as_prompt(case):
    return f"""You are a judge in an Indian court. 
Domain: {case.get('domain', 'civil')}
Facts: {case.get('fact_pattern', '')}
Applicable Statutes: {', '.join(case.get('statutes_applicable', []))}
Plaintiff argues: The defendant is clearly liable based on the facts.
Defendant argues: We deny liability. The plaintiff has not proven their case.

Deliver your verdict in this JSON format:
{{
  "verdict": "liable|not_liable|guilty|not_guilty|partial_liability|advisory_only",
  "confidence_score": 0.9,
  "reasoning_chain": "Issue: ... Rule: ... Application: ... Conclusion: ...",
  "cited_precedents": ["case_name_year"],
  "applicable_bns_sections": ["BNS 2023 S.XX"],
  "refer_to_human_judge": false,
  "refer_reason": null
}}"""

def judicial_reward_fn(completions, prompts, **kwargs):
    """
    GRPO calls this function with batches of completions.
    We compute the reward using our Rubric.
    """
    rubric = JudicialRubric()
    rewards = []
    
    # In GRPO, kwargs might contain the original dataset rows if passed correctly,
    # but for simplicity we'll extract the gold verdict if we mapped it, 
    # or just use a default case dictionary.
    # To do this perfectly, the dataset needs the 'gold_verdict' column passed through.
    gold_verdicts = kwargs.get('gold_verdict', ['liable'] * len(completions))
    
    for completion, gold in zip(completions, gold_verdicts):
        case_mock = {"gold_verdict": gold}
        # completion is usually a list of strings from the model
        text = completion[0]['content'] if isinstance(completion, list) else completion
        reward = rubric.score(text, case_mock)
        rewards.append(reward)
        
    return rewards

def train():
    if not TRAINING_AVAILABLE:
        print("Cannot start training without Unsloth/TRL.")
        return

    print("Initializing Unsloth Llama 3.1 8B...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Meta-Llama-3.1-8B-Instruct",
        max_seq_length=4096,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(model, r=16, lora_alpha=16)

    # Prepare Dataset
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cases.json')
    if os.path.exists(data_path):
        cases = load_cases(data_path)
    else:
        # Fallback dummy data for testing
        cases = [{"fact_pattern": "Test", "domain": "contract", "gold_verdict": "liable"}]
        
    formatted_data = {
        "prompt": [format_case_as_prompt(c) for c in cases],
        "gold_verdict": [c.get("gold_verdict", "liable") for c in cases]
    }
    dataset = Dataset.from_dict(formatted_data)

    print("Configuring GRPO Trainer...")
    config = GRPOConfig(
        output_dir="./judicial-grpo-output",
        num_train_epochs=3,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=5e-6,
        logging_steps=10,
        save_steps=50,
        report_to="wandb",
    )

    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        reward_funcs=[judicial_reward_fn],
        args=config,
        train_dataset=dataset,
    )
    
    print("Starting Training Loop...")
    trainer.train()
    print("Training Complete!")

if __name__ == "__main__":
    train()
