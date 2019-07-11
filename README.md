# Impact App

Impact App is a ...

## Data Sources

### PubMed

**Scopus**. Data from Scopus were collected using the [Scopus API client](https://github.com/scopus-api/scopus) 
developed by Rose, Michael E. and John R. Kitchin.

### PubMed Central

...


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