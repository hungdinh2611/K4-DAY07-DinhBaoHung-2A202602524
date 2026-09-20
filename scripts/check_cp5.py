"""Validate CP5 artifacts and heading fallback without API calls."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bench import BASELINE_IDS, read_document
from src.heading_chunking import HeadingChunker


def main():
    output = ROOT / 'report/cp5'
    run = json.loads((output/'results.json').read_text(encoding='utf-8'))
    chunks = json.loads((output/'chunks.json').read_text(encoding='utf-8'))
    baseline = json.loads((output/'baseline.json').read_text(encoding='utf-8'))
    assert run['chunk_count'] == len(chunks) == len({c['id'] for c in chunks})
    assert run['queries_sha256'] == hashlib.sha256((ROOT/'report/benchmark_queries.json').read_bytes()).hexdigest()
    fingerprint = hashlib.sha256()
    sources = {}
    for path in sorted((ROOT/'data/ecommerce').glob('*.md')):
        sources[path.stem] = read_document(path)
        fingerprint.update(path.name.encode()+b'\0'+path.read_bytes())
    assert run['corpus_sha256'] == fingerprint.hexdigest()
    for c in chunks:
        meta = c['metadata']
        original, _ = sources[meta['doc_id']]
        assert all(meta[k] == v for k,v in original.items())
        assert c['id'] == f"{meta['doc_id']}#{meta['chunk_index']}"
        assert 0 < len(c['content']) <= run['parameters']['chunk_size']
        assert not c['content'].startswith('---') and 'retrieved_at:' not in c['content']
    assert set(baseline) == set(BASELINE_IDS)
    for strategies in baseline.values():
        assert set(strategies) == {'fixed_size','by_sentences','recursive'}
        for stats in strategies.values():
            assert stats['count'] == len(stats['chunks'])
            assert stats['avg_length'] == sum(map(len,stats['chunks']))/stats['count']
            assert all('retrieved_at:' not in c for c in stats['chunks'])
    assert len(run['results']) == 5
    for q in run['results']:
        assert len(q['filtered_top3']) == 3
        assert all(all(r['metadata'][k] == v for k,v in q['metadata_filter'].items()) for r in q['filtered_top3'])
        assert all(e['chunk_ids'] for e in q['evidence_locations'])
        assert [r['score'] for r in q['filtered_top3']] == sorted([r['score'] for r in q['filtered_top3']],reverse=True)
    chunker = HeadingChunker(chunk_size=100)
    assert chunker.chunk('') == [] and chunker.chunk('  \n') == []
    prefix = '# Policy\n## Refunds\n\n'
    payload = 'abcdefghij' * 40
    pieces = chunker.chunk('# Policy\n\n## Refunds\n\n' + payload)
    assert len(pieces) > 1 and all(p.startswith(prefix) and len(p)<=100 for p in pieces)
    assert ''.join(p[len(prefix):] for p in pieces) == payload
    assert chunker.chunk('# One\nbody\n# Two\nother') == ['# One\n\nbody','# Two\n\nother']
    assert '# fake' in chunker.chunk('# Real\n```text\n# fake\n```\nbody')[0]
    assert chunker.chunk('plain text') == ['plain text']
    try:
        HeadingChunker(5).chunk('# Long heading\nbody')
    except ValueError:
        pass
    else:
        raise AssertionError('Oversized heading must be reported, not silently truncated')
    text = '\n'.join([
        f'OK {len(sources)} files -> {len(chunks)} unique chunks; all metadata propagated',
        'OK file doc_id versus chunk id; body-only ingestion; size bound <= 800',
        'OK baseline: 3 source bodies, all 3 strategies, correct counts/averages',
        'OK 5 queries: 3 sorted filtered results each; gold evidence chunk locations exist',
        'OK source/query hashes match saved run',
        'OK heading fallback repeats full ancestor titles; keeps body; empty/plain/fenced text handled',
        'LIMITATION: MockEmbedder; no semantic quality or agent-answer evaluation',
        'PENDING: actual team member assignments remain unconfirmed',
    ])+'\n'
    (output/'check.txt').write_text(text,encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
