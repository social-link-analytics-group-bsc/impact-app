# from elsapy.elsclient import ElsClient
# from elsapy.elssearch import ElsSearch

import bs4
import json
import logging
import requests
import pathlib
import time


logging.basicConfig(filename=str(pathlib.Path(__file__).parents[1].joinpath('impact_app.log')),
                    level=logging.DEBUG)

####
# Scopus Collector
#
# Limitation: 5000 requests per week
# Scopus covers 50 million abstracts of over 20,500
# peer-reviewed titles from more than 5,000 publishers.
# ScopusSearch: This represents a search against the SCOPUS cluster,
# which contains SCOPUS abstracts
# With my API key I can only use the search endpoint
#
####
# class ScopusClient:
#     query_ret = None
#     api_client = None
#
#     def __init__(self):
#         con_file = open('config.json')
#         config = json.load(con_file)
#         con_file.close()
#         self.client = ElsClient(config['scopus']['api_key'])
#
#     def get_author_publications_by_name(self, first_name, last_name):
#         auth_srch = ElsSearch(f"authlast({last_name})", 'author')
#         auth_srch.execute(self.client)
#         print("auth_srch has", len(auth_srch.results), "results.")


class ScopusWebCollector:
    __search_url = 'https://www.scopus.com/authid/detail.uri?authorId='

    def get_author_info(self, author_scopus_id):
        url = self.__search_url + str(author_scopus_id)
        ret_rq = requests.get(url)
        time.sleep(20)
        if ret_rq.status_code == 200:
            author_info = dict()
            dom = bs4.BeautifulSoup(ret_rq.text, 'html.parser')
            doi_link = dom.find('a', {'title': 'View this author’s ORCID profile'})
            if doi_link:
                author_info['doi'] = doi_link.contents[1].text
            h_index_panel = dom.find(id='authorDetailsHindex')
            h_index = h_index_panel.find(class_='fontLarge')
            if h_index:
                author_info['h_index'] = h_index.text
            num_papers_panel = dom.find(id='authorDetailsDocumentsByAuthor')
            num_papers = num_papers_panel.find(class_='fontLarge pull-left')
            if num_papers:
                author_info['num_papers'] = num_papers.text
            return author_info
        else:
            logging.error(f"Error {ret_rq.status_code} when trying to access the website {url}")
            return None


if __name__ == '__main__':
    swc = ScopusWebCollector()
    swc.get_author_info('16308427600')

