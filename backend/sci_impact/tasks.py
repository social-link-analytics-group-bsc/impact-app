from celery.utils.log import get_task_logger
from celery import shared_task
from collections import defaultdict
from data_collector.pubmed import EntrezClient
from datetime import date
from django.contrib.auth.models import User
from sci_impact.article import ArticleMgm
from sci_impact.models import ArtifactCitation, Affiliation, Article, Authorship, Scientist

import csv
import pathlib

logger = get_task_logger(__name__)


@shared_task
def get_citations(context):
    logger.info(f"Starting the process of getting citations...")
    ec = EntrezClient()
    am = ArticleMgm()
    citation_objs = []
    num_citations = 0
    article_ids = context['article_ids']
    user = User.objects.get(id=context['user_id'])
    for article_id in article_ids:
        article_obj = Article.objects.get(id=article_id)
        saved_citation_author, saved_citation_authorship = False, False
        authorships = article_obj.authorship_set.all()
        logger.info(f"Getting the citations of the paper {article_obj.title}")
        repo_id = article_obj.repo_id.value
        paper_citations = ec.get_paper_citations(repo_id)
        if paper_citations:
            logger.info(f"Found {len(paper_citations)} citations for the paper")
            for i, paper_citation in enumerate(paper_citations):
                article_citation_obj, created_objs = am.process_paper(i, paper_citation, user)
                if article_citation_obj:
                    try:
                        ArtifactCitation.objects.get(from_artifact=article_citation_obj,
                                                     to_artifact=article_obj)
                        logger.info('Citation already exists!')
                    except ArtifactCitation.DoesNotExist:
                        # 1) Create citation
                        citation_obj = ArtifactCitation(from_artifact=article_citation_obj,
                                                        to_artifact=article_obj,
                                                        created_by=user)
                        citation_obj.save()
                        citation_objs.append(citation_obj)
                        logger.info('Citation created!')
                        num_citations += 1
                        # 2) Update scientist citation metrics
                        for authorship in authorships:
                            author = authorship.author
                            author.article_citations += 1
                            author.total_citations += 1
                            if not saved_citation_author:
                                author.articles_with_citations += 1
                                saved_citation_author = True
                            author.save()
                            # 3) Update affiliation citation metrics
                            affiliations = Affiliation.objects.filter(scientist=author,
                                                                      institution=authorship.institution)
                            for affiliation in affiliations:
                                affiliation.article_citations += 1
                                affiliation.total_citations += 1
                                if not saved_citation_authorship:
                                    affiliation.articles_with_citations += 1
                                    saved_citation_authorship = True
                                affiliation.save()
        else:
            logger.info(f"Could not find citations for the paper")
    logger.info(f"The process has finished! It was created {num_citations} citations")


@shared_task
def get_references(context):
    logger.info(f"Starting the process of getting references...")
    ec = EntrezClient()
    am = ArticleMgm()
    references_objs = []
    num_references = 0
    article_ids = context['article_ids']
    user = User.objects.get(id=context['user_id'])
    for article_id in article_ids:
        article_obj = Article.objects.get(id=article_id)
        logger.info(f"Getting the references of the paper {article_obj.title} ({article_obj.year})")
        repo_id = article_obj.repo_id.value
        paper_references = ec.get_paper_references(repo_id)
        if not paper_references:
            logger.info(f"Found 0 references for the paper")
            continue
        logger.info(f"Found {len(paper_references)} references for the paper")
        for i, paper_reference in enumerate(paper_references):
            article_reference_obj, created_objs = am.process_paper(i, paper_reference, user)
            if article_reference_obj:
                try:
                    ArtifactCitation.objects.get(from_artifact=article_obj,
                                                 to_artifact=article_reference_obj)
                    logger.info('Reference already exists!')
                except ArtifactCitation.DoesNotExist:
                    # 1) Create reference
                    ref_obj = ArtifactCitation(from_artifact=article_obj,
                                               to_artifact=article_reference_obj,
                                               created_by=user)
                    ref_obj.save()
                    references_objs.append(ref_obj)
                    logger.info('Reference created!')
                    num_references += 1
                    authorships = article_reference_obj.authorship_set.all()
                    saved_reference_authors = []
                    for authorship in authorships:
                        # 2) Update scientist citation metrics
                        author = authorship.author
                        if author.id not in saved_reference_authors:
                            saved_reference_authors.append(author.id)
                            author.article_citations += 1
                            author.total_citations += 1
                            author.articles_with_citations += 1
                            author.save()
                        # 3) Update affiliation citation metrics
                        try:
                            affiliation = Affiliation.objects.get(scientist=author,
                                                                  institution=authorship.institution)
                            affiliation.article_citations += 1
                            affiliation.total_citations += 1
                            affiliation.articles_with_citations += 1
                            affiliation.save()
                        except Affiliation.DoesNotExist:
                            # Ignore affiliations that don't exist
                            pass
        else:
            logger.info(f"Could not find references for the paper")
    logger.info(f"The process has finished! It was created {num_references} references")


@shared_task
def mark_articles_of_inb_pis(article_ids):
    for article_id in article_ids:
        article_obj = Article.objects.get(id=article_id)
        authorships = article_obj.authorship_set.all()
        for authorship in authorships:
            author_obj = authorship.author
            if author_obj.is_pi_inb:
                logger.info(f"The article {article_obj} has the INB PI {author_obj} as one of the co-authors")
                article_obj.inb_pi_as_author = True
                article_obj.save()
                break


@shared_task
def fill_affiliation_join_date(affiliation_ids):
    num_affiliations, deleted_affiliations = 0, 0
    for affiliation_id in affiliation_ids:
        affiliation = Affiliation.objects.get(id=affiliation_id)
        logger.info(f"Processing affiliation: {affiliation}")
        num_affiliations += 1
        aff_authorships = Authorship.objects.filter(author=affiliation.scientist,
                                                    institution=affiliation.institution)
        min_year = 1000000
        max_year = -1
        if len(aff_authorships) > 0:
            for aff_authorship in aff_authorships:
                if aff_authorship.artifact.year < min_year:
                    min_year = aff_authorship.artifact.year
                if aff_authorship.artifact.year > max_year:
                    max_year = aff_authorship.artifact.year
            affiliation.joined_date = date(year=min_year, month=1, day=1)
            affiliation.departure_date = date(year=max_year, month=1, day=1)
            affiliation.save()
        else:
            deleted_affiliations += 1
            affiliation.delete()
    logger.info(f"It was completed {num_affiliations} affiliations")
    logger.info(f"{deleted_affiliations} affiliations were deleted because they don't any authorship associated")


@shared_task
def compute_h_index(scientist_ids):
    for scientist_id in scientist_ids:
        scientist = Scientist.objects.get(id=scientist_id)
        logger.info(f"Computing the h-index of: {scientist}")
        article_ids, author_citations = [], []
        # Get citations of the scientist's articles
        authorships = Authorship.objects.filter(author=scientist_id)
        for authorship in authorships:
            article = authorship.artifact
            if article.id not in article_ids:
                article_ids.append(article.id)
                article_citations = ArtifactCitation.objects.filter(to_artifact=article).count()
                author_citations.append(article_citations)
        h_index = scientist.articles_with_citations
        if h_index > 0:
            while True:
                greater_counter = 0
                for citation in author_citations:
                    if citation >= h_index:
                        greater_counter += 1
                if greater_counter >= h_index:
                    break
                else:
                    h_index -= 1
        logger.info(f"H-index of {scientist}: {h_index}")
        scientist.h_index = h_index
        scientist.save()


@shared_task
def update_productivy_metrics(scientist_ids):
    for scientist_id in scientist_ids:
        scientist_obj = Scientist.objects.get(id=scientist_id)
        scientist_production = {'articles': 0, 'articles_as_first_author': 0, 'articles_as_last_author': 0,
                                'articles_with_citations': 0, 'article_citations': 0}
        articles = []
        logger.info(f"Updating the metrics of {scientist_obj}")
        scientist_authorships = Authorship.objects.filter(author_id=scientist_obj.id)
        for scientist_authorship in scientist_authorships:
            if scientist_authorship.artifact_id not in articles:
                articles.append(scientist_authorship.artifact_id)
                scientist_production['articles'] += 1
                if scientist_authorship.first_author:
                    scientist_production['articles_as_first_author'] += 1
                if scientist_authorship.last_author:
                    scientist_production['articles_as_last_author'] += 1
                article_citations = ArtifactCitation.objects.filter(to_artifact=scientist_authorship.artifact_id). \
                    count()
                scientist_production['article_citations'] += article_citations
                if article_citations > 0:
                    scientist_production['articles_with_citations'] += 1
        scientist_obj.articles = scientist_production['articles']
        scientist_obj.articles_as_first_author = scientist_production['articles_as_first_author']
        scientist_obj.articles_as_last_author = scientist_production['articles_as_last_author']
        scientist_obj.article_citations = scientist_production['article_citations']
        scientist_obj.articles_with_citations = scientist_production['articles_with_citations']
        scientist_obj.save()
    logger.info('Task finished!')


@shared_task
def identify_self_citation(article_ids):
    for article_id in article_ids:
        article = Article.objects.get(id=article_id)
        logger.info(f"Analyzing citations of the article: {article}")
        citations = ArtifactCitation.objects.filter(from_artifact=article)
        # get authors of the article
        authorships = Authorship.objects.filter(artifact=article).distinct('author').values_list('author')
        authors = set([to_authorship[0] for to_authorship in authorships])
        num_self_citations = 0
        for citation in citations:
            target_article = citation.to_artifact
            # get authors of article
            target_authorships = Authorship.objects.filter(artifact=target_article).distinct('author').values_list('author')
            target_authors = set([target_authorship[0] for target_authorship in target_authorships])
            # check if the are authors in common between the source and target articles
            common_authors = authors.intersection(target_authors)
            if len(common_authors) > 0:
                citation.self_citation = True
                citation.save()
                num_self_citations += 1
        logger.info(f"The article has {num_self_citations} self-citations")
    logger.info('The process has finished...')


@shared_task
def fix_incorrect_citation(citation_ids):
    for citation_id in citation_ids:
        citation_obj = ArtifactCitation.objects.get(id=citation_id)
        fixed_citations = 0
        if citation_obj.from_artifact.year < citation_obj.to_artifact.year:
            logger.info(f"Fixing citation: {citation_obj.id}. From year: {citation_obj.from_artifact.year} "
                        f"To year: {citation_obj.to_artifact.year}")
            fixed_citations += 1
            aux_citation = citation_obj.from_artifact
            citation_obj.from_artifact = citation_obj.to_artifact
            citation_obj.to_artifact = aux_citation
            try:
                citation_obj.save()
            except:
                logger.info(f"The swapped citation already exists!. It will be deleted")
                citation_obj.delete()
            fixed_citations += 1
    logger.info(f"The process has finished, {fixed_citations} citations were fixed")


@shared_task()
def import_scopus_data(context):
    objs_created = defaultdict(list)
    am = ArticleMgm()
    scopus_data_dir = pathlib.Path('sci_impact', 'data', 'scopus')
    user = User.objects.get(username=context['username'])
    for scientist_id in context['scientist_ids']:
        scientist_obj = Scientist.objects.get(id=scientist_id)
        scientist_name = scientist_obj.first_name[0].lower() + scientist_obj.last_name.lower()
        file_name = scientist_name + '.csv'
        logger.info(f"Processing: {file_name}")
        scopus_file_name = scopus_data_dir.joinpath(file_name)
        try:
            with open(str(scopus_file_name), 'r', encoding='utf-8-sig') as f:
                file = csv.DictReader(f, delimiter=',')
                paper_index = 0
                for paper_line in file:
                    article_obj, created_objs = am.process_scopus_paper(paper_index, paper_line, scientist_obj, user)
                    if created_objs:
                        for type_obj, objs in created_objs.items():
                            if isinstance(objs, list):
                                objs_created[type_obj].extend(article_obj)
                            else:
                                objs_created[type_obj].append(article_obj)
            if objs_created:
                msg = 'The action was completed successfully!\n'
                for model, objs in objs_created.items():
                    msg += f"- It was created {len(objs)} objects of the type {model}\n"
                logger.info(msg)
            else:
                logger.warning('No objects were created')
        except Exception as e:
            logger.error(e)


@shared_task()
def update_citations(article_ids):
    for article_id in article_ids:
        article = Article.objects.get(id=article_id)
        if article.cited_by == 0:
            logger.info(f"Updating the citations of paper {article.title}")
            citations = ArtifactCitation.objects.filter(to_artifact=article)
            num_citations = len(citations)
            article.cited_by = num_citations
            article.save()
    logger.info('Task has finished!')