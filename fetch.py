import os
import unicodecsv
import json
import hashlib
import requests
from StringIO import StringIO
from common import DATA_PATH

URL = 'http://opendatalabs.org/misc/openoil/subsidiaries_1.csv'

res = requests.get(URL)
for row in unicodecsv.DictReader(StringIO(res.content)):
    url = row.get('file_url')
    fn = os.path.join(DATA_PATH, hashlib.sha1(url).hexdigest())
    if os.path.exists(fn):
        continue

    cn = row.get('company_name')
    r = requests.get(url)
    with open(fn, 'wb') as fh:
        row['content'] = r.content
        json.dump(row, fh)
