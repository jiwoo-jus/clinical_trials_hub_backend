from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from services import ctg_service, pmc_service, openai_service, test_service
import json

router = APIRouter()

# PMC의 full text HTML 반환 API
@router.get("/pmc_full_text_html")
async def get_pmc_full_text_html(pmcid: str):
    try:
        html_content = pmc_service.get_pmc_full_text_html(pmcid)
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PMC XML에서 구조화된 정보 추출 API
@router.get("/structured_info")
async def get_structured_info(pmcid: str):
    try:
        content = pmc_service.get_pmc_full_text_xml(pmcid)
        structured_info = openai_service.get_structured_info_with_cache(pmcid, content)
        # structured_info = test_service.extract_structured_info(content)
        print("Structured Info:", json.dumps(structured_info, indent=2))
        return {"pmcid": pmcid, "structured_info": structured_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ctg_detail")
async def get_ctg_detail(nctId: str):
    try:
        detail = ctg_service.get_ctg_detail(nctId)
        # You might decide whether to include the entire detail object or extract specific fields.
        return {"nctId": nctId, "structured_info": detail, "full_text": ""}
    except Exception as e:
        # Log the error on the backend and send a proper message to the client.
        raise HTTPException(status_code=500, detail=str(e))
