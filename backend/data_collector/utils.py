from hammock import Hammock as GendreAPI

import gender_guesser.detector as gender
import json
import logging
import re


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


def curate_text(raw_text):
    regex_l = re.compile('^[0-9]+')  # leading numbers
    regex_t = re.compile('[0-9]+$')  # trailing numbers
    clean_text = regex_l.sub('', raw_text)
    clean_text = regex_t.sub('', clean_text)
    clean_text = clean_text.replace(' and ', ' ')
    clean_text = clean_text.strip()
    clean_text = clean_text.rstrip(',')
    clean_text = clean_text.lstrip(',')
    clean_text = clean_text.rstrip('\t')
    clean_text = clean_text.lstrip('\t')
    clean_text = clean_text.rstrip('.')
    # remove duplicate whitespaces and newline characters
    clean_text = ' '.join(clean_text.split())
    return clean_text
