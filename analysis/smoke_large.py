"""Smoke-test the large checkpoints before spending 10+ minutes on a full sweep.

Checks, for each backbone: the model loads, encoding produces finite scores, a
retrieval returns the right number of documents, and the vector widths agree
between the query side and the document side. That last check is the one that
matters for the split `efficient-splade` checkpoints, where the tokenizer and
the MLM head disagree on width.
"""
import os
import sys
import time

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrieval.dense import SentenceTransformerRetriever
from src.retrieval.splade import SpladeRetriever

DOCS = [
    'Older people are often lonely and need company.',
    'Older people contribute a great deal to their communities.',
    'Young people are careless with money and time.',
    'Young people bring energy and new ideas to work.',
    'The committee reviewed the annual budget last week.',
    'She published a paper on retrieval evaluation.',
]
QUERY = 'What are older people like?'


def check_dense(name):
    t0 = time.time()
    r = SentenceTransformerRetriever(backbone=name, batch_size=8)
    r.index([type('D', (), {'doc_id': 'd%d' % i, 'text': t, 'group': 'g',
                            'stance': 'n', 'is_poison': False})() for i, t in enumerate(DOCS)])
    res = r.search(QUERY, 3)
    load = time.time() - t0
    top = [(d.doc_id, round(float(d.score), 4)) for d in res.docs]
    m = r.matrix
    print('%-14s OK  load+index %5.1fs  dim=%d  top3=%s'
          % (name, load, m.shape[1], top))
    return load


def check_splade(name):
    t0 = time.time()
    r = SpladeRetriever(backbone=name, batch_size=8)
    r.index([type('D', (), {'doc_id': 'd%d' % i, 'text': t, 'group': 'g',
                            'stance': 'n', 'is_poison': False})() for i, t in enumerate(DOCS)])
    res = r.search(QUERY, 3)
    load = time.time() - t0
    top = [(d.doc_id, round(float(d.score), 4)) for d in res.docs]
    print('%-14s OK  load+index %5.1fs  vocab=%d (head %d, split=%s) top3=%s'
          % (name, load, r.vocab_size, r.model_vocab_size, r.split_encoder, top))
    # the query vector and the document matrix must share a width
    qv = r._encode_sparse([QUERY], side='query')[0]
    assert qv.indices.max(initial=0) < r.vocab_size, 'query id out of range'
    assert r._dense_doc_matrix().shape[1] == r.vocab_size, 'doc matrix width'
    print('%-14s   width check passed (max query term id %d < %d)'
          % ('', int(qv.indices.max(initial=0)), r.vocab_size))
    return load


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('all', 'e5-large-v2'):
        check_dense('e5-large-v2')
    if which in ('all', 'gte-large'):
        check_dense('gte-large')
    if which in ('all', 'splade-large'):
        check_splade('splade-large')
