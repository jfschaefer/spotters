import importlib.util
import sys
from pathlib import Path

from spotterbase.corpora.resolver import Resolver
from spotterbase.rdf import Uri
from spotterbase.spotters import spotter_runner
from spotterbase.spotters.example_spotters.simple_declaration_spotter import SimpleDeclarationSpotter
from spotterbase.spotters.example_spotters.simple_pos_tag_spotter import SimplePosTagSpotter
from spotterbase.utils import config_loader

spotters = [SimplePosTagSpotter, SimpleDeclarationSpotter]

spotters_dir = Path(__file__).parent.parent

for path, modname, spotterclass in [
    (spotters_dir / 'ams-paragraph-classification' / '__init__.py', 'amsspotter', 'AmsParaSpotter')
]:
    spec = importlib.util.spec_from_file_location(modname, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    spec.loader.exec_module(module)
    spotters.append(getattr(module, spotterclass))

config_loader.auto()

spotter_runner.run(
    spotters,
    [Resolver.get_document(Uri('http://sigmathling.kwarc.info/arxmliv/2020/0901.3956'))],
    corpus_descr='individual document',
    directory=Path('/tmp/spotterrun')
)
