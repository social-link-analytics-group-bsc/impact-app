from hammock import Hammock as GendreAPI

import gender_guesser.detector as gender
import json
import logging


# Get configuration from file
def get_config(config_file):
    with open(str(config_file), 'r') as f:
        config = json.loads(f.read())
    return config


def get_gender(full_name):
    gendre_api = GendreAPI("http://api.namsor.com/onomastics/api/json/gendre")
    gendre_api2 = gender.Detector(case_sensitive=False)

    first_name = full_name.split()[0]
    last_name = full_name.split()[-1]
    resp = gendre_api(first_name, last_name).GET()
    try:
        author_gender = resp.json().get('gender')
        if author_gender == 'unknown':
            logging.info('Trying to get the author\'s gender using the second api')
            # if the main api returns unknown gender, try with another api
            author_gender = gendre_api2.get_gender(first_name)
            author_gender = 'unknown' if author_gender == 'andy' else author_gender
        return author_gender
    except:
        return 'error_api'


def curate_affiliation_name(affiliation_raw):
    affiliation_clean = affiliation_raw.replace(' and ', ' ').rstrip(',').lstrip(',').rstrip('\t').lstrip('\t').\
        rstrip('.')
    affiliation_clean = ' '.join(affiliation_clean.split())  # remove duplicate whitespaces and newline characters
    return affiliation_clean