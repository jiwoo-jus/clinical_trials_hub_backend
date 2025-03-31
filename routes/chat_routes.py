from fastapi import APIRouter, HTTPException, Request
from services import openai_service, pm_service, pmc_service

router = APIRouter()

@router.post("/")
async def chat_about_paper(request: Request):
    try:
        data = await request.json()
        paper_id = data.get("paperId", "")
        user_question = data.get("userQuestion", "")
        # 1. Get full text (using PMC service for both PubMed and PMC)
        paper_content = pmc_service.get_pmc_full_text_xml(paper_id)
        # 2. Get answer from OpenAI service
        result = openai_service.chat_about_paper(paper_content, user_question)
        return result
    except Exception as e:
        print("Error in chat route:", str(e))
        raise HTTPException(status_code=500, detail="Server error")
