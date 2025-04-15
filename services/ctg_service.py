import requests, logging

CT_SEARCH_URL = "https://clinicaltrials.gov/api/v2/studies"

def search_ctg(term, cond, intr, study_type=None, gender=None, ages=None, sponsor=None, location=None, status=None, date_range=None, page_size=20, page_token=None, sort=None):
    print("CTG search params:", locals())
    params = {
        "pageSize": page_size,
        "countTotal": "true",
        "format": "json",
        "sort": sort
    }
    if term:
        params["query.term"] = term
    if cond:
        params["query.cond"] = cond
    if intr:
        params["query.intr"] = intr
    if location:
        params["query.locn"] = location
    if sponsor:
        params["query.spons"] = sponsor
    if status:
        params["filter.overallStatus"] = status if isinstance(status, str) else "|".join(status)
    if page_token:
        params["pageToken"] = page_token
    if date_range:
        print("Todo: Date range filter")  # 추후 처리
    if study_type or gender or ages:
        aggFilters = []
        if study_type:
            aggFilters.append(f'studyType:{study_type}')
        if gender:
            if gender == 'Male':
                aggFilters.append(f'sex:m')
            elif gender == 'Female':
                aggFilters.append(f'sex:f')
        if ages:
            aggFilters.append(f'ages:{ages}')
        params["aggFilters"] = ",".join(aggFilters)
    
    print("Searching CTG with params:", params)
    response = requests.get(CT_SEARCH_URL, params=params)

    if response.status_code != 200:
        logging.error(f"CTG API returned status {response.status_code}")
        logging.error(f"Response content: {response.text}")
        raise Exception("CTG API returned non-200 status")
    try:
        json_data = response.json()
    except ValueError as e:
        logging.error("Failed to decode JSON from CTG API")
        logging.error(f"Response content: {response.text}")
        raise e
    
    studies = json_data.get("studies", [])
    total = json_data.get("totalCount", None) or json_data.get("total", None)
    next_token = json_data.get("nextPageToken")
    results = []
    for study in studies:
        ident = study.get("protocolSection", {}).get("identificationModule", {})
        brief_title = ident.get("briefTitle")
        nct_id = ident.get("nctId")
        status = study.get("protocolSection", {}).get("statusModule", {}).get("overallStatus")
        conds = study.get("protocolSection", {}).get("conditionsModule", {}).get("conditionList", {}).get("condition", [])
        references = study.get("protocolSection", {}).get("referencesModule", {}).get("references", [])
        has_results = study.get("hasResults", False)
        
        results.append({
            "source": "CTG",
            "id": nct_id,
            "title": brief_title,
            "status": status,
            "conditions": conds,
            "studyType": study.get("protocolSection", {}).get("designModule", {}).get("studyType"),
            "references": references,
            "hasResults": has_results,
            "structured_info": study,
            "score": None
        })
    print("CTG search results:", {"total": total, "nextPageToken": next_token, "applied_query": params})
    return {"results": results, "total": total, "nextPageToken": next_token, "applied_query": params}

def get_ctg_detail(nctId: str) -> dict:
    params = {
        "query.nctId": nctId,
        "format": "json"
    }
    response = requests.get(CT_SEARCH_URL, params=params)
    if response.status_code != 200:
        logging.error(f"CTG API returned status {response.status_code}")
        logging.error(f"Response content: {response.text}")
        raise Exception("CTG API returned non-200 status")
    json_data = response.json()
    studies = json_data.get("studies", [])
    if not studies:
        raise Exception(f"No CTG detail found for nctId {nctId}")
    return studies[0]
