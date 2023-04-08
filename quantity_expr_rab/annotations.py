import re
import urllib.parse
from datetime import datetime
from lxml import etree
from lxml.etree import _Element

from quantity_expr_rab.document_corpus import DocInfo, DATA_LOCATOR, DocumentCorpus
from quantity_expr_rab.vocab import RabQuantBody, RAB
from spotterbase.model_core.annotation import Annotation
from spotterbase.model_core.annotation_creator import SpotterRun
from spotterbase.model_core.target import FragmentTarget
from spotterbase.corpora.interface import Document
from spotterbase.data.zipfilecache import SHARED_ZIP_CACHE
from spotterbase.rdf import TripleI, Uri
from spotterbase.selectors.dom_range import DomRange, DomPoint
from spotterbase.spotters.spotter import UriGeneratorMixin, Spotter, SpotterContext
from spotterbase.utils import config_loader

ns = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'kat': 'https://github.com/KWARC/KAT/'}


def eval_cmml_number(node: _Element) -> float:
    if node.tag == 'cn':
        return float(node.text.replace(' ', '').replace('\u2009', '').replace('\u2004', ''))
    if node.tag == 'apply':
        children = iter(node)
        operator = next(children)
        if operator.tag == 'times' or (operator.tag == 'ci' and operator.text == '⋅'):
            return eval_cmml_number(next(children)) * eval_cmml_number(next(children))
        elif operator.tag == 'csymbol' and operator.text == 'superscript':
            return eval_cmml_number(next(children)) ** eval_cmml_number(next(children))
        elif operator.tag == 'minus':
            return -eval_cmml_number(next(children))

    raise Exception(f'Failed to process {etree.tostring(node)}')


def unit_cmml_to_str(node: _Element) -> str:
    if node.tag == 'csymbol':
        return node.attrib['cd']
    if node.tag == 'apply':
        children = iter(node)
        operator = next(children)
        if operator.tag == 'times':
            return '_'.join(unit_cmml_to_str(n) for n in children)
        elif operator.tag == 'divide':
            return '_per_'.join(unit_cmml_to_str(n) for n in children)
        elif operator.tag == 'power':
            s = unit_cmml_to_str(next(children))
            exp = eval_cmml_number(next(children))
            if exp == 1.0:
                return s
            elif exp == 2.0:
                return s + '_squared'
            elif exp == 3.0:
                return s + '_cubed'
            elif exp == int(exp):
                return s + f'_pow_{int(exp)}'
            else:
                return s + f'_pow_{exp}'
        elif operator.tag == 'csymbol' and operator.attrib['cd'] == 'Prefix':
            return '_'.join(unit_cmml_to_str(n) for n in children)

    raise Exception(f'Failed to process {etree.tostring(node)}')


def process_cmml(node: _Element) -> tuple[float, Uri]:
    # print(etree.tostring(node))
    child: _Element = next(iter(node))
    assert child.tag == 'apply', f'Unexpected CMML: {etree.tostring(child)}'

    children = iter(child)
    assert next(children).tag == 'times'

    scalar = eval_cmml_number(next(children))
    unit = RAB.NS[unit_cmml_to_str(next(children))]
    if unit.starts_with('_'):
        unit = unit[1:]
    # print(scalar, unit)
    return scalar, unit


class RabQuantImporter(UriGeneratorMixin, Spotter):
    spotter_short_id = 'rabquants'

    @classmethod
    def setup_run(cls, **kwargs) -> tuple[SpotterContext, TripleI]:
        ctx = SpotterContext()

        return ctx, SpotterRun(
            uri=ctx.run_uri,
            spotter_uri=DocumentCorpus.uri / 'importspotter',
            spotter_version='0.0.1',
            date=datetime.now(),
        ).to_triples()

    def process_document(self, document: Document) -> TripleI:
        uri_generator = self.get_uri_generator_for(document)
        doc_info = DocInfo.from_uri(document.get_uri())
        with SHARED_ZIP_CACHE[DATA_LOCATOR.require() / 'Annotations.zip'] as zip_file:
            with zip_file.open(doc_info.to_kat_filename()) as fp:
                tree = etree.parse(fp)
                nodes = tree.xpath('/rdf:RDF/rdf:Description[kat:concept]', namespaces=ns)
                if not nodes:
                    return iter(())
                htmltree = document.get_html_tree(cached=True)
                for node in nodes:
                    resources = node.xpath('./kat:annotates/@rdf:resource', namespaces=ns)
                    katcmls = node.xpath('./kat:contentmathml', namespaces=ns)
                    assert katcmls
                    cml = max(katcmls, key=lambda e: float(e.attrib['score']))

                    assert len(resources) == 1
                    resource = urllib.parse.unquote(resources[0].split('#')[1])

                    esc = re.escape
                    match = re.match(
                        esc("cse(//*[@id='") + r"(?P<c>[^']+)" + esc("'],//*[@id='") + r"(?P<s>[^']+)" +
                        esc("'],//*[@id='") + r"(?P<e>[^']+)" + esc("'])"),
                        resource)

                    selectors = document.get_selector_converter().dom_to_selectors(
                        DomRange(start=DomPoint(document.get_node_for_id(match.group('s'))),
                                 end=DomPoint(document.get_node_for_id(match.group('e')), after=True)))
                        #     DomRange(start=DomPoint(htmltree.xpath(f"//*[@id='{match.group('s')}']")[0]),
                        #              end=DomPoint(htmltree.xpath(f"//*[@id='{match.group('e')}']")[0], after=True)))

                    uri = next(uri_generator)
                    target = FragmentTarget(
                        uri('target'), source=document.get_uri(),
                        selectors=selectors
                    )
                    yield from target.to_triples()
                    quant = process_cmml(cml)  # type: ignore
                    yield from Annotation(uri=uri('anno'), target_uri=target.uri, creator_uri=self.ctx.run_uri,
                                          body=RabQuantBody(scalar=quant[0], unit=quant[1])
                                          ).to_triples()


if __name__ == '__main__':
    import spotterbase.spotters.spotter_runner

    config_loader.auto()
    assert spotterbase.spotters.spotter_runner.DIRECTORY.value is not None, 'No output directory specified'
    spotterbase.spotters.spotter_runner.run(spotter_classes=[RabQuantImporter],
                                            documents=DocumentCorpus().get_documents(),
                                            corpus_descr='quantity expression data set',
                                            directory=spotterbase.spotters.spotter_runner.DIRECTORY.value)

# get_annotations(DocInfo('0001/astro-ph0001454/paper.html'))
