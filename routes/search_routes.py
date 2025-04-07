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
        refine_param = {
            "cond": input_data.get("cond"),
            "intr": input_data.get("intr"),
            "other_term": input_data.get("other_term")
        }
        
        refined_input_data = openai_service.refine_query(refine_param)
        print("Refined Query:", refined_input_data)
        
        pm_temp_data = {
            "journal": "BMJ open",
            "sex": "Male",
            "age": "child",
            "date_from": "1000/01/01",
            "date_to": "3009/12/31",
            "page": 1,
            "page_size": 10,
            "sort": "relevance"
        }
        ctg_temp_data = {
            "study_type": "int obs", 
            "gender": "Male", #need to be changed
            "ages": "child adult older",
            "sponsor": "National Institute of Health",
            "location": "Columbus, Ohio", 
            "status": "COMPLETED,TERMINATED",
            "date_range": None, #need to be changed
            "page_size": 10,
            "page_token": None, #need to be changed
            "sort": "@relevance"
        }
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "../queries/pmConditionQuery.md"), "r", encoding="utf-8") as f:
            pm_condition_query = f.read()
        
        pm_results = pm_service.search_pm(
            refined_input_data.get("combined_query", ""), 
            condition_query=pm_condition_query, 
            journal=input_data.get("journal"), 
            sex=input_data.get("sex"), 
            age=input_data.get("age"), 
            date_from=pm_temp_data.get("date_from"), 
            date_to=pm_temp_data.get("date_to"), 
            page=pm_temp_data.get("page"), 
            page_size=pm_temp_data.get("page_size"), 
            sort="relevance")
        sleep_ms(1000)
        
        ctg_results = ctg_service.search_ctg(
            refined_input_data.get("other_term"),
            refined_input_data.get("cond"),
            refined_input_data.get("intr"),
            input_data.get("study_type"),
            input_data.get("sex"),
            input_data.get("age"),
            input_data.get("sponsor"),
            input_data.get("location"),
            input_data.get("status"),
            ctg_temp_data.get("date_range"),
            ctg_temp_data.get("page_size"),
            ctg_temp_data.get("page_token"),
            ctg_temp_data.get("sort")
            )
        sleep_ms(1000)
        combined_results = {
            "pm": {
                "results": pm_results.get("results", []),
                "total": pm_results.get("total", 0),
                "query": pm_results.get("applied_query", "")
            },
            # "pmc": {
            #     "results": pmc_results,
            #     "total": pmc_total,
            #     "query": pmc_term
            # },
            "ctg": {
                "results": ctg_results.get("results", []),
                "total": ctg_results.get("total", 0),
                "query": ctg_results.get("applied_query", "")
            }
        }   
        return {"refinedQuery": refined_input_data, "results": combined_results}
    except Exception as e:
        print("Error in search route:", str(e))
        raise HTTPException(status_code=500, detail="Server error")
