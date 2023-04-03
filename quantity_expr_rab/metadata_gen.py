import logging

from quantity_expr_rab.document_corpus import DocumentCorpus, iter_doc_info
from spotterbase.anno_core.sb import SB
from spotterbase.corpora.arxiv import ArxivUris
from spotterbase.data.locator import DataDir
from spotterbase.rdf import FileSerializer
from spotterbase.rdf.vocab import RDF
from spotterbase.utils import config_loader

logger = logging.getLogger(__name__)

dest_file = DataDir.get('rab-quantexpr-metadata.ttl.gz')

config_loader.auto()


def get_triples():
    corpus_uri = DocumentCorpus.uri
    yield corpus_uri, RDF.type, SB.Dataset
    yield corpus_uri, SB.isBasedOn, ArxivUris.dataset
    for doc_info in iter_doc_info():
        yield doc_info.to_uri(), SB.isBasedOn, doc_info.get_arxivid().as_uri()
        yield doc_info.to_uri(), RDF.type, SB.Document
        yield doc_info.to_uri(), SB.belongsTo, corpus_uri


logger.info(f'Writing meta data to {dest_file}')
with FileSerializer(dest_file) as fp:
    fp.add_from_iterable(get_triples())

logger.info('Done')
