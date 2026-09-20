"""Validate the collected corpus and source evidence; no embedding or retrieval."""
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT/'data/ecommerce'
EVIDENCE = ROOT/'docs/collection-evidence'
REQUIRED = {'doc_id','title','source_url','retrieved_at','document_version','audience','category','language'}


def read_document(path):
    text = path.read_text(encoding='utf-8')
    match = re.fullmatch(r'---\n(.*?)\n---\n\n(.*)', text, re.S)
    assert match, f'{path.name}: invalid frontmatter'
    # Generated YAML uses JSON double-quoted strings, a strict YAML subset.
    metadata = {line.split(': ',1)[0]: json.loads(line.split(': ',1)[1]) for line in match[1].splitlines()}
    return metadata, match[2]


def main():
    messages = []
    docs = {}
    files = sorted(CORPUS.glob('*.md'))
    assert 5 <= len(files) <= 10
    inputs = list(csv.DictReader((ROOT/'data/urls.csv').open(encoding='utf-8',newline='')))
    rows = list(csv.DictReader((CORPUS/'sources.csv').open(encoding='utf-8',newline='')))
    audits = json.loads((EVIDENCE/'content-audit.json').read_text(encoding='utf-8'))
    logs = json.loads((EVIDENCE/'fetch-log.json').read_text(encoding='utf-8'))
    robots = RobotFileParser()
    robots.parse((EVIDENCE/'ofn-robots.txt').read_text().splitlines())
    for path in files:
        meta, body = read_document(path)
        assert REQUIRED <= meta.keys() and all(meta[k] for k in REQUIRED)
        assert meta['doc_id'] == path.stem and path.stem not in docs
        assert meta['audience'] in ('buyer','seller','both') and meta['language'] == 'en'
        datetime.strptime(meta['retrieved_at'],'%Y-%m-%d')
        assert meta['license_or_permission'] == 'CC-BY-SA-4.0'
        assert meta['attribution'] and meta['permission_source'] and meta['changes']
        assert len(body) >= 80 and len(re.findall(r'^#{2,6} .+',body,re.M)) >= 2
        assert not any(s in body for s in ('example.com','{%','<img','token=','For the complete documentation index'))
        assert robots.can_fetch('Day7DataFoundationsCourse/1.0 (+educational-lab)',meta['source_url'])
        manifest = [r for r in rows if r['doc_id'] == path.stem]
        source_input = [r for r in inputs if r['doc_id'] == path.stem]
        audit = next(a for a in audits if a['doc_id'] == path.stem)
        assert len(manifest) == len(source_input) == 1
        assert manifest[0]['file_path'] == path.relative_to(ROOT).as_posix()
        for key in ('title','source_url','retrieved_at','document_version','license_or_permission'):
            assert manifest[0][key] == meta[key]
        assert source_input[0]['url'] == meta['source_url']
        for key in ('title','audience','category','language','document_version','license_or_permission'):
            assert source_input[0][key] == meta[key]
        assert audit['body_characters'] == len(body)
        assert audit['body_sha256'] == hashlib.sha256(body.encode()).hexdigest()
        request = next(r for r in logs if r['url'] == audit['fetch_url'])
        assert request['status'] == 200 and request['sha256'] == audit['raw_sha256']
        assert request['content_type'] == 'text/markdown' and request['started_at'][:10] == meta['retrieved_at']
        assert robots.can_fetch('Day7DataFoundationsCourse/1.0 (+educational-lab)',request['url'])
        docs[path.stem] = (meta,body)
        messages.append(f'OK {path.name}: metadata, manifest, source HTTP 200, body hash, headings')
    assert len(rows) == len(inputs) == len(audits) == len(docs)
    assert set(r['doc_id'] for r in rows) == set(docs)
    audiences = Counter(meta['audience'] for meta,_ in docs.values())
    assert {'buyer','seller'} <= audiences.keys()
    gaps = [(datetime.fromisoformat(b['started_at'])-datetime.fromisoformat(a['finished_at'])).total_seconds() for a,b in zip(logs,logs[1:])]
    assert min(gaps) >= 1
    queries = json.loads((ROOT/'report/benchmark_queries.json').read_text(encoding='utf-8'))
    assert len(queries) == 5 and len({q['id'] for q in queries}) == 5
    for query in queries:
        for e in query['evidence']:
            meta,body = docs[e['doc_id']]
            assert e['quote'] in body, (query['id'], e['quote'])
            headings = re.findall(r'^#{1,6} (.*)$',body,re.M)
            assert e['heading'] in [h.replace('*','').strip() for h in headings]
            assert meta['audience'] == query['metadata_filter']['audience']
        assert query['status'] in ('prepared-not-run', 'ready-for-benchmark')
    buyer = docs['ofn-buyer-faq'][1]
    seller = docs['ofn-seller-orders'][1]
    assert 'You will not be able to add extra products to this basket though.' in buyer
    assert 'You can add a product to the order by selecting the variant you require' in seller
    messages += [f'OK files: {len(docs)}; sources.csv and urls.csv match 1:1',f'OK audience: {dict(audiences)}',f'OK request delay: minimum {min(gaps):.3f}s (after previous response)', 'OK 5 benchmark specifications: all evidence quotes and headings exist', 'OK buyer/seller contrast for Q1: cannot add vs admin can add', 'SCOPE: source validation only; benchmark runs are recorded separately in report/cp5/', 'PENDING: real member names and role confirmation, as requested by user']
    text = '\n'.join(messages)+'\n'
    (EVIDENCE/'cp2-check.txt').write_text(text,encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
