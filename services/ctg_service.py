import requests

def search_ctg(refined_query: dict) -> list:
    try:
        query_string = refined_query.get("query", "")
        base_url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "query.term": query_string,
            # "fields": "NCTId,BriefTitle,OverallStatus,HasResults,protocolSection.referencesModule.references",
            "fields": "protocolSection,resultsSection,annotationSection,documentSection,derivedSection,hasResults",
            "format": "json",
            "filter.overallStatus": "COMPLETED",
            "sort": "@relevance",
            "countTotal": "true",
            "pageSize": "5"
        }
        print("Searching CTG with params:", params)
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        studies = data.get("studies", [])
        results = []
        for study in studies:
            protocol_section = study.get("protocolSection", {})
            identification_module = protocol_section.get("identificationModule", {})
            nct_id = identification_module.get("nctId", "N/A")
            title = identification_module.get("briefTitle", "No title")
            reference_module = protocol_section.get("referencesModule", {})
            references = reference_module.get("references", [])
            has_results = study.get("HasResults", False)
            results.append({
                "source": "CTG",
                "id": nct_id,
                "title": title,
                "references": references,
                "hasResults": has_results,
                "structured_info": study
            })
        return results
    except Exception as e:
        print("CTG API error:", str(e))
        return []