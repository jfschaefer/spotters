from pathlib import Path
from typing import Iterator, IO

from id_grounding_asa.vocab import ASA
from spotterbase.corpora.arxiv import ArxivId
from spotterbase.corpora.arxmliv import ArXMLivCorpus
from spotterbase.corpora.interface import Corpus, Document, DocumentNotInCorpusException, CannotLocateCorpusDataError
from spotterbase.data.locator import Locator
from spotterbase.rdf import Uri

DATA_LOCATOR = Locator(
    '--id-grounding-asa-data', 'Folder with the .zip files of the quantity expression dataset', ['grounding-dataset'],
    'More information on the dataset can be found here: https://sigmathling.kwarc.info/resources/grounding-dataset/'
)


class AsaDocument(Document):
    def __init__(self, path: Path, uri: Uri, arxivid: ArxivId):
        self.path = path
        self.uri = uri
        self.arxivid = arxivid

    def get_uri(self) -> Uri:
        return self.uri

    def open(self, *args, **kwargs) -> IO:
        return open(self.path, *args, **kwargs)


class DocumentCorpus(Corpus):
    uri = ASA.corpus

    def __iter__(self) -> Iterator[AsaDocument]:
        if (datasetpath := DATA_LOCATOR.location_opt()) is None:
            raise CannotLocateCorpusDataError()
        for file in (datasetpath / 'sources').glob('*.html'):
            yield self.get_document(DocumentCorpus.uri / file.name)

    def get_document(self, uri: Uri) -> Document:
        if not uri.starts_with(DocumentCorpus.uri):
            raise DocumentNotInCorpusException()
        file = uri.relative_to(DocumentCorpus.uri)[1:]
        if (datasetpath := DATA_LOCATOR.location_opt()) is None:
            raise CannotLocateCorpusDataError()
        arxivid = ArXMLivCorpus.filename_to_arxivid_or_none(file)
        assert arxivid is not None, f'Failed to infer arxiv id from {file!r}'
        return AsaDocument(datasetpath / 'sources' / file, uri, arxivid)

    def get_uri(self) -> Uri:
        return self.uri

