from elsapy.elsclient import ElsClient
from elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elssearch import ElsSearch

import json
import scholarly


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
class ScopusClient:
    query_ret = None
    api_client = None

    def __init__(self):
        con_file = open('scopus_config.json')
        config = json.load(con_file)
        con_file.close()
        self.client = ElsClient(config['apikey'])

    def get_author_publications_by_name(self, first_name, last_name):
        auth_srch = ElsSearch(f"authlast({last_name})", 'author')
        auth_srch.execute(self.client)
        print("auth_srch has", len(auth_srch.results), "results.")


####
# Google Scholar collector
#
# Discussion about Google Scholar ToS
# https://academia.stackexchange.com/questions/34970/how-to-get-permission-from-google-to-use-google-scholar-data-if-needed
####
class GScholarClient:
    def __init__(self):
        pass

    def get_author_publication_by_name(self, first_name, last_name):
        search_query = scholarly.search_author(f"{first_name} {last_name}")
        author = next(search_query).fill()
        publication_list = [pub.bib['title'] for pub in author.publications]
        # Take a closer look at the first publication
        most_popular_pub = author.publications[3].fill()
        # Which papers cited the most popular publication?
        citations_most_popular = most_popular_pub.get_citedby()
        citation_titles = []
        for citation in citations_most_popular:
            citation_titles.append(citation.bib['title'])
        pass


# TODO: Add PubMed collector


# TODO: Add WoS collector


if __name__ == '__main__':
    #sc = ScopusClient()
    #sc.get_author_publications_by_name('Alfonso', 'Valencia')
    #res = r.query_ret
    gs = GScholarClient()
    gs.get_author_publication_by_name('Alfonso', 'Valencia')
