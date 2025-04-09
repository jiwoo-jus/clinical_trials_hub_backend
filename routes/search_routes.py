# /Users/jiwoo/WorkSpace/ClinicalTrialsHub/clinical_trials_hub_web/clinical_trials_hub_backend/routes/search_routes.py
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
        
        # 기존 검색 필터들
        input_data = {
            "cond": data.get("cond", ""),
            "intr": data.get("intr", ""),
            "other_term": data.get("other_term", ""),
            "journal": data.get("journal", ""),
            "sex": data.get("sex", ""),
            "age": data.get("age", ""),
            "studyType": data.get("studyType", ""),
            "sponsor": data.get("sponsor", ""),
            "location": data.get("location", ""),
            "status": data.get("status", "")
        }
        
        # 리파인 파라미터: 기존 필터 외에 user_query도 추가 (프론트엔드에서 전송된 값)
        refine_param = {
            "cond": input_data.get("cond"),
            "intr": input_data.get("intr"),
            "other_term": input_data.get("other_term"),
            "user_query": data.get("user_query", "")
        }
        
        # refined 여부에 따라 정제된 쿼리 재사용
        is_refined = data.get("isRefined", False)
        if is_refined and "refinedQuery" in data and data["refinedQuery"]:
            refined_input_data = data["refinedQuery"]
            print("already refined. skip refining.")
        else:
            refined_input_data = openai_service.refine_query(refine_param)
            print("refined_input_data:", refined_input_data)
        
        # 페이지네이션 값
        page = int(data.get("page", 1))
        page_size = int(data.get("pageSize", 10))
        # CTG 페이지 토큰 (프론트엔드에서 전달됨)
        ctg_page_token = data.get("ctgPageToken", None)
        
        pm_temp_data = {
            "journal": "BMJ open",
            "sex": "Male",
            "age": "child",
            "date_from": "1000/01/01",
            "date_to": "3009/12/31",
            "sort": "relevance",  # Best Match
            "sort_order": None
        }
        ctg_temp_data = {
            "study_type": "int obs", 
            "gender": "Male",  # 추후 수정 필요
            "ages": "child adult older",
            "sponsor": "National Institute of Health",
            "location": "Columbus, Ohio", 
            "status": "COMPLETED,TERMINATED",
            "date_range": None,  # 추후 수정 필요
            "page_token": None,  # 프론트엔드 전달값 사용
            "sort": "@relevance"
        }
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "../queries/pmConditionQuery.md"), "r", encoding="utf-8") as f:
            pm_condition_query = f.read()
        
        # 다중 검색 소스: 기본은 모두 선택, 프론트엔드에서 배열 형태로 전달
        sources = data.get("sources", ["PM", "PMC", "CTG"])
        
        # PubMed 검색 (PM)
        pm_results = {}
        if "PM" in sources:
            pm_results = pm_service.search_pm(
                refined_input_data.get("combined_query", ""),
                condition_query=pm_condition_query,
                journal=input_data.get("journal"),
                sex=input_data.get("sex"),
                age=input_data.get("age"),
                date_from=pm_temp_data.get("date_from"),
                date_to=pm_temp_data.get("date_to"),
                page=page,
                page_size=page_size,
                sort=pm_temp_data.get("sort"),
                sort_order=pm_temp_data.get("sort_order")
            )
        # PMC 검색은 필요에 따라 추가
        
        # ClinicalTrials.gov (CTG) 검색
        ctg_results = {}
        if "CTG" in sources:
            ctg_results = ctg_service.search_ctg(
                term=refined_input_data.get("other_term"),
                cond=refined_input_data.get("cond"),
                intr=refined_input_data.get("intr"),
                study_type=input_data.get("studyType"),
                gender=input_data.get("sex"),
                ages=input_data.get("age"),
                sponsor=input_data.get("sponsor"),
                location=input_data.get("location"),
                status=input_data.get("status"),
                date_range=ctg_temp_data.get("date_range"),
                page_size=page_size,
                page_token=ctg_page_token,
                sort=ctg_temp_data.get("sort")
            )
        sleep_ms(1000)
        combined_results = {
            "pm": {
                "results": pm_results.get("results", []),
                "total": pm_results.get("total", 0),
                "query": pm_results.get("applied_query", "")
            },
            # pmc_results = {}
            # if "PMC" in sources:
            #     pmc_results = pmc_service.search_pmc(...)
            "ctg": {
                "results": ctg_results.get("results", []),
                "total": ctg_results.get("total", 0),
                "query": ctg_results.get("applied_query", ""),
                "nextPageToken": ctg_results.get("nextPageToken", None)
            }
        }
        return {"refinedQuery": refined_input_data, "results": combined_results}
    except Exception as e:
        print("Error in search route:", str(e))
        raise HTTPException(status_code=500, detail="Server error")
