import os
from fastapi import APIRouter, HTTPException, Request
from services import openai_service, pm_service, pmc_service, ctg_service

from utils import sleep_ms

router = APIRouter()

@router.post("/")
async def search(request: Request):
    try:
        data = await request.json()
        user_query = data.get("userQuery", "")
        print("Received userQuery:", user_query)
        
        refined_query = openai_service.refine_query(user_query)
        print("Refined Query:", refined_query)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "../queries/pmConditionQuery.md"), "r", encoding="utf-8") as f:
            pm_condition_query = f.read()
        pm_results = pm_service.search_pm(refined_query, pm_condition_query)
        sleep_ms(1000)
        
        with open(os.path.join(base_dir, "../queries/pmcConditionQuery.md"), "r", encoding="utf-8") as f:
            pmc_condition_query = f.read()
        pmc_results = pmc_service.search_pmc(refined_query, pmc_condition_query)
        
        ctg_results = ctg_service.search_ctg(refined_query)
        sleep_ms(1000)
        
        combined_results = pm_results + pmc_results + ctg_results
        return {"refinedQuery": refined_query, "results": combined_results}
    except Exception as e:
        print("Error in search route:", str(e))
        raise HTTPException(status_code=500, detail="Server error")
