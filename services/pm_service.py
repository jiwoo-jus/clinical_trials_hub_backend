import requests
from urllib.parse import urlencode
from config import TOOL_NAME, TOOL_EMAIL
from utils import convert_pmid_to_pmcid, get_pm_abstract
import json

NCBI_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

def search_pm(combined_query, condition_query=None, journal=None, sex=None, age=None, date_from=None, date_to=None, page=1, page_size=10, sort="relevance"):
    try:
        term = combined_query.replace("+", " ")
        if condition_query:
            term += f" AND {condition_query}"
        if journal:
            term += f' AND "{journal}"[ta]'
        if sex:
            term += f' AND {sex}[filter]'
        if age:
            term += f' AND {age}[filter]'
        if date_from or date_to:
            # Format dates as YYYY/MM/DD
            df = date_from or "1800/01/01"
            dt = date_to or "3000/01/01"
            term += f' AND ({df}:{dt}[dp])'
        retstart = (page - 1) * page_size
        search_params = {
            "db": "pubmed",
            "term": term,
            "retmode": "json",
            "retstart": retstart,
            "retmax": page_size,
            "sort": sort
        }
        print("Searching PubMed with combined query:\n", search_params)
        search_response = requests.get(NCBI_ESEARCH, params=search_params).json()
        id_list = search_response["esearchresult"]["idlist"]
        total = int(search_response["esearchresult"]["count"])
        print("PubMed search response:", total, id_list)
        if not id_list:
            print("No results found in PubMed.")
            return {"results": [], "total": 0, "page": page, "page_size": page_size, "applied_query": term}
        
        summary_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json"
        }
        summary_response = requests.get(NCBI_ESUMMARY, params=summary_params).json()
        print("PubMed summary response:", summary_response)
        
        
        results = []
        for pmid, info in summary_response["result"].items():
            if pmid == "uids": 
                continue
            results.append({
                "source": "PM",
                "id": pmid,
                "pmid": pmid,
                "pmcid": convert_pmid_to_pmcid(pmid),
                "title": info.get("title"),
                "journal": info.get("fulljournalname"),
                "authors": [au.get("name") for au in info.get("authors", [])],
                "pubDate": info.get("pubdate"),
                "score": None,  # (PubMed API doesn’t return a numeric relevance score; can leave None or compute if needed)
                "abstract": get_pm_abstract(pmid)
            })    
        return {"results": results, "total": total, "page": page, "page_size": page_size, "applied_query": term}
    except Exception as e:
        print("PubMed API error:", str(e))
        return {"results": [], "total": 0, "page": page, "page_size": page_size, "applied_query": term}
