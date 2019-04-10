from Bio import Entrez
from Bio import Medline
from urllib.error import HTTPError
from data_collector.utils import get_config


import logging
import pathlib
import time


logging.basicConfig(filename=str(pathlib.Path(__file__).parents[1].joinpath('impact_app.log')),
                    level=logging.DEBUG)

class EntrezClient:
    __entrez = None

    def __init__(self):
        config_file = get_config('config.json')
        self.__entrez = Entrez
        self.__entrez.email = config_file['pubmed']['email']
        self.__entrez.api_key = config_file['pubmed']['api_key']

    def search(self, query):
        handle = self.__entrez.esearch(db='pubmed', sort='relevance', retmode='xml',
                                       usehistory='y', term=query)
        results = self.__entrez.read(handle)
        handle.close()
        return results

    def fetch_in_batch_from_history(self, num_results_to_fetch, webenv, query_key,
                                    batch_size=20):
        MAX_ATTEMPTS = 5
        results = []
        num_results_to_fetch = int(num_results_to_fetch)
        out_handle = open('recent_orchid_papers.txt', "w")
        for start in range(0, num_results_to_fetch, batch_size):
            end = min(num_results_to_fetch, start + batch_size)
            logging.info(f"Downloading records from {start+1} to {end}")
            attempt = 0
            while attempt < MAX_ATTEMPTS:
                attempt += 1
                try:
                    handle = self.__entrez.efetch(db='pubmed', retmode='xml',
                                                  rettype='medline', retstart=start,
                                                  retmax=batch_size, webenv=webenv,
                                                  query_key=query_key)
                except HTTPError as err:
                    if 500 <= err.code <= 599:
                        logging.error(f"Received error from server {err}")
                        logging.error(f"Attempt {attempt} of {MAX_ATTEMPTS}")
                        time.sleep(15)
                    else:
                        raise
            records = Entrez.read(handle)
            for record in records['PubmedArticle']:
                results.append(record)
        return results

    def fetch_in_bulk_from_list(self, id_list):
        ids = ','.join(id_list)
        handle = self.__entrez.efetch(db='pubmed', retmode='xml', id=ids)
        results = self.__entrez.read(handle)
        return results

    #def get_paper_citations(id):
    #    handle = Entrez.elink(dbfrom="pubmed", id=id, linkname="pubmed_pubmed")
    #    record = Entrez.read(handle)
    #    handle.close()
    #    print(record[0]["LinkSetDb"][0]["LinkName"])
    #    linked = [link["Id"] for link in record[0]["LinkSetDb"][0]["Link"]]
    #    pass


if __name__ == '__main__':
    ec = EntrezClient()
    results = ec.search('Alfonso Valencia[author]')
    #id_list = results['IdList']
    #get_paper_citations(id_list[0])
    #papers = fetch_summary(id_list)
    papers = ec.fetch_in_batch_from_history(results['Count'], results['WebEnv'], results['QueryKey'])
    for i, paper in enumerate(papers):
        print(f"{i + 1}) {paper['MedlineCitation']['Article']['ArticleTitle']}")
