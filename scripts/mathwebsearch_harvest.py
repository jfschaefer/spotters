import datetime
import logging
import multiprocessing
from pathlib import Path

from lxml import etree

from spotterbase.corpora.arxiv import ArxivCategory
from spotterbase.corpora.arxmliv import ARXMLIV_CORPORA, ArXMLivUris, ArXMLivDocument
from spotterbase.corpora.resolver import Resolver
from spotterbase.model_core.sb import SB
from spotterbase.rdf import Uri
from spotterbase.rdf.vocab import OA, RDF
from spotterbase.sparql.sb_sparql import get_data_endpoint
from spotterbase.utils import config_loader
from spotterbase.utils.progress_updater import ProgressUpdater

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    config_loader.auto()

    query = f'''
SELECT DISTINCT ?doc WHERE {{
    ?doc {SB.belongsTo:<>} {ARXMLIV_CORPORA["2020"].get_uri():<>} .
    ?doc {SB.isBasedOn:<>} ?arxivdoc .
    ?anno {OA.hasTarget:<>} ?arxivdoc .
    ?anno {OA.hasBody:<>}/{RDF.value:<>} {ArxivCategory("astro-ph").as_uri():<>} .
    ?anno2 {OA.hasTarget:<>} ?doc .
    ?anno2 {OA.hasBody:<>}/{RDF.value:<>} {ArXMLivUris.severity_no_problem:<>} .
}}
'''

    query_result = get_data_endpoint().query(query)
    uris = [r['doc'] for r in query_result]
    uris.sort(key=str)

    logger.info(f'Found {len(uris)} relevant documents')

    directory = Path('/tmp/harvest')
    directory.mkdir(exist_ok=False)

    timestamp = datetime.datetime.now().isoformat()

    def process(uri: Uri):
        document = Resolver.get_document(uri)
        formula_count = 0
        harvest = etree.Element("{http://search.mathweb.org/ns}harvest",
                                nsmap={'mws': 'http://search.mathweb.org/ns',
                                       'm': 'http://www.w3.org/1998/Math/MathML'})
        # ts = etree.SubElement(harvest, 'timestamp')
        # ts.text = timestamp
        tree = document.get_html_tree(cached=True)
        for node in tree.xpath('//annotation-xml/*'):
            formula_count += 1
            f = etree.SubElement(harvest, '{http://search.mathweb.org/ns}expr')
            f.attrib['url'] = document.get_uri().full_uri() + '#' + tree.getpath(node)
            for subnode in node.iter():
                subnode.tag = 'm:' + subnode.tag
            f.insert(0, node)

        assert isinstance(document, ArXMLivDocument)

        with open(directory / f'{document.arxivid.identifier.replace("/", "")}.harvest', 'wb') as fp:
            fp.write(etree.tostring(harvest, pretty_print=True))

        return formula_count


    progress_updater = ProgressUpdater('{progress} documents processed')
    formula_count = 0

    with multiprocessing.Pool(processes=8) as pool:
        for i, formulae in enumerate(pool.imap_unordered(process, uris[:50000], chunksize=5)):
            progress_updater.update(i)
            formula_count += formulae

    logger.info(f'Found {formula_count} formulae')
    logger.info(f'Done')
