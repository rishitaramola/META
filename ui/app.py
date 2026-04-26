import gradio as gr
import json
import sys
import os
import threading

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import list_cases, load_case, save_debate
from debate.debate_orchestrator import DebateOrchestrator

def get_case_choices():
    cases = list_cases()
    # Format: "ID - Title (Domain)"
    return [f"{c['id']} - {c['title']} ({c['domain']})" for c in cases]

def parse_case_selection(selection: str) -> int:
    if not selection:
        return 1
    return int(selection.split(" - ")[0])

def run_debate_ui(case_selection: str, num_rounds: int, progress=gr.Progress()):
    if not case_selection:
        return "Please select a case first.", "", "", ""
        
    case_id = parse_case_selection(case_selection)
    case = load_case(case_id)
    
    if not case:
        return f"Error loading case {case_id}", "", "", ""
        
    case_info = f"### Case Facts\n\n{case.get('facts', 'No facts available.')}\n\n"
    case_info += f"**Domain:** {case.get('domain', 'Unknown')}\n"
    case_info += f"**Difficulty:** {case.get('difficulty', 'Unknown')}\n"
    
    yield case_info, "Initializing Debate...", "", ""
    
    # We will collect the transcript text incrementally
    transcript_text = ""
    
    # Simple callback to update UI during processing
    def progress_callback(msg):
        progress(0, desc=msg)
    
    orchestrator = DebateOrchestrator(case, num_rounds=num_rounds)
    
    # Since orchestrator.run_debate is synchronous, we run it
    # We could make it asynchronous or generator-based for true streaming,
    # but for simplicity we will just yield the final result after it runs.
    # In a full production app, orchestrator should yield after each message.
    
    result = orchestrator.run_debate(progress_callback=progress_callback)
    
    # Format Transcript
    for msg in result["transcript"]:
        role = msg["role"]
        content = msg["content"]
        citations = msg.get("citations", [])
        
        if role == "Plaintiff":
            color = "#1f77b4" # Blue
        elif role == "Defendant":
            color = "#d62728" # Red
        else:
            color = "#2ca02c" # Green
            
        transcript_text += f"**Round {msg['round']} - {role}**\n\n"
        transcript_text += f"{content}\n\n"
        if citations:
            transcript_text += f"*{', '.join(citations)}*\n\n"
        transcript_text += "---\n\n"
        
    # Format Verdict
    verdict_data = result["verdict"]
    verdict_text = f"## Final Verdict: {verdict_data.get('verdict', 'Unknown').upper()}\n\n"
    verdict_text += f"**Confidence:** {verdict_data.get('confidence_score', 0.0):.0%}\n\n"
    verdict_text += f"### Reasoning Chain\n{verdict_data.get('reasoning_chain', '')}\n\n"
    verdict_text += f"### Ratio Decidendi\n{verdict_data.get('ratio_decidendi', '')}\n\n"
    if verdict_data.get("obiter_dicta"):
        verdict_text += f"### Obiter Dicta\n{verdict_data.get('obiter_dicta', '')}\n\n"
        
    # Format Evaluation
    eval_data = result["evaluation"]
    eval_text = f"## Overall Score: {eval_data.get('overall_score', 0)}/100\n\n"
    eval_text += f"*{eval_data.get('evaluation_summary', '')}*\n\n"
    
    scores = eval_data.get('scores', {})
    eval_text += "### Dimension Scores\n"
    for k, v in scores.items():
        eval_text += f"- **{k.replace('_', ' ').title()}**: {v}/10\n"
        
    eval_text += f"\n**Hallucinations Detected:** {eval_data.get('hallucination_count', 0)}\n\n"
    
    strengths = eval_data.get('strengths', [])
    if strengths:
        eval_text += "### Strengths\n" + "\n".join([f"- {s}" for s in strengths]) + "\n\n"
        
    weaknesses = eval_data.get('weaknesses', [])
    if weaknesses:
        eval_text += "### Weaknesses\n" + "\n".join([f"- {w}" for s in weaknesses]) + "\n\n"
        
    # Save to DB
    try:
        save_debate(case_id, result["transcript"], result["verdict"], result["evaluation"])
    except Exception as e:
        print(f"Failed to save debate: {e}")
        
    yield case_info, transcript_text, verdict_text, eval_text


with gr.Blocks(title="Judicial Debate Arena", theme=gr.themes.Default(primary_hue="indigo")) as demo:
    gr.Markdown("# ⚖️ Judicial Debate Arena")
    gr.Markdown("A multi-agent simulation where 3 AI agents debate an Indian legal case using IRAC reasoning.")
    
    with gr.Row():
        with gr.Column(scale=1):
            case_dropdown = gr.Dropdown(choices=get_case_choices(), label="Select Case from Database")
            rounds_slider = gr.Slider(minimum=1, maximum=5, value=2, step=1, label="Number of Debate Rounds")
            start_btn = gr.Button("Start 3-AI Debate", variant="primary")
            
            case_details = gr.Markdown("Select a case to see facts.")
            
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("Live Debate Transcript"):
                    transcript_box = gr.Markdown("Debate will appear here...")
                
                with gr.TabItem("Final Verdict"):
                    verdict_box = gr.Markdown("Waiting for judge...")
                    
                with gr.TabItem("LLM-as-Judge Evaluation"):
                    eval_box = gr.Markdown("Waiting for evaluation...")

    start_btn.click(
        fn=run_debate_ui,
        inputs=[case_dropdown, rounds_slider],
        outputs=[case_details, transcript_box, verdict_box, eval_box]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7861)
