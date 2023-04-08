from pyutils.timer import CumulativeTimer

from spotterbase.corpora.resolver import Resolver
from spotterbase.dnm.simple_dnm_factory import ARXMLIV_STANDARD_DNM_FACTORY
from spotterbase.rdf import Uri
from spotterbase.utils import config_loader

config_loader.auto()


load_timer = CumulativeTimer('load')
parse_timer = CumulativeTimer('parse')
offset_timer = CumulativeTimer('offs')
dnm_timer = CumulativeTimer('dnm')


for u in ['0364', '2455', '0519', '3406', '0266', '3735', '2317', '1440', '1137', '1566', '0359', '3120', '4580',
    '1548', '1450', '2277', '2305', '0135', '0048', '0671', '2614', '3080', '1580', '3222', '3941', '3048', '2560',
    '2836', '4670', '4009']:
    with load_timer:
        document = Resolver.get_document(Uri('http://sigmathling.kwarc.info/arxmliv/2020/0901.' + u))

    with document.open() as fp:
        content = fp.read()     # make sure everything is accessbile

    with parse_timer:
        tree = document.get_html_tree(cached=True)

    with offset_timer:
        offs = document.get_offset_converter()

    with dnm_timer:
        # dnm = TokenBasedDnm.from_token_generator(tree, DefaultGenerators.ARXMLIV_TEXT_ONLY)
        # s = dnm.get_dnm_str()
        s = ARXMLIV_STANDARD_DNM_FACTORY.dnm_from_document(document)
        print(len(s))

for timer in [load_timer, parse_timer, offset_timer, dnm_timer]:
    print(timer.info_string())

