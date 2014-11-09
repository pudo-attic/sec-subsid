from lxml import html
from pprint import pprint
from common import filings


def parse_filing(filing):
    doc = html.fromstring(filing['content'])

    for tbl in doc.findall('.//table'):
        print tbl, filing.get('file_url')
        table = []
        headers = []
        for row in tbl.findall('.//tr'):
            data = {}
            if not len(headers):
                for hdr in row.findall('.//th'):
                    headers.append(hdr.xpath('string()').strip())
                for hdr in row.findall('.//td'):
                    headers.append(hdr.xpath('string()').strip())
                print headers
            else:
                for hdr, val in zip(headers, row.findall('.//td')):
                    data[hdr] = val.xpath('string()').strip()
                #pprint(data)


for filing in filings():
    parse_filing(filing)
