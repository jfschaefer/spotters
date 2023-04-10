import csv
import functools
import logging

from simple_concept_spotter.omp2_concepts import LookupTree, STEMMER
from spotterbase.data.locator import DataDir
from spotterbase.dnm_nlp.word_tokenizer import word_tokenize
from spotterbase.rdf import Uri
from spotterbase.sparql.endpoint import WIKIDATA
from spotterbase.utils import config_loader

logger = logging.getLogger(__name__)


@functools.cache
def get_lookup_tree() -> LookupTree:
    file_name = DataDir.get('wikidata_concepts_cache.csv')
    if not file_name.is_file():
        logger.info(f'Querying WikiData for concepts and caching them in {file_name}')
        results = WIKIDATA.send_query('''
SELECT DISTINCT ?item ?itemLabel WHERE {
  { ?item wdt:P2579/wdt:P31 wd:Q20026918 . } UNION { ?item wdt:P2579/wdt:P31 wd:Q1936384 . } UNION {  ?item wdt:P279/wdt:P2579/wdt:P31 wd:Q1936384 . } .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
''', accept='text/csv')
        with open(file_name, 'w') as fp:
            fp.write(results)
    else:
        logger.info(f'Loading concepts from {file_name}')

    result = LookupTree()

    with open(file_name, newline='') as fp:
        for row in csv.reader(fp, delimiter=','):
            uri = Uri(row[0])
            if row[1][-1].isdigit() or len(row[1]) < 3:
                continue
            words = word_tokenize(row[1])

            lt = result
            for word in words:
                word = STEMMER.stem(word).lower()
                if word not in lt:
                    lt[word] = LookupTree()
                lt = lt[word]
            if lt.uri is not None:
                # there is nothing we can do - some concepts seem to be duplicates (e.g. Mobius transformation).
                # logger.warning(f'{lt.uri} and {uri} have coinciding labels: {row[1]}')
                pass
            lt.uri = uri

    return result


if __name__ == '__main__':
    config_loader.auto()
    get_lookup_tree()
