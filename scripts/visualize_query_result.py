import sys

from lxml import etree

from spotterbase.corpora.resolver import Resolver
from spotterbase.rdf import Uri
from spotterbase.utils import config_loader
from spotterbase.utils.config_loader import ConfigLoader


args = sys.argv[1:-1]
ConfigLoader().load_from_args(args)


with open(sys.argv[-1]) as infp, open('/tmp/results.html', 'wb') as outfp:
    outfp.write(b'<html><body>\n')
    for line in infp:
        print('processing', line)
        line = line.strip()
        if not line:
            continue
        number, uri = line.split()

        outfp.write(f'<h1>{number}</h1>\n'.encode())

        doc = Resolver.get_document(Uri(uri.split('#')[0]))
        tree = doc.get_html_tree(cached=True)

        node = tree.xpath(uri.split('#')[1])[0]
        while node.tag != 'math':
            node = node.getparent()
        node.tail = ''

        outfp.write(etree.tostring(node))

        # node.attrib['style'] = 'background: orange'

    outfp.write(b'</body></html>\n')

