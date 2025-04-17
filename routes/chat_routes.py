from fastapi import APIRouter, HTTPException, Request, Body # Import Body
from pydantic import BaseModel, Field # Import Pydantic models
from services import openai_service, pm_service, pmc_service
import json
# Remove highlight_evidence_in_html if not needed for CTG JSON
# from utils import highlight_evidence_in_html

router = APIRouter()

# Define request model for better validation
class ChatRequest(BaseModel):
    userQuestion: str
    source: str = Field(..., pattern="^(CTG|PM|PMC)$") # Validate source
    id: str # nctId or pmcid
    content: str # Can be JSON string or HTML/text

@router.post("/")
# Use the Pydantic model for automatic validation
async def chat_about_paper(chat_request: ChatRequest):
    try:
        print(f"Received chat request for source: {chat_request.source}, id: {chat_request.id}")
        # Data is already validated and parsed by Pydantic
        user_question = chat_request.userQuestion
        paper_content = chat_request.content
        source = chat_request.source
        # id = chat_request.id # ID is available if needed later

        # Pass source to the service function
        result = openai_service.chat_about_paper(source, paper_content, user_question)

        # Highlighting might not make sense for JSON evidence from CTG
        # Conditionally apply highlighting only for PM/PMC sources if needed
        # if source in ['PM', 'PMC'] and "evidence" in result and result["evidence"]:
        #     # Assuming highlight_evidence_in_html works with the paper_content format for PM/PMC
        #     result["highlighted_article"] = highlight_evidence_in_html(paper_content, result["evidence"])
        # else:
        #     # For CTG or if no evidence, just return the original content or null/empty
        #     result["highlighted_article"] = None # Or paper_content if you want to return the JSON

        # Let's remove highlighted_article for now to simplify, as it's complex for JSON
        if "highlighted_article" in result:
             del result["highlighted_article"]

        return result
    except Exception as e:
        print(f"Error in chat route: {type(e).__name__} - {str(e)}")
        # Consider logging the full traceback for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error processing chat request: {str(e)}")