# search_routes.py
import os
from fastapi import APIRouter, HTTPException, Request
from services import openai_service, pm_service, pmc_service, ctg_service
from utils import sleep_ms

router = APIRouter()

@router.post("/")
async def search(request: Request):
    try:
        data = await request.json()
        print("Received data:", data)

        # ① 프론트엔드에서 넘어오는 모든 필터 수집 (새 필드 포함)
        input_data = {
            "cond": data.get("cond"),
            "intr": data.get("intr"),
            "other_term": data.get("other_term"),
            "journal": data.get("journal"),
            "sex": data.get("sex"),
            "age": data.get("age"),
            "studyType": data.get("studyType"),
            "sponsor": data.get("sponsor"),
            "location": data.get("location"),
            "status": data.get("status"),
            "publicationType": data.get("publicationType"),  # 신규
            "phase": data.get("phase"),                      # 신규
        }

        # ② Query refinement 준비
        refine_param = {
            "cond": input_data.get("cond"),
            "intr": input_data.get("intr"),
            "other_term": input_data.get("other_term"),
            "user_query": data.get("user_query", "")
        }
        is_refined = data.get("isRefined", False)
        if is_refined and data.get("refinedQuery"):
            refined_input_data = data["refinedQuery"]
        else:
            refined_input_data = openai_service.refine_query(refine_param)

        # ③ 페이지네이션 인자
        page = int(data.get("page", 1))
        page_size = int(data.get("pageSize", 10))
        ctg_page_token = data.get("ctgPageToken")

        # ④ 임시 기본값 (필요시 조정)
        pm_temp = {
            "date_from": "1000/01/01", "date_to": "3009/12/31",
            "sort": "relevance", "sort_order": None
        }
        ctg_temp = {
            "date_range": None, "sort": "@relevance"
        }

        # ⑤ PubMed 조건 쿼리 템플릿 로드
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "../queries/pmConditionQuery.md"), "r", encoding="utf-8") as f:
            pm_condition_query = f.read()

        # ⑥ PubMed 검색
        pm_results = {}
        if "PM" in data.get("sources", ["PM","PMC","CTG"]):
            pm_results = pm_service.search_pm(
                combined_query=refined_input_data.get("combined_query",""),
                condition_query=pm_condition_query,
                publicationType=input_data.get("publicationType"),  # 신규
                journal=input_data.get("journal"),
                sex=input_data.get("sex"),
                age=input_data.get("age"),
                date_from=pm_temp["date_from"],
                date_to=pm_temp["date_to"],
                page=page,
                page_size=page_size,
                sort=pm_temp["sort"],
                sort_order=pm_temp["sort_order"]
            )

        # ⑦ ClinicalTrials.gov 검색
        ctg_results = {}
        if "CTG" in data.get("sources", ["PM","PMC","CTG"]):
            ctg_results = ctg_service.search_ctg(
                term=refined_input_data.get("other_term"),
                cond=refined_input_data.get("cond"),
                intr=refined_input_data.get("intr"),
                study_type=input_data.get("studyType"),
                phase=input_data.get("phase"),                   # 신규
                gender=input_data.get("sex"),
                ages=input_data.get("age"),
                sponsor=input_data.get("sponsor"),
                location=input_data.get("location"),
                status=input_data.get("status"),
                date_range=ctg_temp["date_range"],
                page_size=page_size,
                page_token=ctg_page_token,
                sort=ctg_temp["sort"]
            )

        sleep_ms(1000)

        # ⑧ 결과 병합
        combined = {
            "pm": {
                "results": pm_results.get("results", []),
                "total": pm_results.get("total", 0),
                "query": pm_results.get("applied_query", "")
            },
            "ctg": {
                "results": ctg_results.get("results", []),
                "total": ctg_results.get("total", 0),
                "query": ctg_results.get("applied_query", ""),
                "nextPageToken": ctg_results.get("nextPageToken")
            }
        }
        return {"refinedQuery": refined_input_data, "results": combined}

    except Exception as e:
        print("Error in search route:", str(e))
        raise HTTPException(status_code=500, detail="Server error")
