from fastapi import APIRouter, HTTPException, Request
from services import openai_service, pm_service, pmc_service
import json

router = APIRouter()

@router.post("/")
async def chat_about_paper(request: Request):
    try:
        data = await request.json()
        print("Received data:", data)
        user_question = data.get("userQuestion", "")
        # 만약 content가 전달되면 그 값을 그대로 paper_content로 사용
        if "content" in data:
            paper_content = data["content"]
            if isinstance(paper_content, dict):
                paper_content = json.dumps(paper_content, indent=2)
        else:
            paper_id = data.get("paperId", "")
            paper_content = pmc_service.get_pmc_full_text_xml(paper_id)
        result = openai_service.chat_about_paper(paper_content, user_question)
        return result
    except Exception as e:
        print("Error in chat route:", str(e))
        raise HTTPException(status_code=500, detail="Server error")
