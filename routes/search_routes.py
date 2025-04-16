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
            "cond": data.get("cond", None),
            "intr": data.get("intr", None),
            "other_term": data.get("other_term", None),
            "journal": data.get("journal", None),
            "sex": data.get("sex", None),
            "age": data.get("age", None),
            "studyType": data.get("studyType", None),
            "sponsor": data.get("sponsor", None),
            "location": data.get("location", None),
            "status": data.get("status", None)
        }
        print("input_data:", input_data)

        
        # Prepare parameters for query refinement, including user_query from the frontend
        refine_param = {
            "cond": input_data.get("cond"),
            "intr": input_data.get("intr"),
            "other_term": input_data.get("other_term"),
            "user_query": data.get("user_query", "")
        }
        
        # Use refined query if already refined, otherwise perform refinement
        is_refined = data.get("isRefined", False)
        if is_refined and "refinedQuery" in data and data["refinedQuery"]:
            refined_input_data = data["refinedQuery"]
            print("Already refined. Skipping refinement step.")
        else:
            refined_input_data = openai_service.refine_query(refine_param)
            print("refined_input_data:", refined_input_data)
        
        # Pagination parameters
        page = int(data.get("page", 1))
        page_size = int(data.get("pageSize", 10))
        # CTG pagination token from frontend if provided
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
            "gender": "Male",  # Modify as needed
            "ages": "child adult older",
            "sponsor": "National Institute of Health",
            "location": "Columbus, Ohio", 
            "status": "COMPLETED,TERMINATED",
            "date_range": None,  # Modify as needed
            "page_token": None,  # Will be provided from frontend
            "sort": "@relevance"
        }
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "../queries/pmConditionQuery.md"), "r", encoding="utf-8") as f:
            pm_condition_query = f.read()
        
        # Determine search sources from payload; default to all
        sources = data.get("sources", ["PM", "PMC", "CTG"])
        
        # PubMed (PM) search
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
        
        # ClinicalTrials.gov (CTG) search
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
