from contextlib import closing

import pytest

from app.context import store
from app.crawl.queue import CrawlQueue
from app.crawl.writer import DocWriter
from app.prep.documents import crawl_docs, filter_documents


def put_collection(data_dir, sid, cid, parent, docs):
    root = data_dir / 'crawl' / sid / 'collections' / cid
    store.write_json(root / 'manifest.json', {'id': cid, 'parent': parent})
    with closing(CrawlQueue(root / 'queue.sqlite')) as queue:
        queue.finish_run(queue.register_run('detail'), 'done')
    writer = DocWriter(root / 'docs')
    try:
        for doc in docs:
            writer.write(doc)
    finally:
        writer.close()


def document(doc_id, **kwargs):
    return dict(doc_id=doc_id, source='youtube', title='', body='충분히 긴 본문 내용입니다', comments=[{'text': '댓글 내용'}],
                src_meta={}, url=f'https://example.test/{doc_id}', fetch_level='full', **kwargs)


def test_collection_chain_child_wins_and_export_fields(data_dir):
    parent = document('shared')
    child = {**parent, 'body': '자식 수집본의 본문 내용입니다', 'src_meta': {'cafe': '지정 카페'}}
    put_collection(data_dir, 's', 'c1', None, [parent, document('parent')])
    put_collection(data_dir, 's', 'c2', 'c1', [child, document('child'), child])
    put_collection(data_dir, 's', 'c3', None, [document('unrelated')])
    raw = crawl_docs('s', {'collectionId': 'c2'})
    filtered, removed = filter_documents(raw)
    docs = {d['doc_id']: d for d in filtered}
    assert set(docs) == {'shared', 'parent', 'child'}
    assert docs['shared']['desc'] == child['body'] + '\n댓글 내용'
    assert docs['shared']['cafe'] == '지정 카페'
    assert docs['parent']['cafe'] == '유튜브'
    assert docs['shared']['link'] == child['url']
    assert all(docs['shared'][k] == v for k, v in child.items())
    assert removed == {'ad': 0, 'excluded_source': 0, 'duplicate': 0, 'too_short': 0}


@pytest.mark.parametrize('cid', ['', 'x1', 'c0', '../c1', None])
def test_crawl_docs_rejects_invalid_collection(data_dir, cid):
    with pytest.raises(ValueError):
        crawl_docs('s', {'collectionId': cid})


def test_crawl_docs_rejects_cycle(data_dir):
    put_collection(data_dir, 's', 'c1', 'c2', [document('a')])
    put_collection(data_dir, 's', 'c2', 'c1', [document('b')])
    with pytest.raises(ValueError, match='Cyclic'):
        crawl_docs('s', {'collectionId': 'c1'})


def test_quality_rules_and_desc_limit():
    docs = [document('full'), {**document('short'), 'body': '짧음'},
            {**document('long'), 'body': '긴' * 4100},
            {**document('snippet_ok'), 'fetch_level': 'snippet', 'title': '다섯글자제목', 'body': '', 'snippet': '충분히 긴 설명 내용입니다'},
            {**document('snippet_bad_title'), 'fetch_level': 'snippet', 'title': '짧음', 'snippet': '충분히 긴 설명 내용입니다'},
            {**document('snippet_bad_desc'), 'fetch_level': 'snippet', 'title': '다섯글자제목', 'body': '', 'snippet': '짧음'},
            {**document('snippet_both_short'), 'fetch_level': 'snippet', 'title': '짧음', 'body': '', 'snippet': '짧음'}]
    filtered, removed = filter_documents(docs)
    result = {d['doc_id']: d for d in filtered}
    assert set(result) == {'full', 'long', 'snippet_ok', 'snippet_bad_title', 'snippet_bad_desc'}
    assert result['long']['desc'] == '긴' * 4000
    assert removed['too_short'] == 2


def test_excludes_cafe_name_and_slug_not_body():
    docs = [
        {'doc_id': 'name', 'src_meta': {'cafe': 'Joong market'}},
        {'doc_id': 'slug', 'src_meta': {'cafe': '중고나라', 'cafe_id': 'joonggonara'}},
        {'doc_id': 'keep', 'src_meta': {'cafe': 'Other', 'cafe_id': 'other', 'note': 'joong'}},
        {'doc_id': 'no_meta'},
    ]
    docs = [{**doc, 'body': 'joong in article content is retained', 'fetch_level': 'full'} for doc in docs]
    filtered, removed = filter_documents(docs, excluded=['JOONG'])
    assert [doc['doc_id'] for doc in filtered] == ['keep', 'no_meta']
    assert removed['excluded_source'] == 2


def test_full_text_ads_channel_exclusion_and_duplicates():
    docs = [{**document('ad'), 'comments': [{'text': '협찬 받은 글'}]},
            {**document('chan'), 'source': 'naver_blog'},
            document('dup'), document('dup')]
    filtered, removed = filter_documents(docs, ad_filter=['협찬'], excluded=['naver_blog'], full_text=True)
    assert [d['doc_id'] for d in filtered] == ['dup']
    assert removed == {'ad': 1, 'excluded_source': 1, 'duplicate': 1, 'too_short': 0}
    assert filtered[0]['idx'] == 2
