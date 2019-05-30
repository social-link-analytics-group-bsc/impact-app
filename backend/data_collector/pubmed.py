from Bio import Entrez
from collections import defaultdict
from django.conf import settings
from urllib.error import HTTPError
from data_collector.utils import get_config


import logging
import time


logger = logging.getLogger(__name__)


class EntrezClient:
    __entrez = None

    def __init__(self, read_config_from_settigs=True):
        if read_config_from_settigs:
            config = settings.PUBMED_API
        else:
            config = get_config('config.json')
        self.__entrez = Entrez
        self.__entrez.email = config['email']
        self.__entrez.api_key = config['api_key']

    def search(self, query, db='pubmed', use_history=True, batch_size=20):
        if use_history:
            handle = self.__entrez.esearch(db=db, sort='relevance', retmode='xml',
                                           usehistory='y', term=query, retmax=batch_size)
        else:
            handle = self.__entrez.esearch(db=db, sort='relevance', retmode='xml',
                                           term=query, retmax=batch_size)
        results = self.__entrez.read(handle)
        handle.close()
        return results

    def fetch_in_batch_from_history(self, num_results_to_fetch, webenv, query_key,
                                    db='pubmed', batch_size=20):
        MAX_ATTEMPTS = 5
        results = []
        num_results_to_fetch = int(num_results_to_fetch)
        for start in range(0, num_results_to_fetch, batch_size):
            end = min(num_results_to_fetch, start + batch_size)
            logger.info(f"Downloading records from {start + 1} to {end}")
            attempt = 0
            while attempt < MAX_ATTEMPTS:
                attempt += 1
                try:
                    handle = self.__entrez.efetch(db=db, retmode='xml',
                                                  rettype='medline', retstart=start,
                                                  retmax=batch_size, webenv=webenv,
                                                  query_key=query_key)
                except HTTPError as err:
                    if 500 <= err.code <= 599:
                        logger.error(f"Received error from server {err}")
                        logger.error(f"Attempt {attempt} of {MAX_ATTEMPTS}")
                        time.sleep(15)
                    else:
                        raise
            records = self.__entrez.read(handle)
            for record in records['PubmedArticle']:
                results.append(record)
        return results

    def fetch_in_bulk_from_list(self, id_list, db='pubmed'):
        ids = ','.join(id_list)
        handle = self.__entrez.efetch(db=db, rettype='medline', retmode='xml', id=ids)
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
        citations = defaultdict(list)
        for pm_id in pm_id_list:
            citations[pm_id] = self.get_paper_citations(pm_id)
        return citations

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
        references = defaultdict(list)
        for pm_id in pm_id_list:
            references[pm_id] = self.get_paper_references(pm_id)
        return references


#if __name__ == '__main__':
#    ec = EntrezClient(False)
#    paper_citations = ec.get_paper_citations('23202358')
#    paper_references = ec.get_paper_references('23202358')
#    print('done!')
    #results = ec.search('10.1074/jbc.m105766200[doi]')
#    results = ec.fetch_in_bulk_from_list(['28666314'])
#    print('Done!')
#     results = ec.search('M Carmen Arilla[author]')
#     papers = ec.fetch_in_batch_from_history(results['Count'], results['WebEnv'], results['QueryKey'])
#     for i, paper in enumerate(papers):
#         print(f"{i + 1}) {paper['MedlineCitation']['Article']['ArticleTitle']} ({paper['MedlineCitation']['PMID']})")
#         print(str(paper['MedlineCitation']['Article']['PublicationTypeList'][0]))
#         print(str(paper['MedlineCitation']['Article']['Journal']['ISSN']))
#         print(str(paper['MedlineCitation']['Article']['Journal']['JournalIssue']['Issue']))
#         print(str(paper['MedlineCitation']['Article']['Journal']['JournalIssue']['Volume']))
#         print(int(paper['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']['Year']))
#         print(str(paper['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']['Month']))
#         print(int(paper['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']['Day']))
#     # print the title of the first paper
#     # print(papers[0]['MedlineCitation']['Article']['ArticleTitle'])
#     # get citations of the first paper
#     #pm_id = papers[15]['MedlineCitation']['PMID']
#     #ec.get_paper_citations(pm_id)
#     ec.get_paper_references('28934481')
