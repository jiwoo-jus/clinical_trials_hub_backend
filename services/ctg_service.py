# ctg_service.py
import requests, logging

CT_SEARCH_URL = "https://clinicaltrials.gov/api/v2/studies"

def search_ctg(
    term,
    cond,
    intr,
    study_type=None,
    phase=None,       # 신규
    gender=None,
    ages=None,
    sponsor=None,
    location=None,
    status=None,
    date_range=None,
    page_size=20,
    page_token=None,
    sort=None
):
    # print("CTG search params:", locals())
    params = {"pageSize": page_size, "countTotal": "true", "format": "json", "sort": sort}
    if term:     params["query.term"]           = term
    if cond:     params["query.cond"]           = cond
    if intr:     params["query.intr"]           = intr
    if location: params["query.locn"]           = location
    if sponsor:  params["query.spons"]          = sponsor
    if status:   params["filter.overallStatus"] = status if isinstance(status,str) else "|".join(status)
    if page_token: params["pageToken"]          = page_token

    # aggFilters 구성
    agg = []
    if study_type: agg.append(f'studyType:{study_type}')
    if phase:      agg.append(f'phase:{phase}')
    if gender:
        code = "m" if gender.lower().startswith("m") else "f"
        agg.append(f'sex:{code}')
    if ages:       agg.append(f'ages:{ages}')
    if agg:        params["aggFilters"] = ",".join(agg)

    resp = requests.get(CT_SEARCH_URL, params=params)
    if resp.status_code != 200:
        logging.error(f"CTG API {resp.status_code} / {resp.text}")
        raise Exception("CTG API error")
    data = resp.json()

    studies   = data.get("studies", [])
    total     = data.get("totalCount") or data.get("total")
    nextToken = data.get("nextPageToken")
    print(f"CTG search: params={params}, total={total}, page_token={page_token}, page_size={page_size}")

    results = []
    for st in studies:
        idmod = st.get("protocolSection",{}).get("identificationModule",{})
        results.append({
            "source": "CTG",
            "id": idmod.get("nctId"),
            "title": idmod.get("briefTitle"),
            "status": st.get("protocolSection",{}).get("statusModule",{}).get("overallStatus"),
            "conditions": st.get("protocolSection",{}).get("conditionsModule",{}).get("conditionList",{}).get("condition",[]),
            "studyType": st.get("protocolSection",{}).get("designModule",{}).get("studyType"),
            "references": st.get("protocolSection",{}).get("referencesModule",{}).get("references",[]),
            "hasResults": st.get("hasResults",False),
            "structured_info": st,
            "score": None
        })

    return {
        "results": results,
        "total": total,
        "nextPageToken": nextToken,
        "applied_query": params
    }

def get_ctg_detail(nctId: str) -> dict:
    params = {"query.nctId": nctId, "format": "json"}
    resp = requests.get(CT_SEARCH_URL, params=params)
    if resp.status_code != 200:
        logging.error(f"CTG API {resp.status_code} / {resp.text}")
        raise Exception("CTG API error")
    arr = resp.json().get("studies", [])
    if not arr:
        raise Exception(f"No detail for {nctId}")
    return arr[0]
