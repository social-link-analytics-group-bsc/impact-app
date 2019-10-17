# Impact App

Impact App is a work-in-progress tool developed by the [Social and Media Impact Evaluation group](https://www.bsc.es/discover-bsc/organisation/scientific-structure/social-and-media-impact-evaluation) 
of the [Barcelona Supercomputing Center](https://www.bsc.es) with the goal of assist organizations and scholars to
measure the scientific and social impact of their research projects. 

## Scientific Impact

By **scientific impact** we understand the intellectual contribution to a person’s field of study within academia [[1](https://watermark.silverchair.com/rvt021.pdf?token=AQECAHi208BE49Ooan9kkhW_Ercy7Dm3ZL_9Cf3qfKAc485ysgAAAmkwggJlBgkqhkiG9w0BBwagggJWMIICUgIBADCCAksGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMRj2dd7F4L_cwKEUSAgEQgIICHNp6KnbAQrD7D0xXXvl6LkGQRmKhXYFdTks1uib8Y7xIAb5ast0nr_XaXF0FSm9vyO7KDVmL2-7LdsIdfMiBzu32uuWh1LdgF7YSlg0-nfyNWT5LAPC0sGNAFq4Pg9Zq2VJUwEGO8P1qqYS2rTyXiy_5TbWKwssQ2tDQLU4U3PY4a-n_2N4pvRse2hErI1R2ozB2DpuauH8uPU3TsJog_vK_DJ59-vMM4hcl-QbDpj4iuEmaBXBOdA428WAWZ_A3kvXYL4C2E8z4ugB0--NYD6GU9Qq_5igyA4NvovxL10-P19K4EUE2-ilUF5qOoFWC_ZbyD_ILlsdVGhQ8yiy0y6cEeuyvX8gG5kwyIrFQkfpz1MNUtsuQ8vR9DuJ3CbPHHitxznIEjy1WJBSHzUnG8niknBWJ8PF0tnMw4w1nIvpUn1Ebk8Gd_e2rdblSTxhrxTkmbK3uuHmveR2fzoI4nsCL_OOU9RCPTULkqFLZH8x1JnGC4CcNINQZuCAQOedVb4Rdhe_agXcOdYDwuK6dAc1BUaDPGWZEk-Vt3WMGppQGR52hPL3c6VR-KMS8zFQaOBZwcyzIoLBAg1vvbRfMNbJdUpSpC-5JiWqgU0ElnnHU2-B219-Vvw1jH2CEZwKWHfdqSPN_4LniU6fzyDWI8JEwVBZUFrxZ9bJqemL2iu6s2G5jhCOi2mE1uZ3hzyFEGRDO0Ys2RXIRUWh8dQ)].
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

To understand whether a certain number of citations or a specific value of citations per publications is low or high, we 
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
year of the evaluation period;
2. Compute the indicators for each year in the selected range;
3. Evaluate how the institution performs within their field of activity.

### Example




**Social Impact.** ...

![ImpactApp Front Page](/screenshots/front_page.png)
 
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

## Technologies

1. [Python 3.4](https://www.python.org/downloads/)
2. [PostgreSQL](https://www.postgresql.org/)
3. [Django 2.2](https://www.djangoproject.com)
4. [Biopython](https://biopython.org/)

## Issues

Please use [Github's issue tracker](https://github.com/ParticipaPY/politic-bots/issues/new) to report issues and 
suggestions.

## References

[^1]: Penfield, T., Baker, M. J., Scoble, R., & Wykes, M. C. (2014). Assessment, evaluations, and definitions of research 
impact: A review. Research Evaluation, 23(1), 21-32.
[^2]: Van Raan, A. F. (2004). Measuring science. In Handbook of quantitative science and technology research (pp. 19-50). 
Springer, Dordrecht.
[^3]: Donovan, C. (2007). Introduction: Future pathways for science policy and research assessment: metrics vs peer 
review, quality vs impact.
[^4]: Ministerio de Industria, Economía, y Competitiva. (2017). Cálculo del impacto normalizado de la producción científica.