import os
import json
from pathlib import Path
from openai import AzureOpenAI  # Assuming AzureOpenAI is installed and configured

def load_prompt(file_name: str, variables: dict) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / file_name
    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()
    for key, value in variables.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template

def refine_query(user_query: str) -> dict:
    prompt_system = load_prompt("refine_query_prompt_system.md", {})
    prompt_user = load_prompt("refine_query_prompt_user.md", {"userQuery": user_query})
    client = AzureOpenAI(
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ],
        response_format={"type": "json_object"}
    )
    refined_query = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(refined_query)
    except Exception as e:
        raise Exception("Failed to parse Refined Query response") from e
    return parsed

def chat_about_paper(paper_content: str, user_question: str) -> dict:
    prompt = load_prompt("chatAboutPaper.md", {"paperContent": paper_content, "userQuestion": user_question})
    client = AzureOpenAI(
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that answers questions about clinical trial study papers."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    result_text = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(result_text)
    except Exception:
        parsed = {"answer": result_text, "evidence": []}
    return parsed

def extract_structured_info(paper_content: str) -> dict:
    prompt = load_prompt("extractStructuredInfo.md", {"paperContent": paper_content})
    client = AzureOpenAI(
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a specialized assistant trained to extract structured data from clinical trial papers."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    result_text = response.choices[0].message.content.strip()
    try:
        structured_data = json.loads(result_text)
    except Exception:
        structured_data = {"error": "Could not parse structured data", "raw": result_text}
    return structured_data
