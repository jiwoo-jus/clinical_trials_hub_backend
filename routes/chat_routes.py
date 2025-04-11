from fastapi import APIRouter, HTTPException, Request
from services import openai_service, pm_service, pmc_service
import json
from utils import highlight_evidence_in_html

router = APIRouter()

@router.post("/")
async def chat_about_paper(request: Request):
    try:
        data = await request.json()
        user_question = data.get("userQuestion", "")
        print("user_question: ", user_question)
        if "content" in data:
            paper_content = data["content"]
            if isinstance(paper_content, dict):
                paper_content = json.dumps(paper_content, indent=2)
        else:
            paper_id = data.get("paperId", "")
            paper_content = pmc_service.get_pmc_full_text_xml(paper_id)
        result = openai_service.chat_about_paper(paper_content, user_question)
        # Highlight evidence sentences in the article HTML.
        if "evidence" in result and result["evidence"]:
            result["highlighted_article"] = highlight_evidence_in_html(paper_content, result["evidence"])
        else:
            result["highlighted_article"] = paper_content
        return result
    except Exception as e:
        print("Error in chat route:", str(e))
        raise HTTPException(status_code=500, detail="Server error")