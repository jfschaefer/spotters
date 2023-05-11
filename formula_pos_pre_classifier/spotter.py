import datetime

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

TAG_SET: TagSet = TagSet(
    uri=SB.NS['formula-pos'],
    label='Formula part-of-speech tag set',
)

TAGS: dict[str, Tag] = {
    s: Tag(
        uri=TAG_SET.uri + '#' + s,
        label=s,
        belongs_to=TAG_SET.uri,
    )
    for s in ['CL', 'NN', 'NNS', 'NNP', 'NNPS']
}


class FormulaPosPreSpotter(UriGeneratorMixin, Spotter):
    spotter_short_id = 'formulapospre'

    @classmethod
    def setup_run(cls, **kwargs) -> tuple[SpotterContext, TripleI]:
        ctx = SpotterContext()

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
        node: _Element
        tree = document.get_html_tree(cached=True)
        selector_converter = document.get_selector_converter()
        uri_generator = self.get_uri_generator_for(document)

        # TODO: Make the recursion code more understandable (and more efficient)
        formula_children: set[_Element] = set()
        for node in tree.iter(tag=Element):
            if node.getparent() in formula_children:
                formula_children.add(node)
                continue

            if node.tag != 'math':
                c = node.get('class')
                if not c:
                    continue
                if 'ltx_equation' not in c:
                    continue

            formula_children.add(node)

            # if we get here, it's a formula

            uri = next(uri_generator)
            target = FragmentTarget(uri('target'), document.get_uri(),
                                    selector_converter.dom_to_selectors(DomRange.from_node(node)))
            yield from target.to_triples()
            yield from Annotation(
                uri=uri('anno'),
                target_uri=target.uri,
                body=SimpleTagBody(TAGS['NNP'].uri),
                creator_uri=self.ctx.run_uri,
            ).to_triples()


if __name__ == '__main__':
    from spotterbase.spotters import spotter_runner

    spotter_runner.auto_run_spotter(FormulaPosPreSpotter)
