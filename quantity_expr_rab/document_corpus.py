from __future__ import annotations

from pathlib import Path

import dataclasses
from typing import Iterator, IO

from quantity_expr_rab.vocab import RAB
from spotterbase.corpora.arxiv import ArxivId
from spotterbase.corpora.interface import Corpus, Document, DocumentNotFoundError, DocumentNotInCorpusException
from spotterbase.corpora.resolver import Resolver
from spotterbase.data.locator import Locator
from spotterbase.data.zipfilecache import SHARED_ZIP_CACHE
from spotterbase.rdf import Uri
from spotterbase.utils import config_loader

DATA_LOCATOR = Locator(
    '--quantexpr-rab-data', 'Folder with the .zip files of the quantity expression dataset', ['quantexpr-rab-data'],
    'More information on the dataset can be found here: https://sigmathling.kwarc.info/resources/quantity-expressions/'
)


@dataclasses.dataclass
class DocInfo:
    path: str

    def to_uri(self) -> Uri:
        return DocumentCorpus.uri / self.path

    @classmethod
    def from_uri(cls, uri: Uri):
        if not uri.starts_with(DocumentCorpus.uri):
            raise DocumentNotInCorpusException()
        return DocInfo(uri.relative_to(DocumentCorpus.uri)[1:])

    def get_arxivid(self) -> ArxivId:
        return ArxivId(self.path.split('/')[1])

    @classmethod
    def from_kat_filename(cls, kat_filename: str) -> DocInfo:
        assert kat_filename.endswith('.kat.xml')
        yield DocInfo(kat_filename[:-len('.kat.xml')] + '.html')

    def to_kat_filename(self) -> str:
        return self.path[:-len('.html')] + '.kat.xml'

    def to_html_filename(self) -> str:
        return self.path


def iter_doc_info() -> Iterator[DocInfo]:
    with SHARED_ZIP_CACHE[DATA_LOCATOR.require() / 'Annotations.zip'] as file:
        for entry in file.filelist:
            if entry.is_dir():
                continue
            assert entry.filename.endswith('.kat.xml')
            yield DocInfo(entry.filename[:-len('.kat.xml')] + '.html')


class RabDoc(Document):
    def __init__(self, arxivid: ArxivId, path_to_zipfile: Path, filename: str, uri: Uri):
        self.arxivid: ArxivId = arxivid
        self.path_to_zipfile = path_to_zipfile
        self.filename = filename
        self.uri = uri

    def get_uri(self) -> Uri:
        return self.uri

    def open(self, *args, **kwargs) -> IO:
        zf = SHARED_ZIP_CACHE[self.path_to_zipfile]
        try:
            return zf.open(self.filename, *args, **kwargs)
        except KeyError as e:
            missing = DocumentNotFoundError(f'Failed to find {self.filename} in {self.path_to_zipfile}: {e}')
            missing.__suppress_context__ = True
            raise missing


def _document_from_doc_info(doc_info: DocInfo) -> RabDoc:
    return RabDoc(
        arxivid=doc_info.get_arxivid(),
        path_to_zipfile=DATA_LOCATOR.require() / 'Documents.zip',
        filename=doc_info.to_html_filename(),
        uri=doc_info.to_uri(),
    )


class DocumentCorpus(Corpus):
    uri: Uri = RAB.corpus

    def get_uri(self) -> Uri:
        return self.uri

    def get_document(self, uri: Uri) -> RabDoc:
        return _document_from_doc_info(DocInfo.from_uri(uri))

    def __iter__(self) -> Iterator[RabDoc]:
        for doc_info in iter_doc_info():
            yield _document_from_doc_info(doc_info)


Resolver.register_corpus(DocumentCorpus())


if __name__ == '__main__':
    config_loader.auto()
    iter_doc_info()
