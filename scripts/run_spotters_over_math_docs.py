import logging
from pathlib import Path

from scripts.run_spotters_on_doc import get_spotters
from spotterbase.corpora.arxiv import ArxivCategory
from spotterbase.corpora.arxmliv import ARXMLIV_CORPORA, ArXMLivUris
from spotterbase.corpora.resolver import Resolver
from spotterbase.model_core.sb import SB
from spotterbase.rdf.vocab import OA, RDF
from spotterbase.sparql.sb_sparql import get_data_endpoint
from spotterbase.spotters import spotter_runner
from spotterbase.utils import config_loader

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    config_loader.auto()

    query = f'''
SELECT DISTINCT ?doc WHERE {{
    ?doc {SB.belongsTo:<>} {ARXMLIV_CORPORA["2020"].get_uri():<>} .
    ?doc {SB.isBasedOn:<>} ?arxivdoc .
    ?anno {OA.hasTarget:<>} ?arxivdoc .
    ?anno {OA.hasBody:<>}/{RDF.value:<>} {ArxivCategory("math").as_uri():<>} .
    ?anno2 {OA.hasTarget:<>} ?doc .
    ?anno2 {OA.hasBody:<>}/{RDF.value:<>} {ArXMLivUris.severity_warning:<>} .
}}
'''

    query_result = get_data_endpoint().query(query)
    uris = [r['doc'] for r in query_result]
    uris.sort(key=str)

    logger.info(f'Found {len(uris)} relevant documents')

    spotter_runner.run(
        get_spotters(),
        # [Resolver.get_document(Uri('http://sigmathling.kwarc.info/arxmliv/2020/0901.3956'))],
        [Resolver.get_document(uri) for uri in uris[:100000]],
        corpus_descr='individual document',
        directory=Path('/drive/spotterbase/math-warning-first-100000-decls')
    )
