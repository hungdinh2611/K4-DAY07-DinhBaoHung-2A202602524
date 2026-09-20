"""CP6: fixed, recursive, heading comparison with real local embeddings.

python bench_cp6.py --backend local (default; fail loudly if unavailable)
python bench_cp6.py --backend mock  (explicit non-semantic fallback)
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from bench import ROOT, read_document
from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker
from src.embeddings import LOCAL_EMBEDDING_MODEL, MockEmbedder
from src.heading_chunking import HeadingChunker
from src.models import Document
from src.store import EmbeddingStore


def plain(text):
    text = re.sub(r'\[([^\]]+)\]\([^\s)]+\)', r'\1', text)
    return re.sub(r'[*#`]', '', text)


def normalized(text):
    return ' '.join(plain(text).translate(str.maketrans({'’':"'",'‘':"'",'“':'"','”':'"','–':'-','—':'-'})).lower().split())


class CachedEmbedder:
    def __init__(self, backend):
        self.backend = backend
        self.model_name = LOCAL_EMBEDDING_MODEL if backend == 'local' else 'mock-64'
        self.model = None
        self.cache_path = ROOT/'.cache/cp6-vectors.json'
        self.cache_path.parent.mkdir(exist_ok=True)
        self.data = json.loads(self.cache_path.read_text(encoding='utf-8')) if self.cache_path.exists() else {}
        if backend == 'local':
            os.environ['HF_HOME'] = str(ROOT/'.cache/huggingface')
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name, cache_folder=str(ROOT/'.cache/models'), device='cpu')
            self.model.max_seq_length = min(256, self.model[0].auto_model.config.max_position_embeddings)
            self.revision = getattr(self.model[0].auto_model.config, '_commit_hash', None)
        else:
            self.model = MockEmbedder()
            self.revision = None
        self.namespace = json.dumps([self.backend,self.model_name,self.revision,'plain-v1',256 if backend=='local' else None])

    def key(self, text):
        return hashlib.sha256((self.namespace+'\0'+plain(text)).encode()).hexdigest()

    def preload(self, texts):
        missing = {self.key(t):plain(t) for t in texts if self.key(t) not in self.data}
        if missing:
            print(f'Embedding {len(missing)} new texts ({self.backend})',flush=True)
            values = (self.model.encode(list(missing.values()),batch_size=16,normalize_embeddings=True,show_progress_bar=True).tolist()
                      if self.backend=='local' else [self.model(t) for t in missing.values()])
            self.data.update(zip(missing,values))
            self.cache_path.write_text(json.dumps(self.data),encoding='utf-8')

    def __call__(self,text):
        self.preload([text])
        return self.data[self.key(text)]


def coverage(results, groups):
    matched = []
    for group in groups:
        ranks = [i for i,r in enumerate(results,1)
                 if r['metadata']['doc_id']==group['doc_id']
                 and any(normalized(v) in normalized(r['content']) for v in group['any'])]
        matched.append(dict(label=group['label'],ranks=ranks))
    return matched


class FilteredStore:
    def __init__(self,store,filters):
        self.store,self.filters = store,filters

    def search(self,query,top_k=3):
        return self.store.search_with_filter(query,top_k,self.filters)


class ExtractiveAnswer:
    """Non-generative llm_fn: rank paragraphs in supplied context, quote top six.

    Sees only the agent prompt; never receives gold answers/check strings.
    Returned quotations are auditable, but not an evaluation of a generative LLM.
    """
    def __init__(self,embedder):
        self.embedder=embedder

    def __call__(self,prompt):
        question, context = prompt.split('Câu hỏi: ',1)[1].split('\n\nNgữ cảnh:\n',1)
        candidates=[]
        for section in re.split(r'(?=^\[\d+\] source:)',context,flags=re.M):
            match=re.match(r'\[(\d+)\] source: (.*?)\ndoc_id: (.*?) \| chunk_id: (.*?)\n(.*)',section,re.S)
            if not match:
                continue
            for paragraph in re.split(r'\n\s*\n',match[5]):
                lines=[line for line in paragraph.splitlines() if not line.startswith('#')]
                text='\n'.join(lines).strip()
                if len(plain(text))>35:
                    candidates.append((match[1],text))
        if not candidates:
            return 'Không tìm thấy thông tin đủ để trả lời trong ngữ cảnh.'
        self.embedder.preload([question]+[p for _,p in candidates])
        q=self.embedder(question)
        ranked=sorted(candidates,key=lambda p:sum(a*b for a,b in zip(q,self.embedder(p[1]))),reverse=True)
        return 'Các đoạn nguồn liên quan (trích xuất, chưa tổng hợp bằng LLM):\n'+'\n\n'.join(f'[{n}] {p}' for n,p in ranked[:6])


def evaluate(store,question,groups,filters,embedder):
    hits=store.search_with_filter(question['query'],top_k=3,metadata_filter=filters)
    gold_docs={e['doc_id'] for e in question['evidence']}
    doc_rank=next((i for i,h in enumerate(hits,1) if h['metadata']['doc_id'] in gold_docs),None)
    checks=coverage(hits,groups)
    all_covered=all(c['ranks'] for c in checks)
    content_rank=min((r for c in checks for r in c['ranks']),default=None)
    answer=KnowledgeBaseAgent(FilteredStore(store,filters),ExtractiveAnswer(embedder)).answer(question['query'],top_k=3)
    answer_checks=[any(normalized(v) in normalized(answer) for v in group['any']) for group in groups]
    wrong_audience=[h['id'] for h in hits if h['metadata']['audience']!=question['metadata_filter']['audience']]
    # Exact-match coverage is necessary but not a complete correctness judgement.
    return dict(top3=hits,doc_rank=doc_rank,naive_doc_score=2 if doc_rank==1 else 1 if doc_rank else 0,
                required_groups=checks,context_complete=all_covered,
                content_score=(2 if content_rank==1 else 1) if all_covered else 0,
                answer=answer,answer_group_coverage=answer_checks,
                answer_complete_by_markers=all(answer_checks),wrong_audience=wrong_audience,
                provisional_extractive_score=((2 if content_rank==1 else 1) if all_covered and all(answer_checks) and not wrong_audience else 0),
                generative_llm_evaluated=False)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--backend',choices=['local','mock'],default='local')
    args=parser.parse_args()
    output=ROOT/'report/cp6'
    output.mkdir(exist_ok=True)
    queries_path=ROOT/'report/benchmark_queries.json'
    checks_path=ROOT/'report/cp6_checks.json'
    queries=json.loads(queries_path.read_text(encoding='utf-8'))
    spec=json.loads(checks_path.read_text(encoding='utf-8'))['queries']
    assert len(queries)==5 and set(spec)=={q['id'] for q in queries}
    sources={p.stem:read_document(p) for p in sorted((ROOT/'data/ecommerce').glob('*.md'))}
    for groups in spec.values():
        for g in groups:
            assert any(normalized(v) in normalized(sources[g['doc_id']][1]) for v in g['any']),g
    strategies={'fixed_size':FixedSizeChunker(800,80),'recursive':RecursiveChunker(chunk_size=800),'heading':HeadingChunker(800)}
    chunks={name:[Document(f'{doc_id}#{i}',piece,{**meta,'doc_id':doc_id,'source':f'data/ecommerce/{doc_id}.md','chunk_index':i})
                  for doc_id,(meta,body) in sources.items() for i,piece in enumerate(chunker.chunk(body))]
            for name,chunker in strategies.items()}
    embedder=CachedEmbedder(args.backend)
    embedder.preload([d.content for ds in chunks.values() for d in ds]+[q['query'] for q in queries])
    results={}
    for name,ds in chunks.items():
        print('Running strategy:',name,flush=True)
        store=EmbeddingStore(embedding_fn=embedder)
        store.add_documents(ds)
        results[name]=dict(count=len(ds),avg_length=sum(len(d.content) for d in ds)/len(ds),parameters=vars(strategies[name]),queries={})
        if args.backend=='local':
            lengths=[len(embedder.model.tokenizer.encode(plain(d.content),truncation=False)) for d in ds]
            results[name]['inputs_over_model_limit']=sum(n>embedder.model.max_seq_length for n in lengths)
        for q in queries:
            results[name]['queries'][q['id']]={'filtered':evaluate(store,q,spec[q['id']],q['metadata_filter'],embedder)}
            if q['id']=='Q1':
                results[name]['queries'][q['id']]['unfiltered']=evaluate(store,q,spec[q['id']],None,embedder)
        (output/f'chunks-{name}.json').write_text(json.dumps([vars(d) for d in ds],ensure_ascii=False,indent=2),encoding='utf-8')
    run=dict(run_at=datetime.now(timezone.utc).isoformat(),backend=args.backend,model=embedder.model_name,revision=embedder.revision,
             max_seq_length=embedder.model.max_seq_length if args.backend=='local' else None,
             queries_sha256=hashlib.sha256(queries_path.read_bytes()).hexdigest(),checks_sha256=hashlib.sha256(checks_path.read_bytes()).hexdigest(),
             corpus_sha256={d:hashlib.sha256((ROOT/f'data/ecommerce/{d}.md').read_bytes()).hexdigest() for d in sources},
             answer_backend='extractive paragraph ranking; NOT a generative LLM; no gold in prompt',results=results)
    if args.backend=='local':
        run['packages']={p:importlib.metadata.version(p) for p in ['sentence-transformers','torch','transformers']}
    (output/'results.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=[f'CP6 backend={args.backend}; model={embedder.model_name}; revision={embedder.revision}',
           'Agent backend: extractive paragraph quotations, not generative LLM. Scores are diagnostic, not final awarded marks.']
    for name,result in results.items():
        totals={k:sum(q['filtered'][k] for q in result['queries'].values()) for k in ['naive_doc_score','content_score','provisional_extractive_score']}
        lines += ['',f'{name}: count={result["count"]}, avg_length={result["avg_length"]:.2f}, totals={totals}']
        for qid,modes in result['queries'].items():
            for mode,r in modes.items():
                lines += [f'{qid} {mode}: document={r["naive_doc_score"]}/2 content={r["content_score"]}/2 extractive={r["provisional_extractive_score"]}/2',
                          'Missing clauses: '+', '.join(c['label'] for c in r['required_groups'] if not c['ranks'])]
                lines += [f'  {i}. {h["id"]} score={h["score"]:.6f} audience={h["metadata"]["audience"]}\n     {h["content"]}' for i,h in enumerate(r['top3'],1)]
                lines += ['Agent quotations:',r['answer']]
    text='\n'.join(lines)+'\n'
    (ROOT/'ket_qua_benchmark.txt').write_text(text,encoding='utf-8')
    print('\n'.join(line for line in lines if line.startswith(('CP6','fixed_size:','recursive:','heading:','Q1 '))))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
