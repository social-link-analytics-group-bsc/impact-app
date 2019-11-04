# Impact App

Impact App is a work-in-progress tool developed by the [Social and Media Impact Evaluation group](https://www.bsc.es/discover-bsc/organisation/scientific-structure/social-and-media-impact-evaluation) 
of the [Barcelona Supercomputing Center](https://www.bsc.es) with the goal of assist organizations and scholars to
measure the scientific and social impact of their research projects.

![ImpactApp Front Page](/screenshots/front_page.png)

## Scientific Impact

By **scientific impact**, we understand the intellectual contribution to a person’s field of study within academia [[1](https://watermark.silverchair.com/rvt021.pdf?token=AQECAHi208BE49Ooan9kkhW_Ercy7Dm3ZL_9Cf3qfKAc485ysgAAAmkwggJlBgkqhkiG9w0BBwagggJWMIICUgIBADCCAksGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMRj2dd7F4L_cwKEUSAgEQgIICHNp6KnbAQrD7D0xXXvl6LkGQRmKhXYFdTks1uib8Y7xIAb5ast0nr_XaXF0FSm9vyO7KDVmL2-7LdsIdfMiBzu32uuWh1LdgF7YSlg0-nfyNWT5LAPC0sGNAFq4Pg9Zq2VJUwEGO8P1qqYS2rTyXiy_5TbWKwssQ2tDQLU4U3PY4a-n_2N4pvRse2hErI1R2ozB2DpuauH8uPU3TsJog_vK_DJ59-vMM4hcl-QbDpj4iuEmaBXBOdA428WAWZ_A3kvXYL4C2E8z4ugB0--NYD6GU9Qq_5igyA4NvovxL10-P19K4EUE2-ilUF5qOoFWC_ZbyD_ILlsdVGhQ8yiy0y6cEeuyvX8gG5kwyIrFQkfpz1MNUtsuQ8vR9DuJ3CbPHHitxznIEjy1WJBSHzUnG8niknBWJ8PF0tnMw4w1nIvpUn1Ebk8Gd_e2rdblSTxhrxTkmbK3uuHmveR2fzoI4nsCL_OOU9RCPTULkqFLZH8x1JnGC4CcNINQZuCAQOedVb4Rdhe_agXcOdYDwuK6dAc1BUaDPGWZEk-Vt3WMGppQGR52hPL3c6VR-KMS8zFQaOBZwcyzIoLBAg1vvbRfMNbJdUpSpC-5JiWqgU0ElnnHU2-B219-Vvw1jH2CEZwKWHfdqSPN_4LniU6fzyDWI8JEwVBZUFrxZ9bJqemL2iu6s2G5jhCOi2mE1uZ3hzyFEGRDO0Ys2RXIRUWh8dQ)].
Within the various methods proposed in the literature to measure the scientific impact of research (e.g., [[2](https://bura.brunel.ac.uk/bitstream/2438/7048/4/Fulltext.pdf)], 
[[3](https://academic.oup.com/rev/article/25/3/264/2364634)], [[4](https://www.researchgate.net/profile/Marc_Luwel/publication/226564764_The_Use_of_Input_Data_in_the_Performance_Analysis_of_RD_Systems/links/00b7d51834c299d9a9000000/The-Use-of-Input-Data-in-the-Performance-Analysis-of-R-D-Systems.pdf)]), 
we decided to employ the method called *normalized impact of the scientific production*, which is the methodology employed
by the government of Spain to understand the impact of publications authored by scholars working in the country's research 
institutions [[5](http://www.ciencia.gob.es/stfls/MICINN/Ayudas/PE_2017_2020/PE_Generacion_Conocimiento_Fortalecimiento_Cientifico_Tecnologico/Subprograma_Fortalecimiento_Institucional/FICHEROS/Centros_Excelencia_Severo_Ochoa_y_Unidades_Excelencia_Maria_Maeztu_2018/Calculo_IN_definitivo.pdf)].

### Indicators

| Name                                  | Description                                                                                                                                               |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Number of publications (NP)           | Number of papers published by the organization (or researcher). Papers are considered normal articles published in journals and in conference proceedings |
| Number of citations (C)               | Total citations received by NP                                                                                                                            |
| Mean of citations per paper (CPP)     | Average number of citations per publications                                                                                                              |
| Percentage of not-cited papers (%ncP) | Proportion of papers that did not receive citations                                                                                                       |
| Percentage of self-citation (%sc)     | Proportion of citations in which the list of authors of the citing paper match the list of authors of the cited paper                                     |

To understand whether a certain number of citations or a specific value of citations per publication is low or high, we 
compare them against some reference value. The following indicators are the international reference values used 
to normalize the assessment of scientific impact.

| Name                                  | Description                                                                                                                                               |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Mean of field citation score (FCS)    | Average of citations of all papers published in all journals of the field in which the institute has been active                                          |
| CPP/FCS                               | Whether or not the average citations per publications is above (or below) the international average in the field                                          |

The mean of citations by field and year can be obtained from the annual [report](https://www.recursoscientificos.fecyt.es/servicios/indices-de-impacto) 
of Elsevier.

### Methodology
 
1. Select the range of years of evaluation. There should be at least four years between the current year and the final 
year of the evaluation period. The average "peak" in the number of citations happens in the third to a fourth-year after 
publication. A five-year period is then appropriate for impact evaluation [[2](https://bura.brunel.ac.uk/bitstream/2438/7048/4/Fulltext.pdf)];
2. Compute the indicators for each year in the selected range;
3. Evaluate how the institution performs within its field of activity.

### Illustrative Example

Evaluate the scientific impact of a research institute between 2012 and 2015.

| Year | NP | C   | CCP | %Pnc | %sc | FCS | CPP/FCS |
|------|----|-----|-----|------|-----|-----|---------|
| 2012 | 70 | 450 | 6.2 | 3    | 7   | 3.1 | 2       |
| 2013 | 78 | 370 | 4.7 | 5    | 6   | 3.6 | 1.3     |
| 2014 | 81 | 407 | 5.0 | 7    | 8   | 3.5 | 1.4     |
| 2015 | 84 | 463 | 5.5 | 4    | 6   | 3.8 | 1.5     |

### Data Sources

Currently, the primary sources of data are [PubMed](https://www.ncbi.nlm.nih.gov/pubmed/) and [PubMedCentral (PMC)](https://www.ncbi.nlm.nih.gov/pmc/). 
The API of these sources are hit through [Biopython](https://biopython.org/)—a PubMed API client.

## Social Impact

Social impact is the social improvements achieved as a consequence of implementing the results of a particular research 
project or program. The computation of social impact is conducted by applying the Impact methodology proposed to monitor
the impact of projects funded by the European Union [[6](https://research.vu.nl/en/publications/monitoring-the-impact-of-eu-framework-programmes)].

### Indicators

1. **Connection** to UN Sustainable Development Goals, EU2020 targets or other similar official targets;
2. Percentage of **improvement** achieved concerning the starting situation;
3. **Transferability** of the impact. The actions developed based on the project's findings have been transferred to other 
contexts besides the original one;
4. **Social impact published** on scientific journals (with recognized impact), governmental or non-governmental 
official bodies;
5. **Sustainability**. The impact achieved by the action developed based on the project’s findings has shown to be sustainable throughout time

### Illustrative Example

| Organization  | Project    | SDG (UN 2030) [1] | % of Improvement achieved [2] | Description of achievement [3]           | Sustainability [4] | Replicability [5] | Social impact report | Score-Impact [6] |
|---------------|------------|---------------|---------------------------|--------------------------------------|----------------|---------------|----------------------|--------------|
| Institution A | Project AA | Poverty       | 5%                        | Reduce families in poverty situation | No             | No            | Scientific acticle   | 4            |
|               | Project BB | Health        | 21%                       | Reduce dengue contagion              | Yes            | Yes           | Official report      | 9            |

[1] Respond to at least one of the 2030 United Nations Social Development Goal (or other similar official social goals 
like EU2020)

[2] Percentage of the improvement achieved as a result of the actions taken during the programme execution

[3] Textual description of the achievement 

[4] Evidences of the impact after the end of the project life span (Yes/No)

[5] Whether the programme has been implemented in more than one place (city, region, country) (Yes/No)

[6] The score of each impact is assigned according to the criteria that it fulfils:

* 10: The impact meets all the criteria, and has more than 30% of improvement
* 9: The impact meets all the criteria, and has more than 20% of improvement
* 8: The impact meets all the criteria, and has more than 10% of improvement
* 7: The impact meets all the criteria, and has some % of improvement (not available the specific %)
* 6: The impact responds to UN2030 strategy objectives, has achieved some % of improvement and meets at least 2 of the other criteria
* 5: The impact responds to UN2030 strategy objectives, has achieved some % of improvement and meets at least 1 of the other criteria
* 4: The impact responds to UN2030 strategy objectives and has achieved some % of improvement 
* 3: The impact responds to other societal objectives, has achieved some % of improvement and meets at least 2 of the other criteria
* 2: The impact responds to other societal objectives, has achieved some % of improvement and meets at least 1 of the other criteria
* 1: The impact responds to other societal objectives and has achieved some % of improvement

## Impact App in Action

Starting from a group of researcher names, ImpactApp queries the API of PubMed and PubMedCentral to collect information
about the articles authored by the given researchers. With this data, the tool computes the scientific impact following
the methodology mentioned before. The results of this computation are graphically displayed in dashboards, as shown in the
next figures.

### Screenshots

![Initial Dashboard](/screenshots/dashboard_initial.png)
*Initial dashboard showing an overview of the dataset used to compute the scientific impact of an institution*

![INB Dashboard](/screenshots/dashboard_inb.png)
*Dashboard outlining an overview of the scientific impact of the institution understudy*

![AV Dashboard](/screenshots/dashboard_av.png)
*Dashboard reporting the results of applying the scientific impact methodology to a researcher of the institution under 
study* 

### Live Demo

A live demo of the application is available [here](http://socialanalytics.bsc.es/impactapp/)

## Installation

1. Run `git clone https://github.com/social-link-analytics-group-bsc/impact-app.git`

2. Get into the directory impact-app

3. Create a virtual environment `virtualenv env` ([instructions](https://www.linode.com/docs/development/python/create-a-python-virtualenv-on-ubuntu-1610/) on how to install virtualenv on Ubuntu)

4. Activate the virtual environment `source env/bin/activate`

5. Get into the directory backend

6. Execute `pip install -r requirements.txt` to install dependencies. If an error occurs during the installation, it 
might be because some of these reasons: a) package python-dev is missing; b) package libmysqlclient-dev is missing c) 
the environment variables LC_ALL and/or LC_CTYPE are not defined or do not have a valid value

7. Create a PostgreSQL database. Make sure your database collation is set to UTF-8

8. Rename the file backend/backend/settings.py.example as backend/backend/settings.py

9. Set the configuration parameters of the database in backend/backend/settings.py
```
DATABASES = {
    ...
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    ...
}
```

10. Run `python manage.py migrate` to set up the database schema

11. Run `python manage.py createsuperuser` to create an admin user

12. Run the Django server `python manage.py runserver locahost:8000`

13. Get into the backend directory and run `celery worker -A backend --loglevel=info`. Celery is used to execute 
long-running tasks in background

## Technologies

1. [Python 3.4](https://www.python.org/downloads/)
2. [PostgreSQL](https://www.postgresql.org/)
3. [Django 2.2](https://www.djangoproject.com)
4. [Biopython](https://biopython.org/)
5. [Celery](http://www.celeryproject.org/)

## Issues

Please use [Github's issue tracker](https://github.com/ParticipaPY/politic-bots/issues/new) to report issues and 
suggestions.

## Contributors

[Jorge Saldivar](https://github.com/joausaga), María José Rementería, Nataly Buslón, and Salvador Capella