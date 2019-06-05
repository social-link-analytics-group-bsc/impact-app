from celery.utils.log import get_task_logger
from celery import shared_task
from data_collector.pubmed import EntrezClient
from datetime import date
from sci_impact.article import ArticleMgm
from sci_impact.models import ArtifactCitation, Affiliation, Article, Authorship


logger = get_task_logger(__name__)


@shared_task
def get_citations(article_ids):
    logger.info(f"Starting the process of getting citations...")
    ec = EntrezClient()
    am = ArticleMgm()
    citation_objs = []
    num_citations = 0
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
                article_citation_obj, created_objs = am.process_paper(i, paper_citation)
                if article_citation_obj:
                    try:
                        ArtifactCitation.objects.get(from_artifact=article_citation_obj,
                                                     to_artifact=article_obj)
                        logger.info('Citation already exists!')
                    except ArtifactCitation.DoesNotExist:
                        # 1) Create citation
                        citation_obj = ArtifactCitation(from_artifact=article_citation_obj,
                                                        to_artifact=article_obj)
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
def get_references(article_ids):
    logger.info(f"Starting the process of getting references...")
    ec = EntrezClient()
    am = ArticleMgm()
    references_objs = []
    num_references = 0
    for article_id in article_ids:
        article_obj = Article.objects.get(id=article_id)
        logger.info(f"Getting the references of the paper {article_obj.title}")
        repo_id = article_obj.repo_id.value
        paper_references = ec.get_paper_citations(repo_id)
        logger.info(f"Found {len(paper_references)} references for the paper")
        for i, paper_reference in enumerate(paper_references):
            article_reference_obj, created_objs = am.process_paper(i, paper_reference)
            if article_reference_obj:
                try:
                    ArtifactCitation.objects.get(from_artifact=article_obj,
                                                 to_artifact=article_reference_obj)
                    logger.info('Citation already exists!')
                except ArtifactCitation.DoesNotExist:
                    # 1) Create citation
                    ref_obj = ArtifactCitation(from_artifact=article_obj,
                                               to_artifact=article_reference_obj)
                    ref_obj.save()
                    references_objs.append(ref_obj)
                    logger.info('Citation created!')
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
                        affiliation = Affiliation.objects.get(scientist=author,
                                                              institution=authorship.institution)
                        affiliation.article_citations += 1
                        affiliation.total_citations += 1
                        affiliation.articles_with_citations += 1
                        affiliation.save()
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
