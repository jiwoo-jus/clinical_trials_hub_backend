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
        input_data = {
            "cond": data.get("cond", ""),
            "intr": data.get("intr", ""),
            "other_term": data.get("other_term", "")
        }
        print("Received input data:", input_data)
        
        refined_input_data = openai_service.refine_query(input_data)
        print("Refined Query:", refined_input_data)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "../queries/pmConditionQuery.md"), "r", encoding="utf-8") as f:
            pm_condition_query = f.read()
        pm_results = pm_service.search_pm(refined_input_data, pm_condition_query)
        sleep_ms(1000)
        
        with open(os.path.join(base_dir, "../queries/pmcConditionQuery.md"), "r", encoding="utf-8") as f:
            pmc_condition_query = f.read()
        pmc_results = pmc_service.search_pmc(refined_input_data, pmc_condition_query)
        
        ctg_results = ctg_service.search_ctg(refined_input_data)
        sleep_ms(1000)
        
        combined_results = pm_results + pmc_results + ctg_results
        return {"refinedQuery": refined_input_data, "results": combined_results}
    except Exception as e:
        print("Error in search route:", str(e))
        raise HTTPException(status_code=500, detail="Server error")
