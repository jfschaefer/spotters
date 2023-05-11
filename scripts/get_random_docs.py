import random
from pathlib import Path

from spotterbase.corpora.arxmliv import ArXMLivDocument, ARXMLIV_CORPORA
from spotterbase.utils import config_loader

config_loader.auto()
documents = list(ARXMLIV_CORPORA['2020'].get_documents())

path = Path('/tmp/random_docs')
path.mkdir(exist_ok=True)

for i in range(10):
    print(i)
    doc: ArXMLivDocument = random.choice(documents)
    with open(path/f'{doc.arxivid:fn}.html', 'wb') as fp:
        with doc.open() as fp2:
            fp.write(fp2.read())
