"""
This illustrates a bug in lxml's HTMLParser, which swallows a node if the 1508000th character is e.g. the 3 in '&#32;'
in a non-standard attribute of a node (it doesn't work for @id, at least) where the attribute value has at least 240 characters before.

TODO: report this as a bug to lxml
"""

from lxml import etree
from io import BytesIO


bio = BytesIO(b'<!DOCTYPE html>\n<html><body><div>\n' +
              1507708*b'X' +
              b'\n<span myattri="' + 240*b'Y' + b'&#32;"><span id="hello">HELLO WORLD</span></span>' +
              b'\n</div></body></html>\n'
              )

with open('/tmp/example.html', 'wb') as fp:
    fp.write(bio.read())   # parsing from bio directly doesn't cause a bug...

# tree = etree.parse(bio, parser=etree.HTMLParser())
tree = etree.parse('/tmp/example.html', parser=etree.HTMLParser())

spannode = tree.xpath('//span')[0]
print(etree.tostring(spannode))
