import os
import polib
from lxml import etree

countries = ('fr', 'be', 'it', 'mc', 'es', 'ch', 'gb', 'us')


def truncate_records():
    to_remove = []
    with open('data.xml', 'r') as f:
        tree = etree.parse(f)
    for element in tree.xpath("//record[@model='country.country']"):
        if element.attrib['id'] not in countries:
            to_remove.append(element)
    for element in tree.xpath("//record[@model='country.subdivision']"):
        if element.attrib['id'][0:2] not in countries:
            to_remove.append(element)
    for element in to_remove:
        element.getparent().remove(element)
    with open('data.xml', 'wb') as f:
        f.write(b'<?xml version="1.0"?>\n')
        tree.write(f, pretty_print=True, encoding='utf-8')


def truncate_translations():
    country_prefix = 'model:country.country,name:'
    country_msgctxt = tuple([country_prefix + c for c in countries])
    subdiv_prefix = 'model:country.subdivision,name:'
    subdiv_msgctxt = tuple([subdiv_prefix + c for c in countries])
    for f in os.listdir('locale'):
        fname = 'locale/' + f
        po = polib.pofile(fname)
        for r in range(len(po) - 1, 0, -1):
            msg = po[r].msgctxt
            if msg != country_prefix and msg.startswith(country_prefix) and\
                    msg not in country_msgctxt:
                po.pop(r)
            if msg != subdiv_prefix and msg.startswith(subdiv_prefix) and\
                    not msg.startswith(subdiv_msgctxt):
                po.pop(r)
        po.save(fname)


if __name__ == '__main__':
    truncate_records()
    truncate_translations()
