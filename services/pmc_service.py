import requests
from urllib.parse import urlencode
from utils import sleep_ms, extract_article_content
from utils import convert_pmcid_to_pmid
from config import TOOL_NAME, TOOL_EMAIL
import json

def search_pmc(refined_query: dict, pmc_condition_query: str) -> list:
    try:
        query_string = refined_query.get("combined_query", "")
        condition_query = pmc_condition_query or ""
        combined_query = f"{query_string} AND {condition_query}"
        combined_query = combined_query.replace("+", " ")
        print("Searching PMC with combined query:\n", combined_query)
        
        sleep_ms(1000)
        search_params = {
            "term": combined_query,
            "retmode": "json",
            "retmax": "5",
            "db": "pmc"
        }
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{urlencode(search_params)}"
        search_response = requests.get(search_url)
        
        print("PMC search response:", json.dumps(search_response.text, indent=2))
        
        search_response.raise_for_status()
        id_list = search_response.json().get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return []
        sleep_ms(1000)
        summary_params = {
            "db": "pmc",
            "id": ",".join(id_list),
            "retmode": "json"
        }
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{urlencode(summary_params)}"
        summary_response = requests.get(summary_url)
        summary_response.raise_for_status()
        summary_data = summary_response.json().get("result", {})
        
        summaries = []
        for pmcid in summary_data.get("uids", []):
            info = summary_data.get(pmcid)
            if not info:
                continue
            doi = None
            articleids = info.get("articleids", [])
            for article in articleids:
                if article.get("idtype") == "doi":
                    doi = article.get("value")
            pmcid = "PMC" + pmcid
            summaries.append({
                "source": "PMC",
                "id": pmcid,
                "pmid": convert_pmcid_to_pmid(pmcid),
                "pmcid": pmcid,
                "doi": doi,
                "title": info.get("title", "")
            })
        return summaries
    except Exception as e:
        print("PMC API error:", str(e))
        return []

def get_pmc_full_text_xml(pmcid: str) -> str:
    try:
        print(f"[get_PMC_xml] Using PMCID: {pmcid}")
        params = {
            "db": "pmc",
            "id": pmcid.replace("PMC", ""),
            "retmode": "xml",
            "tool": TOOL_NAME,
            "email": TOOL_EMAIL
        }
        efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urlencode(params)
        response = requests.get(efetch_url)
        response.raise_for_status()
        raw_xml = response.text
        return raw_xml
    except Exception as e:
        print("PMC full text API error:", str(e))
        return "Error retrieving full text."

def get_pmc_full_text_html(pmcid: str) -> str:
    try:
        print(f"[get_PMC_html] Using PMCID: {pmcid}")
        url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        full_html = response.text
        article_html = extract_article_content(full_html)
        return article_html
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return f"Error retrieving article detail: {http_err}"
    except Exception as e:
        print("Error fetching article HTML from PMC:", str(e))
        return "Error retrieving article detail."
