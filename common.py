import os
import json

DATA_PATH = 'filings'

try:
    os.makedirs(DATA_PATH)
except:
    pass


def filings():
    for filename in os.listdir(DATA_PATH):
        filename = os.path.join(DATA_PATH, filename)
        with open(filename, 'r') as fh:
            data = json.load(fh)
            yield data
