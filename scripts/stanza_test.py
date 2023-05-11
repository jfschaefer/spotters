import spacy_stanza
import stanza
import spacy
from spacy import displacy

from spotterbase.corpora.resolver import Resolver
from spotterbase.dnm.simple_dnm_factory import ARXMLIV_STANDARD_DNM_FACTORY
from spotterbase.dnm_nlp.sentence_tokenizer import sentence_tokenize
from spotterbase.dnm_nlp.word_tokenizer import word_tokenize
from spotterbase.rdf import Uri
from spotterbase.utils import config_loader

config_loader.auto()

document = Resolver.get_document(Uri('http://sigmathling.kwarc.info/arxmliv/2020/0704.0005'))
dnm = ARXMLIV_STANDARD_DNM_FACTORY.dnm_from_document(document)

# JUST SPACY

sentences = sentence_tokenize(dnm)[:5]
nlp = spacy.load("en_core_web_trf")
def with_period(s: str) -> str:
    if s.endswith('.'):
        return s
    return s + '.'
string = '\n'.join(with_period(sentence._string) for sentence in sentences)
doc = nlp(string)
displacy.serve(doc, style="dep")


# JUST STANZA

# tokenized_document: list[list[str]] = []
# for sentence in sentence_tokenize(dnm):
#     tokenized_document.append([])
#     for word in word_tokenize(sentence):
#         tokenized_document[-1].append(word.string)
#
# print(tokenized_document[:3])


# nlp = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma,depparse', tokenize_pretokenized=True)
#
#
# result = nlp(tokenized_document)
# print(*[f'id: {word.id}\tword: {word.text}\thead id: {word.head}\thead: {sent.words[word.head-1].text if word.head > 0 else "root"}\tdeprel: {word.deprel}' for sent in result.sentences[:3] for word in sent.words], sep='\n')


# STANZA SPACY

# tokenized_document: list[list[str]] = []
# for sentence in sentence_tokenize(dnm):
#     tokenized_document.append([])
#     for word in word_tokenize(sentence):
#         tokenized_document[-1].append(word.string)

# nlp = spacy_stanza.load_pipeline('en', processors='tokenize,mwt,pos,lemma,depparse', tokenize_pretokenized=True)
# result = nlp(string)
#
# displacy.serve(result, style="dep")

# print(*[f'id: {word.id}\tword: {word.text}\thead id: {word.head}\thead: {sent.words[word.head-1].text if word.head > 0 else "root"}\tdeprel: {word.deprel}' for sent in result.sentences[:3] for word in sent.words], sep='\n')
