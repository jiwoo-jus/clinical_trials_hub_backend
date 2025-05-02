# pm_service.py
import requests
from bs4 import BeautifulSoup
import time
import re

NCBI_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def search_pm(
    combined_query,
    condition_query=None,
    publicationType=None,  # 신규
    journal=None,
    sex=None,
    age=None,
    date_from=None,
    date_to=None,
    page=1,
    page_size=10,
    sort='relevance',
    sort_order=None
):
    try:
        term = combined_query.replace("+", " ")
        if condition_query:
            term += f" AND {condition_query}"
        if publicationType:
            term += f' AND "{publicationType}"[Publication Type]'
        if journal:
            term += f' AND "{journal}"[ta]'
        if sex:
            term += f' AND {sex}[filter]'
        if age:
            term += f' AND {age}[filter]'
        if date_from or date_to:
            df = date_from or "1800/01/01"
            dt = date_to   or "3000/01/01"
            term += f' AND ({df}:{dt}[dp])'

        retstart = (page - 1) * page_size
        params = {
            "db": "pubmed", "term": term, "retmode": "json",
            "retstart": retstart, "retmax": page_size,
            "sort": sort, "sort_order": sort_order
        }
        search_resp = requests.get(NCBI_ESEARCH, params=params).json()
        id_list = search_resp["esearchresult"]["idlist"]
        total   = int(search_resp["esearchresult"]["count"])
        print(f"PubMed search: term={term}, total={total}, page={page}, page_size={page_size}")

        if not id_list:
            return {"results": [], "total": 0, "page": page, "page_size": page_size, "applied_query": term}

        # Summary
        summary_resp = requests.get(NCBI_ESUMMARY, params={
            "db":"pubmed","id":",".join(id_list),"retmode":"json",
            "sort": sort,"sort_order": sort_order
        }).json()

        # Abstracts via efetch
        time.sleep(0.5)
        efetch_resp = requests.get(NCBI_EFETCH, params={
            "db":"pubmed","id":",".join(id_list),"retmode":"xml"
        })
        abstr = {}
        if efetch_resp.status_code == 200:
            soup = BeautifulSoup(efetch_resp.text, "xml")
            for art in soup.find_all("PubmedArticle"):
                pmid = art.find("PMID")
                if not pmid: continue
                pid = pmid.text
                abs_tag = art.find("Abstract")
                if abs_tag:
                    d = {}
                    for at in abs_tag.find_all("AbstractText"):
                        lbl = at.get("Label") or ""
                        txt = at.get_text(" ", strip=True)
                        d[lbl] = d.get(lbl, "") + txt
                    abstr[pid] = d
                else:
                    abstr[pid] = None

        results = []
        for pmid, info in summary_resp["result"].items():
            if pmid == "uids": continue
            pmcid = None
            for aid in info.get("articleids", []):
                if aid.get("idtype","").lower() in ("pmc","pmcid"):
                    m = re.match(r'PMC\d+', aid.get("value",""))
                    if m:
                        pmcid = m.group(0)
                        break
            results.append({
                "source": "PM",
                "id": pmid,
                "pmid": pmid,
                "pmcid": pmcid,
                "title": info.get("title"),
                "journal": info.get("fulljournalname"),
                "authors": [a.get("name") for a in info.get("authors",[])],
                "pubDate": info.get("pubdate"),
                "score": None,
                "abstract": abstr.get(pmid),
                "doi": next((i.get("value") for i in info.get("articleids",[]) if i.get("idtype")=="doi"), None)
            })

        return {"results": results, "total": total, "page": page, "page_size": page_size, "applied_query": term}

    except Exception as e:
        print("PubMed API error:", str(e))
        return {"results": [], "total": 0, "page": page, "page_size": page_size, "applied_query": term}
