import requests
from urllib.parse import urlencode
from config import TOOL_NAME, TOOL_EMAIL
from utils import convert_pmid_to_pmcid
import json

def search_pm(refined_query: dict, pm_condition_query: str) -> list:
    try:
        query_string = refined_query.get("combined_query", "")
        condition_query = pm_condition_query or ""
        combined_query = f"{query_string} AND {condition_query}"
        combined_query = combined_query.replace("+", " ")
        print("Searching PubMed with combined query:\n", combined_query)
        
        search_params = {
            "term": combined_query,
            "retmode": "json",
            "retmax": "5",
            "db": "pubmed",
            "tool": TOOL_NAME,
            "email": TOOL_EMAIL
        }
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{urlencode(search_params)}"
        search_response = requests.get(search_url)
        
        print("PubMed search response:", json.dumps(search_response.text, indent=2))
        
        search_response.raise_for_status()
        id_list = search_response.json().get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return []
        
        summary_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json",
            "tool": TOOL_NAME,
            "email": TOOL_EMAIL
        }
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{urlencode(summary_params)}"
        summary_response = requests.get(summary_url)
        
        print("PubMed summary response:", summary_response.text)
        
        summary_response.raise_for_status()
        summary_data = summary_response.json().get("result", {})
        
        summaries = []
        for pmid in summary_data.get("uids", []):
            info = summary_data.get(pmid)
            if not info:
                continue
            doi = None
            articleids = info.get("articleids", [])
            for article in articleids:
                if article.get("idtype") == "doi":
                    doi = article.get("value")
                    break
            summaries.append({
                "source": "PM",
                "id": pmid,
                "pmid": pmid,
                "pmcid": convert_pmid_to_pmcid(pmid),
                "doi": doi,
                "title": info.get("title", "")
            })
        return summaries
    except Exception as e:
        print("PubMed API error:", str(e))
        return []
