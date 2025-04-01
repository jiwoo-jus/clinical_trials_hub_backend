import os
import json
from pathlib import Path

def load_sample_file(file_path: str, variables: dict) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        file = f.read()
    for key, value in variables.items():
        file = file.replace(f"{{{{{key}}}}}", value)
    return file

# openai_service.py extract_structured_info function test
def extract_structured_info(paper_content: str) -> dict:
    sample_ctg = load_sample_file("/Users/jiwoo/WorkSpace/ClinicalTrialsHub/clinical_trials_hub_web/clinical_trials_hub_backend/sample/ctg/case1_ctg_NCT03325985_group0.json", {})
    
    result_text = sample_ctg
    try:
        structured_data = json.loads(result_text)
    except Exception:
        structured_data = {"error": "Could not parse structured data", "raw": result_text}
    return structured_data
