from celery.utils.log import get_task_logger
from celery import shared_task
from collections import defaultdict
from nltk import word_tokenize, pos_tag, corpus
from nltk.tokenize import sent_tokenize
from social_impact.models import SocialImpactSearch, SocialImpactSearchPublication, ImpactMention
from social_impact.utils import normalize, remove_url_from_text, lemmatize_words, remove_non_ascii, remove_extra_spaces

import csv
import nltk
import pdftotext
import spacy
import re


logger = get_task_logger(__name__)


def __build_impact_dictionary(path_dictionary):
    impact_words, i_verbs, i_nouns = [], [], []
    with open(str(path_dictionary), 'r') as f:
        file = csv.DictReader(f, delimiter=',')
        for line in file:
            if line['pos'] == 'verb':
                lemma_words = ' '.join(lemmatize_words(normalize(line['word']), pos=corpus.wordnet.VERB))
                i_verbs.append(lemma_words)
            if line['pos'] == 'noun':
                lemma_words = ' '.join(lemmatize_words(normalize(line['word']), pos=corpus.wordnet.NOUN))
                i_nouns.append(lemma_words)
    impact_words = [i_verb + ' ' + i_noun for i_verb in i_verbs for i_noun in i_nouns if i_verb != i_noun]
    return impact_words


def get_not_processed_publications(search):
    not_processed_search_publications = []
    search_publications = SocialImpactSearchPublication.objects.filter(social_impact_header=search)
    for search_publication in search_publications:
        if not search_publication.completed:
            not_processed_search_publications.append(search_publication.publication)
        else:
            logger.info(f"")
    return not_processed_search_publications


@shared_task()
def search_social_impact_mentions(payload):
    # download stopwords and corpus
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')
    # load spacy english model
    s_nlp = spacy.load('en')
    # define data directory
    docs_with_occurrences = 0
    for search_id in payload['search_ids']:
        search = SocialImpactSearch.objects.get(id=search_id)
        # load impact words
        logger.info('Building impact dictionary...')
        impact_words = __build_impact_dictionary(search.dictionary)
        search_publications = get_not_processed_publications(search)
        total_publications = len(search_publications)
        processed_data = dict()
        for i, search_publication in enumerate(search_publications):
            logger.info(f'({i + 1}/{total_publications}) Looking for mention of impact in the '
                        f'publication: {search_publication}')
            processed_data[str(search_publication.id)] = {'publication': search_publication, 'impact_occurrences': []}
            with open(search_publication.file, 'rb') as f:
                pdf = pdftotext.PDF(f)
            # loop over pdf pages
            pdf_pages = len(pdf)
            for page_num in range(0, pdf_pages):
                page_text = remove_url_from_text(pdf[page_num])
                # iterate over sentences and clean them
                sentences = sent_tokenize(page_text)
                clean_sentences = []
                for sentence in sentences:
                    normalized_sentence = normalize(sentence)
                    # process sentence dependency
                    sentence_to_nlp = remove_non_ascii(sentence)
                    sentence_to_nlp = remove_extra_spaces(sentence_to_nlp)
                    nlp_sentence = s_nlp(' '.join(sentence_to_nlp))
                    sentence_dependencies = defaultdict(list)
                    for nlp_token in nlp_sentence:
                        token_text, token_tag, token_dependency_type, token_dependent_text, token_dependent_tag = \
                            nlp_token.text, nlp_token.tag_, nlp_token.dep_, nlp_token.head.text, nlp_token.head.tag_
                        if token_tag[0] == 'N' and token_dependency_type == 'dobj' and token_dependent_tag[0] == 'V':
                            lemma_dependent = ' '.join(lemmatize_words(token_dependent_text))
                            lemma_token = ' '.join(lemmatize_words(token_text, pos=corpus.wordnet.NOUN))
                            sentence_dependencies[lemma_dependent].append(lemma_token)
                    tagged_tokens = pos_tag(normalized_sentence)
                    lemma_tokens = []
                    for tagged_token in tagged_tokens:
                        token, tag = tagged_token
                        if tag[0] == 'N':
                            lemma_token = lemmatize_words(token, pos=corpus.wordnet.NOUN)
                            lemma_tokens.append(' '.join(lemma_token))
                        if tag[0] == 'V':
                            lemma_token = lemmatize_words(token, pos=corpus.wordnet.VERB)
                            lemma_tokens.append(' '.join(lemma_token))
                    lemma_sentence = ' '.join(lemma_tokens)
                    occurrences = set()
                    for impact_word in impact_words:
                        impact_tokens = word_tokenize(impact_word)
                        reg_verb, reg_noun = impact_tokens[0], ' '.join(impact_tokens[1:])
                        reg_exp = r'^[\w\s]+{verb}\s[\w\s]*{noun}[\w\s]*$'.format(verb=reg_verb, noun=reg_noun)
                        if re.search(reg_exp, lemma_sentence):
                            if sentence_dependencies.get(reg_verb):
                                if reg_noun in sentence_dependencies[reg_verb]:
                                    occurrences.add(impact_word)
                    if len(occurrences) > 0:
                        found_sentence = ' '.join(sentence_to_nlp)
                        found_impact_word = ', '.join(occurrences)
                        logger.info(f'Impact found =======\n'
                                    f'Sentence: {found_sentence}\n'
                                    f'Impact word: {found_impact_word}\n')
                        processed_data[str(search_publication.id)]['impact_occurrences'].append(
                            {
                                'page': page_num + 1,
                                'sentence': found_sentence,
                                'found_tokens': found_impact_word
                            }
                        )
            if len(processed_data[search_publication]['impact_occurrences']) > 0:
                docs_with_occurrences += 1
            search_publication.completed = True
            search_publication.save()
        logger.info(f'Found occurrences in {docs_with_occurrences} of the {total_publications} pdfs')
        search.completed = True
        search.save()
        logger.info('Recording results...')
        for publication_id, metadata in processed_data.items():
            for occurrence in metadata['impact_occurrences']:
                mention_dict = {
                    'publication': metadata['publication'],
                    'page': occurrence['page'],
                    'sentence': occurrence['sentence'],
                    'impact_mention': occurrence['found_tokens'],
                    'created_by': payload.current_user
                }
                impact_mention_obj = ImpactMention(**mention_dict)
                impact_mention_obj.save()
    logger.info(f'Processed finished successfully!')