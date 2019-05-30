from celery import shared_task
from celery.utils.log import get_task_logger
from data_collector.pubmed import EntrezClient
from sci_impact.article import ArticleMgm
from sci_impact.models import ArtifactCitation, Affiliation, Article

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
    logger.info(f"It was create {num_citations} citations")