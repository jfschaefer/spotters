# background: Virtuoso is very efficient, but uploading large amounts of data is a pain because of various bugs
import gzip
import sys
from pathlib import Path

from spotterbase.rdf import Uri
from spotterbase.sparql.endpoint import Virtuoso
from spotterbase.utils import config_loader

# hacky (should separate at right places because of bnodes. This only works for the scripts I'm currently interested in)

config_loader.auto()

# file = Path('/drive/spotterbase/math-warning-first-100000-decls/sdecl.nt.gz')
# tmpfile = Path('/tmp/spotterbase/extracted.nt')
# graph = Uri(f'http://localhost:8890/graph/math-warning-first-100000/sdecl')

file = Path('/tmp/asa.nt.gz')
tmpfile = Path('/tmp/spotterbase/extracted.nt')
graph = Uri(f'http://localhost:8890/asa_id_grounding_data')

endpoint = Virtuoso()
endpoint.update(f'CLEAR GRAPH {graph:<>}')

with gzip.open(file, 'rt') as fp:
    lines = iter(fp)
    total_length = 0

    done = False

    while not done:
        length = 0
        try:
            with open(tmpfile, 'w') as fp:
                while length < 10000000 - 50000:
                    line: str = next(lines)  # type: ignore
                    fp.write(line)
                    length += len(line)
                while True:
                    line: str = next(lines)   # type: ignore
                    fp.write(line)
                    # if 'http://purl.org/dc/terms/creator' in line:
                    if 'Annotation' in line:
                        break
        except StopIteration:
            done = True
        endpoint.update(f'LOAD {Uri(tmpfile):<>} INTO GRAPH {graph:<>}')

        total_length += length
        print(total_length)
