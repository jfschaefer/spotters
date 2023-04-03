import logging

from id_grounding_asa.document_corpus import DocumentCorpus
from spotterbase.anno_core.sb import SB
from spotterbase.corpora.arxiv import ArxivUris
from spotterbase.data.locator import DataDir
from spotterbase.rdf import FileSerializer
from spotterbase.rdf.vocab import RDF
from spotterbase.utils import config_loader

logger = logging.getLogger(__name__)

dest_file = DataDir.get('id-grounding-asa-metadata.ttl.gz')

config_loader.auto()


def get_triples():
    corpus_uri = DocumentCorpus.uri
    yield corpus_uri, RDF.type, SB.Dataset
    yield corpus_uri, SB.isBasedOn, ArxivUris.dataset
    for doc in DocumentCorpus():
        yield doc.get_uri(), SB.isBasedOn, doc.arxivid.as_uri()
        yield doc.get_uri(), RDF.type, SB.Document
        yield doc.get_uri(), SB.belongsTo, corpus_uri


logger.info(f'Writing meta data to {dest_file}')
with FileSerializer(dest_file) as fp:
    fp.add_from_iterable(get_triples())

logger.info('Done')
