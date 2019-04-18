from Bio import Entrez
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
                        logging.error(f'Received error from server {err}')
                        logging.error(f'Attempt {attempt} of {MAX_ATTEMPTS}')
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
        return results['PubmedArticle']

    ####
    # Caveat: It only covers journals indexes for PubMed Central
    ####
    def get_paper_citations(self, pm_id):
        paper_citations = None
        handle = self.__entrez.elink(dbfrom='pubmed', db='pmc', LinkName='pubmed_pmc_refs', id=pm_id)
        results_pmc = self.__entrez.read(handle)
        handle.close()
        if len(results_pmc[0]['LinkSetDb']) > 0:
            pmc_ids = [link["Id"] for link in results_pmc[0]["LinkSetDb"][0]["Link"]]
            handle = self.__entrez.elink(dbfrom='pmc', db='pubmed', LinkName='pmc_pubmed', id=','.join(pmc_ids))
            results_pm = self.__entrez.read(handle)
            handle.close()
            if len(results_pmc[0]['LinkSetDb']) > 0:
                paper_citation_pm_ids = [link['Id'] for link in results_pm[0]['LinkSetDb'][0]['Link']]
                paper_citations = self.fetch_in_bulk_from_list(paper_citation_pm_ids)
        return paper_citations

    def get_papers_citations(self, pm_id_list):
        for pm_id in pm_id_list:
            self.get_paper_citations(pm_id)

    ####
    # Caveat: It only covers journals indexes for PubMed Central
    ####
    def get_paper_references(self, pm_id):
        paper_references = None
        handle = self.__entrez.elink(dbfrom='pubmed', linkname='pubmed_pubmed_refs', id=pm_id)
        results_pm = self.__entrez.read(handle)
        handle.close()
        if len(results_pm[0]['LinkSetDb']) > 0:
            paper_references_pm_ids = [link['Id'] for link in results_pm[0]['LinkSetDb'][0]['Link']]
            paper_references = self.fetch_in_bulk_from_list(paper_references_pm_ids)
        return paper_references

    def get_papers_references(self, pm_id_list):
        for pm_id in pm_id_list:
            self.get_paper_references(pm_id)


#if __name__ == '__main__':
#    ec = EntrezClient()
    #results = ec.search('10.1093/bioinformatics/btx420[doi]')
#    results = ec.fetch_in_bulk_from_list(['28666314'])
#    print('Done!')
#     results = ec.search('Alfonso Valencia[author]')
#     papers = ec.fetch_in_batch_from_history(results['Count'], results['WebEnv'], results['QueryKey'])
#     for i, paper in enumerate(papers):
#         print(f"{i + 1}) {paper['MedlineCitation']['Article']['ArticleTitle']} ({paper['MedlineCitation']['PMID']})")
#     # print the title of the first paper
#     # print(papers[0]['MedlineCitation']['Article']['ArticleTitle'])
#     # get citations of the first paper
#     #pm_id = papers[15]['MedlineCitation']['PMID']
#     #ec.get_paper_citations(pm_id)
#     ec.get_paper_references('28934481')
