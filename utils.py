import time
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlencode
from config import TOOL_NAME, TOOL_EMAIL

def sleep_ms(milliseconds: int):
    """Sleep for the given number of milliseconds."""
    time.sleep(milliseconds / 1000)

def extract_article_content(html: str) -> str:
    """Extract the <article> element from HTML (if present)."""
    soup = BeautifulSoup(html, 'html.parser')
    article_tag = soup.find('article')
    return str(article_tag) if article_tag else html

def convert_pmid_to_pmcid(pmid: str) -> str:
    try:
        url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
        params = {
            "ids": pmid,
            "format": "json",
            "tool": TOOL_NAME,
            "email": TOOL_EMAIL
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        records = data.get("records", [])
        if records and records[0].get("pmcid"):
            return records[0]["pmcid"]
        else:
            print(f"No PMCID found for PMID {pmid}")
            return None
    except Exception as e:
        print("Error converting PMID to PMCID:", e)
        return None

def convert_pmcid_to_pmid(pmcid: str) -> str:
    try:
        url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
        params = {
            "ids": pmcid,
            "format": "json",
            "tool": TOOL_NAME,
            "email": TOOL_EMAIL
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        records = data.get("records", [])
        if records and records[0].get("pmid"):
            return records[0]["pmid"]
        else:
            print(f"No PMID found for PMCID {pmcid}")
            return None
    except Exception as e:
        print("Error converting PMCID to PMID:", e)
        return None