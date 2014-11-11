import os
import re
import unicodecsv
import nltk
from nltk.util import ngrams
from lxml import html
from collections import defaultdict
from unicodedata import normalize as ucnorm, category
from pprint import pprint
from common import filings
import dataset

REMOVE_SPACES = re.compile(r'\s+')

eng = dataset.connect('sqlite://')
col_types = eng['col_types']
col_types._ensure_columns({'type': ''})
row_types = eng['row_types']
row_types._ensure_columns({'type': ''})
columns_classifier = None
rows_classifier = None


def normalize_text(text):
    if not isinstance(text, unicode):
        text = unicode(text)
    chars = []
    # http://www.fileformat.info/info/unicode/category/index.htm
    for char in ucnorm('NFKD', text):
        cat = category(char)[0]
        #if char == '.':
        #    continue
        if cat in ['C', 'Z']:
            chars.append(u' ')
        elif cat in ['M', 'P']:
            continue
        else:
            chars.append(char)
    text = u''.join(chars)
    text = REMOVE_SPACES.sub(' ', text)
    return text.strip().lower()


def features(text):
    f = defaultdict(int)

    p = text.split('\t')
    f['_first'] = p[0]
    f['_lens'] = sum(map(len, p)) / float(len(p))
    words = normalize_text(text).split()

    for n in [1, 2, 3]:
        for word in ngrams(words, n):
            word = ' '.join(word)
            if len(word) < 3:
                continue
            f[word] += 1
    return dict(f.items())


def read_data(file_name, table):
    train_set = []
    if not os.path.exists(file_name):
        return
    with open(file_name, 'r') as fh:
        for row in unicodecsv.DictReader(fh):
            del row['id']
            if 'type' in row and row['type']:
                table.upsert(row, ['text'])
                train_set.append((features(row.get('text')), row.get('type')))
    return train_set


def el_text(el):
    text = el.text_content()
    return text.strip()


def classify_table(table):
    columns = defaultdict(list)
    row_guesses = {}
    col_guesses = {}
    for n, row in enumerate(table):
        row_text = '\t'.join(row)
        print features(row_text)
        guess = rows_classifier.classify(features(row_text))
        row_guesses[n] = guess
        row_types.upsert({'text': row_text}, ['text'])
        for i, col in enumerate(row):
            columns[i].append(col)

    for n, col in enumerate(columns.values()):
        col_text = '\t'.join(col)
        guess = columns_classifier.classify(features(col_text))
        col_guesses[n] = guess
        col_types.upsert({'text': col_text}, ['text'])

    for x, row in enumerate(table):
        for y, cell in enumerate(row):
            data = {
                'value': cell,
                'row_type': row_guesses[x],
                'col_type': col_guesses[y]
            }
            pprint(data)


def collapse_table(table):
    col_lens = defaultdict(int)
    for row in table:
        for i, v in enumerate(row):
            col_lens[i] += len(v)

    red_table = []
    for row in table:
        if len(''.join(row)) < 2:
            continue
        red_row = []
        for i, c in enumerate(row):
            if col_lens[i] > 0:
                red_row.append(c)
        red_table.append(red_row)
    return red_table


def parse_filing(filing):
    doc = html.fromstring(filing['content'])

    for tbl in doc.findall('.//table'):
        print tbl, filing.get('file_url')
        table = []
        for row in tbl.findall('.//tr'):
            rowvs = map(el_text, row.xpath('.//th | .//td'))
            table.append(rowvs)
        table = collapse_table(table)
        classify_table(table)
        #print table


columns_train = read_data('train/columns.csv', col_types)
columns_classifier = nltk.NaiveBayesClassifier.train(columns_train)
rows_train = read_data('train/rows.csv', row_types)
rows_classifier = nltk.NaiveBayesClassifier.train(rows_train)

for filing in filings():
    parse_filing(filing)

dataset.freeze(col_types, filename='train/columns.csv', format='csv')
dataset.freeze(row_types, filename='train/rows.csv', format='csv')
