from fastapi import APIRouter, HTTPException, Query
from utils import convert_pmid_to_pmcid

router = APIRouter()

@router.get("/convert_pmid_to_pmcid")
async def convert_pmid(pmid: str = Query(..., description="The PubMed ID (PMID) to convert.")):
    """
    Converts a PMID to its corresponding PMCID using the NCBI ID Converter API.
    """
    try:
        pmcid = convert_pmid_to_pmcid(pmid)
        if pmcid:
            return {"pmid": pmid, "pmcid": pmcid}
        else:
            # Return 404 if no PMCID is found, as it's a specific resource lookup
            raise HTTPException(status_code=404, detail=f"No PMCID found for PMID {pmid}")
    except Exception as e:
        # Log the original error for debugging
        print(f"Error in /convert_pmid_to_pmcid endpoint: {e}")
        # Raise a generic 500 error to the client
        raise HTTPException(status_code=500, detail="Internal server error during ID conversion.")
