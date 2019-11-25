from nltk.corpus import stopwords
from nltk.stem import LancasterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize
import re
import unicodedata


def remove_non_ascii(words):
    """Remove non-ASCII characters from words"""
    words = get_list(words)
    new_words = []
    for word in words:
        new_word = unicodedata.normalize('NFKD', word).encode('ascii', 'ignore').decode('utf-8', 'ignore')
        new_words.append(new_word)
    return new_words


def to_lowercase(words):
    """Convert all characters of words to lowercase"""
    words = get_list(words)
    new_words = []
    for word in words:
        new_word = word.lower()
        new_words.append(new_word)
    return new_words


def remove_punctuation(words):
    """Remove punctuation from words"""
    words = get_list(words)
    new_words = []
    for word in words:
        new_word = re.sub(r'[^\w\s]', '', word)
        if new_word != '':
            new_words.append(new_word)
    return new_words


def remove_extra_spaces(words):
    words = get_list(words)
    new_words = []
    for word in words:
        word_clean = ' '.join(word.split())
        new_words.append(word_clean)
    return new_words


def remove_stopwords(words):
    """Remove stop words from list of tokenized words"""
    words = get_list(words)
    new_words = []
    for word in words:
        if word not in stopwords.words('english'):
            new_words.append(word)
    return new_words


def stem_words(words):
    """Stem words in list of tokenized words"""
    words = get_list(words)
    stemmer = LancasterStemmer()
    stems = []
    for word in words:
        stem = stemmer.stem(word)
        stems.append(stem)
    return stems


def lemmatize_words(words, pos='v'):
    """Lemmatize verbs in list of tokenized words"""
    words = get_list(words)
    lemmatizer = WordNetLemmatizer()
    lemmas = []
    for word in words:
        lemma = lemmatizer.lemmatize(word, pos=pos)
        lemmas.append(lemma)
    return lemmas


def normalize(words):
    words = get_list(words)
    words = remove_non_ascii(words)
    words = to_lowercase(words)
    words = remove_punctuation(words)
    words = remove_extra_spaces(words)
    words = remove_stopwords(words)
    return words


def get_list(text):
    if not isinstance(text, list):
        return word_tokenize(text)
    else:
        return text


def read_file_as_list(file_name, encoding='utf-8'):
    with open(file_name, 'r', encoding=encoding) as f:
        file_list = f.read().splitlines()
    return file_list


def remove_url_from_text(text):
    return re.sub(r'^https?:\/\/.*[\r\n]*', '', text, flags=re.MULTILINE)