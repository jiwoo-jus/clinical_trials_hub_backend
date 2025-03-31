from fastapi import APIRouter, HTTPException
from services import pmc_service, openai_service

router = APIRouter()

# PMC의 full text HTML 반환 API
@router.get("/pmc_full_text_html")
async def get_pmc_full_text_html(pmcid: str):
    try:
        html_content = pmc_service.get_pmc_full_text_html(pmcid)
        return {"pmcid": pmcid, "pmc_full_text_html": html_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PMC XML에서 구조화된 정보 추출 API
@router.get("/structured_info")
async def get_structured_info(pmcid: str):
    try:
        content = pmc_service.get_pmc_full_text_xml(pmcid)
        structured_info = openai_service.extract_structured_info(content)
        return {"pmcid": pmcid, "structured_info": structured_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
