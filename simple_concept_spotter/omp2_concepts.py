from __future__ import annotations

import functools
import logging

from typing import Optional

import dataclasses

from spotterbase.rdf import Literal, Uri
from spotterbase.rdf.vocab import RDFS
from spotterbase.sparql.sb_sparql import get_data_endpoint
from spotterbase.utils import config_loader

from nltk.stem import SnowballStemmer


logger = logging.getLogger(__name__)


# we need something weaker (e.g. resulting and result are different)
# STEMMER = SnowballStemmer("english", ignore_stopwords=True)

class STEMMER:
    """ A really hacky stemmer """

    @classmethod
    def stem(cls, word: str) -> str:
        if word.endswith('ies'):
            return cls.stem(word[:-3] + 'y')
        elif word.endswith('s'):
            return cls.stem(word[:-1])
        else:
            return word


@dataclasses.dataclass
class LookupTree:
    uri: Optional[Uri] = None
    children: dict[str, LookupTree] = dataclasses.field(default_factory=dict)

    def __getitem__(self, item) -> LookupTree:
        return self.children[item]

    def __setitem__(self, key, value):
        assert isinstance(key, str)
        assert isinstance(value, LookupTree)
        self.children[key] = value

    def __contains__(self, item) -> bool:
        return item in self.children


@functools.cache
def get_lookup_tree() -> LookupTree:
    things = list(get_data_endpoint().query(f'''
SELECT DISTINCT ?label ?uri WHERE {{
    GRAPH <http://localhost:8890/ontomathprov2> {{
        ?uri {RDFS.label:<>} ?label .
        FILTER langMatches(lang(?label), "en") .
    }}
}}
    '''))
    logger.info(f'Found {len(things)} entries')
    result = LookupTree()
    for entry in things:
        label = entry['label']
        assert isinstance(label, Literal)
        if label.string in {
            'Proof', 'Problem', 'Theorem', 'Algorithm', 'Condition', 'Formula', 'Derivation', 'Experiment', 'Section',
            'Equation', 'Method'
        } or label.string[0].islower():
            continue
        if ' ' not in label.string.strip():
            continue   # single words are too messy
            # print(label.string)
        uri = entry['uri']
        assert isinstance(uri, Uri)
        words = label.string.split()
        lt = result
        for word in words:
            word = STEMMER.stem(word).lower()
            if word not in lt:
                lt[word] = LookupTree()
            lt = lt[word]
        if lt.uri is not None:
            # there is nothing we can do - some concepts seem to be duplicates (e.g. Mobius transformation).
            logger.warning(f'{lt.uri} and {uri} have coinciding labels: {label}')
        lt.uri = uri

    return result


if __name__ == '__main__':
    config_loader.auto()
    get_lookup_tree()
