import requests

def search_ctg(refined_input_data: dict) -> list:
    try:
        base_url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "query.term": refined_input_data.get("other_term", ""),
            "query.cond": refined_input_data.get("cond", ""),
            "query.intr": refined_input_data.get("intr", ""),
            "fields": "protocolSection,resultsSection,annotationSection,documentSection,derivedSection,hasResults",
            "format": "json",
            "filter.overallStatus": "COMPLETED",
            "sort": "@relevance",
            "countTotal": "true",
            "pageSize": "5"
        }
        print("Searching CTG with params:", params)
        response = requests.get(base_url, params=params)
        
        print("CTG search response:", response.text)
        
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
