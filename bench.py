"""CP5 reproducible smoke benchmark. No API calls or semantic quality claims.

Run: python bench.py
Change only CHUNKER to compare a personal strategy on identical inputs.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.chunking import ChunkingStrategyComparator, FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import MockEmbedder
from src.heading_chunking import HeadingChunker
from src.models import Document
from src.store import EmbeddingStore

ROOT = Path(__file__).resolve().parent
CHUNKER = HeadingChunker(chunk_size=800)  # Personal strategy: change only this line.
BASELINE_IDS = ('ofn-buyer-faq', 'ofn-seller-refunds', 'ofn-seller-subscriptions')


def read_document(path: Path) -> tuple[dict, str]:
    """Read this corpus's flat frontmatter (JSON-quoted strings or plain scalars)."""
    text = path.read_text(encoding='utf-8')
    match = re.fullmatch(r'---\n(.*?)\n---\n(.*)', text, re.S)
    if not match:
        raise ValueError(f'Missing frontmatter: {path}')
    metadata = {}
    for line in match[1].splitlines():
        key, separator, value = line.partition(':')
        if not separator or key in metadata:
            raise ValueError(f'Invalid or duplicate metadata: {path}: {line}')
        value = value.strip()
        metadata[key] = json.loads(value) if value.startswith('"') else value
    required = ('doc_id', 'title', 'source_url', 'retrieved_at', 'document_version', 'audience', 'category', 'language')
    if not all(metadata.get(k) for k in required) or metadata['doc_id'] != path.stem:
        raise ValueError(f'Invalid corpus metadata: {path}')
    return metadata, match[2].lstrip('\n')


def main() -> int:
    output = ROOT / 'report/cp5'
    output.mkdir(parents=True, exist_ok=True)
    documents = {}
    chunk_documents = []
    corpus_fingerprint = hashlib.sha256()
    for path in sorted((ROOT / 'data/ecommerce').glob('*.md')):
        metadata, body = read_document(path)
        documents[path.stem] = (metadata, body)
        corpus_fingerprint.update(path.name.encode() + b'\0' + path.read_bytes())
        for i, chunk in enumerate(CHUNKER.chunk(body)):
            chunk_documents.append(Document(
                id=f'{path.stem}#{i}', content=chunk,
                metadata={**metadata, 'doc_id': path.stem,
                          'source': path.relative_to(ROOT).as_posix(), 'chunk_index': i},
            ))
    if not 5 <= len(documents) <= 10 or not chunk_documents:
        raise ValueError('Expected 5-10 source documents and nonempty chunks')

    queries_path = ROOT / 'report/benchmark_queries.json'
    queries = json.loads(queries_path.read_text(encoding='utf-8'))
    if len(queries) != 5 or len({q['id'] for q in queries}) != 5:
        raise ValueError('Exactly five unique benchmark queries are required')
    for q in queries:
        for evidence in q['evidence']:
            if evidence['quote'] not in documents[evidence['doc_id']][1]:
                raise ValueError(f"Unverified gold evidence: {q['id']}")

    baseline = {}
    for doc_id in BASELINE_IDS:
        baseline[doc_id] = ChunkingStrategyComparator().compare(documents[doc_id][1], chunk_size=500)

    # Deliberately explicit: CP5 tests execution; real semantic embeddings belong
    # to CP6. Do not silently fall back from a paid/real provider to a mock.
    store = EmbeddingStore(collection_name='cp5', embedding_fn=MockEmbedder())
    store.add_documents(chunk_documents)
    lines = [f'Strategy: {type(CHUNKER).__name__} {vars(CHUNKER)}',
             'Embedding backend: MockEmbedder (64D); execution check only, NOT semantic quality.',
             f'Loaded {len(documents)} files -> {store.get_collection_size()} chunks',
             f'Chunks by audience: {dict(Counter(d.metadata["audience"] for d in chunk_documents))}']
    results = []
    for q in queries:
        filtered = store.search_with_filter(q['query'], top_k=3, metadata_filter=q['metadata_filter'])
        unfiltered = store.search(q['query'], top_k=3)
        evidence_chunks = []
        for evidence in q['evidence']:
            # Exact evidence locations are separate from retrieval hits, never
            # promoted into top-k or presented as successful retrieval.
            matches = [d.id for d in chunk_documents if d.metadata['doc_id'] == evidence['doc_id']
                       and evidence['quote'] in d.content]
            evidence_chunks.append({**evidence, 'chunk_ids': matches})
        results.append({**q, 'filtered_top3': filtered, 'unfiltered_top3': unfiltered,
                        'evidence_locations': evidence_chunks})
        lines += ['', f"{q['id']}: {q['query']}", f"Filter: {q['metadata_filter']}",
                  f"Gold: {q['gold_answer']}"]
        for rank, result in enumerate(filtered, 1):
            lines += [f"  {rank}. score={result['score']:.6f} doc_id={result['metadata']['doc_id']} chunk_id={result['id']}",
                      f"     source={result['metadata']['source_url']}",
                      '     ' + result['content'][:240].replace('\n', ' ')]
        lines.append('Unfiltered top-3 (diagnostic only): ' + ', '.join(
            f"{r['id']} [{r['metadata']['audience']}]" for r in unfiltered))
    run = dict(checkpoint='CP5', run_at=datetime.now(timezone.utc).isoformat(),
               strategy=type(CHUNKER).__name__, parameters=vars(CHUNKER),
               embedding_backend='MockEmbedder', embedding_dim=64, semantic_evaluation=False,
               corpus_sha256=corpus_fingerprint.hexdigest(),
               queries_sha256=hashlib.sha256(queries_path.read_bytes()).hexdigest(),
               document_count=len(documents), chunk_count=len(chunk_documents), results=results)
    for name, value in [('baseline.json', baseline), ('results.json', run),
                        ('chunks.json', [vars(d) for d in chunk_documents])]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    text = '\n'.join(lines)+'\n'
    (output / 'run.txt').write_text(text, encoding='utf-8')
    print(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
