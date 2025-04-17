import requests
from urllib.parse import urlencode
from config import TOOL_NAME, TOOL_EMAIL
# Remove the import for convert_pmid_to_pmcid as it's no longer needed here
# from utils import convert_pmid_to_pmcid
from bs4 import BeautifulSoup
import time
import re # Import the re module for regex matching

NCBI_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def search_pm(combined_query, condition_query=None, journal=None, sex=None, age=None, date_from=None, date_to=None, page=1, page_size=10, sort='relevance', sort_order=None):
    try:
        # Build the search term
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
            # Default date range if not provided
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
            "sort": sort,
            "sort_order": sort_order,
        }
        print("Searching PubMed with combined query:\n", search_params)
        search_response = requests.get(NCBI_ESEARCH, params=search_params).json()
        id_list = search_response["esearchresult"]["idlist"]
        print("PubMed search response:", search_response)
        total = int(search_response["esearchresult"]["count"])
        print("Total results:", total, "PMIDs:", id_list)
        
        if not id_list:
            print("No results found in PubMed.")
            return {"results": [], "total": 0, "page": page, "page_size": page_size, "applied_query": term}

        # Retrieve summary details for the PMIDs (as before)
        summary_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json",
            "sort": sort,
            "sort_order": sort_order,
        }
        summary_response = requests.get(NCBI_ESUMMARY, params=summary_params).json()

        # -----------------------
        # New implementation: Fetch abstracts for all PMIDs at once using efetch
        efetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml"
        }
        # Optional pause to avoid hitting rate limits
        time.sleep(0.5)
        efetch_response = requests.get(NCBI_EFETCH, params=efetch_params)
        abstract_dict_by_pmid = {}  # To map each PMID to its parsed abstract

        if efetch_response.status_code == 200:
            efetch_xml = efetch_response.text
            soup = BeautifulSoup(efetch_xml, "xml")
            # Loop through each article element
            for article in soup.find_all("PubmedArticle"):
                pmid_tag = article.find("PMID")
                if not pmid_tag:
                    continue
                current_pmid = pmid_tag.text
                abstract_tag = article.find("Abstract")
                if abstract_tag:
                    # If there are multiple AbstractText elements, combine into a dictionary.
                    # If a label is provided, use it as the key; otherwise, use the default key "".
                    abstract_contents = {}
                    for abstract_text in abstract_tag.find_all("AbstractText"):
                        label = abstract_text.get("Label")
                        text = abstract_text.get_text(separator=" ", strip=True)
                        if label:
                            if label in abstract_contents:
                                abstract_contents[label] += " " + text
                            else:
                                abstract_contents[label] = text
                        else:
                            if "" in abstract_contents:
                                abstract_contents[""] += " " + text
                            else:
                                abstract_contents[""] = text
                    abstract_dict_by_pmid[current_pmid] = abstract_contents
                else:
                    abstract_dict_by_pmid[current_pmid] = None
        else:
            print(f"Error fetching abstracts via efetch: {efetch_response.status_code}")
        # -----------------------

        # Build the final results list
        results = []
        for pmid, info in summary_response["result"].items():
            if pmid == "uids":
                continue

            # Extract PMCID from articleids in esummary response
            pmcid_value = None
            article_ids = info.get("articleids", [])
            id_type_priority = ["pmc", "pmcid"] # Prioritize 'pmc' then 'pmcid'

            for id_type in id_type_priority:
                for article_id in article_ids:
                    if article_id.get("idtype") == id_type:
                        value = article_id.get("value")
                        # Check if the value matches the PMC format (PMC followed by digits)
                        match = re.match(r'PMC\d+', value)
                        if match:
                            pmcid_value = match.group(0) # Extract the matched PMC ID
                            break # Found a valid PMCID, stop checking this item's IDs
                if pmcid_value:
                    break # Found a valid PMCID from the prioritized list, stop checking types

            # Fallback check for 'pmc-id:' format if not found yet
            if not pmcid_value:
                 for article_id in article_ids:
                    if article_id.get("idtype") == "pmcid": # Check 'pmcid' type again for the specific format
                        value = article_id.get("value")
                        # Look for 'pmc-id: PMC...' pattern
                        match = re.search(r'pmc-id:\s*(PMC\d+)', value)
                        if match:
                            pmcid_value = match.group(1) # Extract the PMC ID part
                            break
                 if pmcid_value:
                     print(f"Extracted PMCID {pmcid_value} using fallback 'pmc-id:' pattern for PMID {pmid}")


            results.append({
                "source": "PM",
                "id": pmid,
                "pmid": pmid,
                # Use the extracted pmcid_value
                "pmcid": pmcid_value,
                "title": info.get("title"),
                "journal": info.get("fulljournalname"),
                "authors": [au.get("name") for au in info.get("authors", [])],
                "pubDate": info.get("pubdate"),
                "score": None,  # PubMed API does not provide a relevance score
                "abstract": abstract_dict_by_pmid.get(pmid),
                # Add doi if available in articleids
                "doi": next((item.get("value") for item in article_ids if item.get("idtype") == "doi"), None)
            })
        return {"results": results, "total": total, "page": page, "page_size": page_size, "applied_query": term}
    except Exception as e:
        print("PubMed API error:", str(e))
        return {"results": [], "total": 0, "page": page, "page_size": page_size, "applied_query": term}
