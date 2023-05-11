import importlib.util
import json
import sys

from spotterbase.corpora.resolver import Resolver
from spotterbase.model_core.oa import OA_JSONLD_CONTEXT
from spotterbase.model_core.record_class_resolver import ANNOTATION_RECORD_CLASS_RESOLVER
from spotterbase.model_core.sb import SB_JSONLD_CONTEXT
from spotterbase.model_core.target import FragmentTarget, populate_standard_selectors
from spotterbase.model_extra.record_class_resolver import SBX_RECORD_CLASS_RESOLVER
from spotterbase.model_extra.sbx import SBX_JSONLD_CONTEXT
from spotterbase.rdf import Uri
from spotterbase.rdf.vocab import OA
from spotterbase.records.jsonld_support import JsonLdRecordConverter
from spotterbase.records.record_class_resolver import RecordClassResolver
from spotterbase.records.record_loading import load_all_records_transitively
from spotterbase.records.sparql_populate import Populator
from spotterbase.sparql.sb_sparql import get_data_endpoint
from spotterbase.utils import config_loader
from spotterbase.utils.progress_updater import ProgressUpdater


modules = {}

for modname, path in [
    ('rabdoc', '/home/jfs/git/github.com/jfschaefer/spotters/quantity_expr_rab/document_corpus.py'),
    ('rabvocab', '/home/jfs/git/github.com/jfschaefer/spotters/quantity_expr_rab/vocab.py'),
    ('asadoc', '/home/jfs/git/github.com/jfschaefer/spotters/id_grounding_asa/document_corpus.py'),
    ('asavocab', '/home/jfs/git/github.com/jfschaefer/spotters/id_grounding_asa/vocab.py'),
]:
    spec = importlib.util.spec_from_file_location(modname, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    spec.loader.exec_module(module)
    modules[modname] = module


def main(document: Uri, name: str):
    endpoint = get_data_endpoint()

    populator = Populator(
        record_type_resolver=RecordClassResolver.merged(ANNOTATION_RECORD_CLASS_RESOLVER, SBX_RECORD_CLASS_RESOLVER,
                                                        RecordClassResolver([getattr(modules['rabvocab'], 'RabQuantBody'),
                                                                             getattr(modules['asavocab'], 'AsaGroundingBody')])),
        endpoint=endpoint,
        special_populators={FragmentTarget: [populate_standard_selectors]},
        chunk_size=50)
    converter = JsonLdRecordConverter(
        contexts=[OA_JSONLD_CONTEXT, SB_JSONLD_CONTEXT, SBX_JSONLD_CONTEXT],
        record_type_resolver=populator.record_type_resolver,
    )

    query = f'''
SELECT DISTINCT ?anno WHERE {{
    ?anno {OA.hasTarget:<>}/{OA.hasSource:<>} {document:<>} .
}}
    '''

    query_result = endpoint.query(query)
    uris = [r['anno'] for r in query_result]
    print(query)
    print(uris)

    records = load_all_records_transitively(uris, populator)
    progress_logger = ProgressUpdater('Status update: Loaded {progress} records')
    results: list = []
    for i, record in enumerate(records):
        progress_logger.update(i)
        results.append(converter.record_to_json_ld(record))

    with open(f'/tmp/{name}.annos.jsonld', 'w') as fp:
        json.dump(results, fp, indent=4)

    with open(f'/tmp/{name}.html', 'wb') as fp:
        with Resolver.get_document(document).open('rb') as fp2:
            fp.write(fp2.read())


if __name__ == '__main__':
    config_loader.auto()

    # main(Uri('https://sigmathling.kwarc.info/resources/quantity-expressions/corpus/0001/astro-ph0001454/paper.html'), 'unitpaper')
    # main(Uri('http://sigmathling.kwarc.info/arxmliv/2020/0704.0005'), '0704.0005')
    main(Uri('https://sigmathling.kwarc.info/resources/grounding-dataset/corpus/2002.06823.html'), 'id_grounding')
