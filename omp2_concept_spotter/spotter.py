from datetime import datetime

from omp2_concept_spotter.omp2_concepts import STEMMER, get_lookup_tree
from spotterbase.corpora.interface import Document
from spotterbase.dnm.simple_dnm_factory import ARXMLIV_STANDARD_DNM_FACTORY
from spotterbase.dnm_nlp.sentence_tokenizer import sentence_tokenize
from spotterbase.dnm_nlp.word_tokenizer import word_tokenize
from spotterbase.model_core.annotation import Annotation
from spotterbase.model_core.annotation_creator import SpotterRun
from spotterbase.model_core.tag_body import SimpleTagBody
from spotterbase.model_core.target import FragmentTarget
from spotterbase.model_extra.sbx import SBX
from spotterbase.rdf import TripleI
from spotterbase.selectors.dom_range import DomRange
from spotterbase.spotters.spotter import UriGeneratorMixin, Spotter, SpotterContext
from spotterbase.utils import config_loader


class OmpConceptSpotter(UriGeneratorMixin, Spotter):
    spotter_short_id = 'ompconcept'

    @classmethod
    def setup_run(cls, **kwargs) -> tuple[SpotterContext, TripleI]:
        ctx = SpotterContext()

        return ctx, SpotterRun(
            uri=ctx.run_uri,
            spotter_uri=SBX.NS['ompconceptspotter'],
            spotter_version='0.0.1',
            date=datetime.now(),
        ).to_triples()

    def process_document(self, document: Document) -> TripleI:
        uri_generator = self.get_uri_generator_for(document)

        lookup_tree = get_lookup_tree()

        # tree = etree.parse(document.open(), parser=etree.HTMLParser())  # type: ignore
        dnm = ARXMLIV_STANDARD_DNM_FACTORY.dnm_from_document(document)
        selector_converter = document.get_selector_converter()

        for sentence in sentence_tokenize(dnm):
            words: list[dnm] = word_tokenize(sentence)
            for i, word in enumerate(words):
                word = STEMMER.stem(word.string).lower()
                if word not in lookup_tree:
                    continue
                lt = lookup_tree[word]
                j = i+1
                while j < len(words):
                    word = STEMMER.stem(words[j].string).lower()
                    if word in lt:
                        lt = lt[word]
                        j += 1
                    else:
                        break
                if lt.uri is None:
                    continue

                # TODO: special treatment for set (check its part-of-speech)
                print(f'Found {words[i:j]}')

                uri = next(uri_generator)
                target = FragmentTarget(uri('target'), document.get_uri(),
                                        selector_converter.dom_to_selectors(
                                            DomRange(words[i].as_range().to_dom(), words[j-1].as_range().to_dom()))
                                        )
                yield from target.to_triples()
                yield from Annotation(
                    uri=uri('anno'),
                    target_uri=target.uri,
                    body=SimpleTagBody(lt.uri),
                    creator_uri=self.ctx.run_uri,
                ).to_triples()


if __name__ == '__main__':
    from spotterbase.spotters import spotter_runner
    config_loader.auto()
    spotter_runner.auto_run_spotter(OmpConceptSpotter)
