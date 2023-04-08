import datetime
import itertools
import re

from lxml.etree import Element, _Element

from spotterbase.corpora.interface import Document
from spotterbase.model_core.annotation import Annotation
from spotterbase.model_core.annotation_creator import SpotterRun
from spotterbase.model_core.sb import SB
from spotterbase.model_core.tag_body import SimpleTagBody, Tag, TagSet
from spotterbase.model_core.target import FragmentTarget
from spotterbase.rdf import TripleI
from spotterbase.selectors.dom_range import DomRange
from spotterbase.spotters.spotter import Spotter, SpotterContext, UriGeneratorMixin
# import load_env_normalization
from . import load_env_normalization


class ParaSpotterCtx(SpotterContext):
    def __init__(self):
        super().__init__()

        self.processed_counter: int = 0
        self.skipped_counter: int = 0

        self.tag_lookup: dict[str, str] = load_env_normalization.load()


TAG_SET: TagSet = TagSet(
    uri=SB.NS['para-class'],
    label='Paragraph classification tag set',
    comment='The set of paragraph classifications used in https://arxiv.org/abs/1908.10993'
)

TAGS: dict[str, Tag] = {
    s: Tag(
        uri=TAG_SET.uri + '#' + s,
        label=s,
        belongs_to=TAG_SET.uri,
    )
    for s in itertools.chain(load_env_normalization.load().values(), ['Other'])
}

regex = re.compile(r'(ltx_proof)|(ltx_acknowledgement)|(ltx_caption)|(ltx_theorem_\w+)')


class AmsParaSpotter(UriGeneratorMixin, Spotter):
    spotter_short_id = 'amsparas'
    ctx: ParaSpotterCtx

    @classmethod
    def setup_run(cls, **kwargs) -> tuple[SpotterContext, TripleI]:
        ctx = ParaSpotterCtx()

        def triple_gen() -> TripleI:
            yield from SpotterRun(
                uri=ctx.run_uri,
                date=datetime.datetime.now(),
                label='Run of AMS Paragraph Spotter',
            ).to_triples()
            yield from TAG_SET.to_triples()
            for tag in TAGS.values():
                yield from tag.to_triples()

        return ctx, triple_gen()

    def process_document(self, document: Document) -> TripleI:
#         should_be_processed = self.ctx.endpoint.ask_query(f'''
# ASK {{
#     ?anno {OA.hasTarget:<>} {document.get_uri():<>} .
#     ?anno {OA.hasBody:<>} ?body .
#     ?body {RDF.value:<>} {simple_substring_spotter.TAGS["ltx_theorem"].uri:<>} .
# }}
#         ''')
#         if not should_be_processed:
#             return

        node: _Element
        tree = document.get_html_tree(cached=True)
        selector_converter = document.get_selector_converter()
        uri_generator = self.get_uri_generator_for(document)
        for node in tree.iter(tag=Element):
            c = node.get('class')
            if not c:
                continue
            match = regex.search(c)
            if not match:
                continue
            m = match.group()
            tag: str
            if m == 'ltx_proof':
                tag = 'Proof'
            elif m == 'ltx_acknowledgement':
                tag = 'Acknowledgement'
            elif m == 'ltx_caption':
                tag = 'Caption'
            else:
                assert m.startswith('ltx_theorem_'), f'did not expect {m!r}'
                m = m[len('ltx_theorem_'):]
                if m in self.ctx.tag_lookup:
                    tag = self.ctx.tag_lookup[m]
                else:
                    tag = 'Other'

            uri = next(uri_generator)
            target = FragmentTarget(uri('target'), document.get_uri(),
                                    selector_converter.dom_to_selectors(DomRange.from_node(node)))
            yield from target.to_triples()
            yield from Annotation(
                uri=uri('anno'),
                target_uri=target.uri,
                body=SimpleTagBody(TAGS[tag].uri),
                creator_uri=self.ctx.run_uri,
            ).to_triples()


if __name__ == '__main__':
    from spotterbase.spotters import spotter_runner

    spotter_runner.auto_run_spotter(AmsParaSpotter)
