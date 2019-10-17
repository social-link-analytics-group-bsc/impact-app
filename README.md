# Impact App

Impact App is a work-in-progress tool developed by the [Social and Media Impact Evaluation group](https://www.bsc.es/discover-bsc/organisation/scientific-structure/social-and-media-impact-evaluation) 
of the [Barcelona Supercomputing Center](https://www.bsc.es) with the goal of assist organizations and scholars to
understand the scientific and social impact of the research projects.

![ImpactApp Front Page](/screenshots/front_page.png)

## Scientific Impact

Impact App applies a normalized 

## Social Impact

...

## Data Sources

Currently, the primary sources of data are [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/) and [PubMedCentral (PMC)](https://www.ncbi.nlm.nih.gov/pmc/). 
The API of these sources are hit through [Biopython](https://biopython.org/), a PubMed API client.

## Impact App in Action

Starting from a set of researcher names, ImpactApp queries the API of PubMed and PubMedCentral to collect information
about the articles authored by the given researchers. With these data, the tool computes the scientific impact following
the methodology mentioned before. The results of this computation is displayed in a dashboard.


## Installation

1. Run `git clone https://github.com/social-link-analytics-group-bsc/impact-app.git`

2. Get into the directory impact-app

3. Create a virtual environment `virtualenv env` ([instructions](https://www.linode.com/docs/development/python/create-a-python-virtualenv-on-ubuntu-1610/) on how to install virtualenv on Ubuntu)

4. Activate the virtual environment `source env/bin/activate`

5. Get into the directory backend

6. Execute `pip install -r requirements.txt` to install dependencies. If an error occurs during the installation, it 
might be because some of these reasons: a) package python-dev is missing; b) package libmysqlclient-dev is missing c) 
the environment variables LC_ALL and/or LC_CTYPE are not defined or do not have a valid value

7. Create...