"""Render the CP6 benchmark results as one self-contained offline HTML page.

Reads report/cp6/results.json, report/benchmark_queries.json and
report/cp6_checks.json; writes report/cp6/index.html. Stdlib only - no network,
no server, no extra dependency. Open the output with a browser (file://).

Run: python scripts/build_report_html.py
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'report/cp6/index.html'
STRATEGY_ORDER = ('fixed_size', 'recursive', 'heading')
SCORE_FIELDS = (
    ('naive_doc_score', 'document'),
    ('content_score', 'content'),
    ('provisional_extractive_score', 'extractive'),
)
QUOTE_TRANSLATION = {'’': "'", '‘': "'", '“': '"', '”': '"',
                     '–': '-', '—': '-'}


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Mirror bench_cp6.normalized() while tracking each output char's origin.

    The markdown-link rewrite is deliberately skipped: this mapping only places
    <mark> spans, and the authoritative hit/miss verdict stays the ranks that
    bench_cp6 computed.
    """
    chars: list[str] = []
    offsets: list[int] = []
    pending_space = False
    for index, char in enumerate(text):
        if char in '*#`':
            continue
        if char.isspace():
            pending_space = bool(chars)
            continue
        if pending_space:
            chars.append(' ')
            offsets.append(index)
            pending_space = False
        lowered = QUOTE_TRANSLATION.get(char, char).lower()
        chars.append(lowered[:1] or char)
        offsets.append(index)
    return ''.join(chars), offsets


def highlight(content: str, needles: list[str]) -> str:
    """Escape content, wrapping every gold quote that occurs in it with <mark>."""
    normalized, offsets = normalize_with_map(content)
    spans: list[tuple[int, int]] = []
    for needle in needles:
        target, _ = normalize_with_map(needle)
        position = normalized.find(target) if target else -1
        if position != -1:
            spans.append((offsets[position], offsets[position + len(target) - 1] + 1))

    merged: list[list[int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    pieces: list[str] = []
    cursor = 0
    for start, end in merged:
        pieces.append(html.escape(content[cursor:start]))
        pieces.append('<mark>' + html.escape(content[start:end]) + '</mark>')
        cursor = end
    pieces.append(html.escape(content[cursor:]))
    return ''.join(pieces)


def badge(text: str, kind: str) -> str:
    return f'<span class="badge {kind}">{html.escape(text)}</span>'


def pill(label: str, value: int) -> str:
    kind = 'ok' if value == 2 else 'warn' if value else 'bad'
    return f'<span class="pill {kind}">{html.escape(label)} {value}/2</span>'


def totals_for(strategy: dict) -> dict[str, int]:
    return {field: sum(query['filtered'][field] for query in strategy['queries'].values())
            for field, _ in SCORE_FIELDS}


def render_summary(results: dict) -> str:
    best = max(STRATEGY_ORDER, key=lambda name: totals_for(results[name])['content_score'])
    rows = []
    for name in STRATEGY_ORDER:
        strategy = results[name]
        totals = totals_for(strategy)
        parameters = ', '.join(f'{key}={value}' for key, value in strategy['parameters'].items())
        cells = ''.join(f'<td class="num">{totals[field]}<span class="muted">/10</span></td>'
                        for field, _ in SCORE_FIELDS)
        rows.append(
            f'<tr class="{"winner" if name == best else ""}">'
            f'<td><strong>{html.escape(name)}</strong>'
            f'<div class="muted">{html.escape(parameters)}</div></td>'
            f'<td class="num">{strategy["count"]}</td>'
            f'<td class="num">{strategy["avg_length"]:.0f}</td>{cells}</tr>')
    return ('<table class="summary"><thead><tr>'
            '<th>Chi&#7871;n l&#432;&#7907;c</th><th class="num">Chunks</th>'
            '<th class="num">&#272;&#7897; d&#224;i TB</th>'
            '<th class="num">Document</th><th class="num">Content</th>'
            '<th class="num">Extractive</th></tr></thead><tbody>'
            + ''.join(rows) + '</tbody></table>')


def render_hit(hit: dict, rank: int, expected_audience: str | None, needles: list[str]) -> str:
    audience = hit['metadata'].get('audience', '?')
    wrong = expected_audience is not None and audience != expected_audience
    width = max(0.0, min(1.0, hit['score'])) * 100
    return (f'<article class="hit{" wrong" if wrong else ""}">'
            f'<header><span class="rank">{rank}</span><code>{html.escape(hit["id"])}</code>'
            f'{badge(audience, "bad" if wrong else "neutral")}'
            f'<span class="score">{hit["score"]:.4f}</span></header>'
            f'<div class="bar"><span style="width:{width:.1f}%"></span></div>'
            f'<pre>{highlight(hit["content"], needles)}</pre></article>')


def render_column(name: str, evaluation: dict, expected_audience: str | None,
                  needles: list[str]) -> str:
    scores = ''.join(pill(label, evaluation[field]) for field, label in SCORE_FIELDS)
    clauses = ''.join(
        badge(('✓ ' if group['ranks'] else '✗ ') + group['label']
              + (f' @top{group["ranks"][0]}' if group['ranks'] else ''),
              'ok' if group['ranks'] else 'bad')
        for group in evaluation['required_groups'])
    wrong = evaluation['wrong_audience']
    alert = (f'<p class="alert">Sai &#273;&#7889;i t&#432;&#7907;ng: '
             f'<code>{html.escape(", ".join(wrong))}</code></p>' if wrong else '')
    hits = ''.join(render_hit(hit, rank, expected_audience, needles)
                   for rank, hit in enumerate(evaluation['top3'], start=1))
    return (f'<section class="col"><h4>{html.escape(name)}</h4>'
            f'<div class="scoreline">{scores}</div>'
            f'<div class="clauses">{clauses}</div>{alert}{hits}</section>')


def render_query(query: dict, groups: list[dict], results: dict) -> str:
    query_id = query['id']
    needles = [quote for group in groups for quote in group['any']]
    expected = query['metadata_filter'].get('audience')
    modes_present = [mode for mode in ('filtered', 'unfiltered')
                     if mode in results[STRATEGY_ORDER[0]]['queries'][query_id]]

    blocks = []
    for mode in modes_present:
        audience = expected if mode == 'filtered' else None
        columns = ''.join(
            render_column(name, results[name]['queries'][query_id][mode], audience, needles)
            for name in STRATEGY_ORDER)
        hidden = ' hidden' if mode == 'unfiltered' else ''
        blocks.append(f'<div class="grid" data-mode="{mode}"{hidden}>{columns}</div>')

    toggle = ''
    if 'unfiltered' in modes_present:
        toggle = ('<label class="toggle"><input type="checkbox" checked> '
                  f'metadata_filter <code>audience={html.escape(expected)}</code></label>'
                  f'<p class="why">{html.escape(query.get("filter_reason", ""))}</p>')

    return (f'<div class="query" data-query="{query_id}" hidden>'
            f'<h3>{query_id} <span class="q">{html.escape(query["query"])}</span></h3>'
            f'<div class="meta">{badge("audience: " + expected, "neutral")}'
            f'{badge(str(len(groups)) + " gold clause", "neutral")}</div>{toggle}'
            '<details><summary>Câu trả lời chuẩn (gold answer)</summary>'
            f'<p>{html.escape(query["gold_answer"])}</p></details>'
            + ''.join(blocks) + '</div>')


STYLE = """
:root{color-scheme:light dark;--bg:#f5f6f8;--card:#fff;--line:#d7dbe0;--ink:#16191d;
--muted:#6b7480;--ok:#12703f;--okbg:#e6f4ec;--bad:#b42318;--badbg:#fdeceb;
--warn:#8a5a00;--warnbg:#fdf3e0;--accent:#1d4ed8;--mark:#fff1a8}
@media(prefers-color-scheme:dark){:root{--bg:#14171b;--card:#1c2027;--line:#333a44;
--ink:#e8eaed;--muted:#98a1ad;--okbg:#10301f;--ok:#5fd394;--badbg:#3a1614;--bad:#f28b82;
--warnbg:#33260c;--warn:#f5c469;--accent:#8ab4f8;--mark:#5c4a00}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,Segoe UI,sans-serif}
.wrap{max-width:1500px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:22px;margin:0 0 4px}
h3{font-size:17px;margin:24px 0 8px;font-weight:600}
h4{font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.q{font-weight:400;color:var(--muted)}
.runinfo{color:var(--muted);font-size:12px;margin:0 0 16px}
.runinfo code{font-size:11px}
.note{background:var(--warnbg);color:var(--warn);border:1px solid currentColor;
border-radius:8px;padding:10px 12px;margin:0 0 20px;font-size:12.5px}
table.summary{width:100%;border-collapse:collapse;background:var(--card);
border:1px solid var(--line);border-radius:10px;overflow:hidden;margin:0 0 8px}
.summary th,.summary td{padding:9px 12px;border-bottom:1px solid var(--line);text-align:left}
.summary tbody tr:last-child td{border-bottom:0}
.summary th{font-size:12px;color:var(--muted);font-weight:600;background:var(--bg)}
.num{text-align:right;font-variant-numeric:tabular-nums}
.winner td{background:var(--okbg)}
.muted{color:var(--muted);font-size:11.5px;font-weight:400}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:24px 0 0}
.tabs button{font:inherit;padding:7px 16px;border:1px solid var(--line);background:var(--card);
color:var(--ink);border-radius:999px;cursor:pointer}
.tabs button[aria-selected=true]{background:var(--accent);border-color:var(--accent);color:#fff}
.meta{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 10px}
.toggle{display:inline-flex;align-items:center;gap:8px;background:var(--card);
border:1px solid var(--line);border-radius:8px;padding:8px 12px;cursor:pointer}
.why{color:var(--muted);font-size:12px;margin:6px 0 0;max-width:80ch}
details{margin:12px 0;background:var(--card);border:1px solid var(--line);
border-radius:8px;padding:10px 12px}
details summary{cursor:pointer;font-size:12.5px;color:var(--muted)}
details p{margin:8px 0 0;max-width:90ch}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:14px}
@media(max-width:1000px){.grid{grid-template-columns:1fr}}
.col{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;min-width:0}
.scoreline,.clauses{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:8px}
.pill,.badge{font-size:11px;padding:2px 8px;border-radius:999px;border:1px solid transparent;
white-space:nowrap}
.pill.ok,.badge.ok{background:var(--okbg);color:var(--ok);border-color:currentColor}
.pill.bad,.badge.bad{background:var(--badbg);color:var(--bad);border-color:currentColor}
.pill.warn{background:var(--warnbg);color:var(--warn);border-color:currentColor}
.badge.neutral{background:var(--bg);color:var(--muted);border-color:var(--line)}
.alert{background:var(--badbg);color:var(--bad);border-radius:6px;padding:6px 8px;
margin:0 0 8px;font-size:12px}
.hit{border:1px solid var(--line);border-radius:8px;padding:8px;margin-bottom:8px;min-width:0}
.hit.wrong{border-color:var(--bad)}
.hit header{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px}
.rank{background:var(--ink);color:var(--bg);width:18px;height:18px;border-radius:50%;
display:grid;place-items:center;font-size:11px;flex:none}
.hit code{font-size:11px;color:var(--muted);overflow-wrap:anywhere}
.score{margin-left:auto;font-variant-numeric:tabular-nums;font-size:12px;font-weight:600}
.bar{height:4px;background:var(--bg);border-radius:2px;overflow:hidden;margin-bottom:8px}
.bar span{display:block;height:100%;background:var(--accent)}
.hit pre{margin:0;max-height:220px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;
font:11.5px/1.5 ui-monospace,Consolas,monospace;color:var(--muted)}
mark{background:var(--mark);color:var(--ink);border-radius:2px}
"""

SCRIPT = """
const queries=[...document.querySelectorAll('.query')];
const tabs=[...document.querySelectorAll('.tabs button')];
function show(id){
  queries.forEach(q=>q.hidden=q.dataset.query!==id);
  tabs.forEach(t=>t.setAttribute('aria-selected',String(t.dataset.query===id)));
}
tabs.forEach(t=>t.addEventListener('click',()=>show(t.dataset.query)));
queries.forEach(q=>{
  const box=q.querySelector('.toggle input');
  if(!box)return;
  const sync=()=>q.querySelectorAll('.grid').forEach(g=>{
    g.hidden=g.dataset.mode!==(box.checked?'filtered':'unfiltered');
  });
  box.addEventListener('change',sync);
  sync();
});
show(tabs[0].dataset.query);
"""


def main() -> int:
    run = json.loads((ROOT / 'report/cp6/results.json').read_text(encoding='utf-8'))
    queries = json.loads((ROOT / 'report/benchmark_queries.json').read_text(encoding='utf-8'))
    checks = json.loads((ROOT / 'report/cp6_checks.json').read_text(encoding='utf-8'))['queries']
    results = run['results']

    tabs = ''.join(f'<button data-query="{query["id"]}" aria-selected="false">{query["id"]}</button>'
                   for query in queries)
    bodies = ''.join(render_query(query, checks[query['id']], results) for query in queries)
    packages = ', '.join(f'{name} {version}' for name, version in run.get('packages', {}).items())

    page = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CP6 · So sánh chiến lược chunking</title>
<style>{STYLE}</style></head><body><div class="wrap">
<h1>CP6 — So sánh chiến lược chunking trên 5 câu hỏi đánh giá</h1>
<p class="runinfo">backend <strong>{html.escape(run['backend'])}</strong> ·
model <code>{html.escape(run['model'])}</code> ·
revision <code>{html.escape(str(run['revision'])[:12])}</code> ·
max_seq_length {run['max_seq_length']} · chạy lúc {html.escape(run['run_at'])}
{(' · ' + html.escape(packages)) if packages else ''}</p>
<p class="note"><strong>Điểm ở đây là điểm chẩn đoán, không phải điểm chấm cuối.</strong>
Câu trả lời của agent sinh bằng {html.escape(run['answer_backend'])}.</p>
{render_summary(results)}
<p class="runinfo">Document = tài liệu đúng có trong top-3. Content = mọi gold clause đều
nằm trong top-3. Extractive = context đủ, trích dẫn đủ và không lẫn chunk sai đối tượng.</p>
<div class="tabs">{tabs}</div>
{bodies}
</div><script>{SCRIPT}</script></body></html>
"""
    OUTPUT.write_text(page, encoding='utf-8')
    print(f'Wrote {OUTPUT.relative_to(ROOT).as_posix()} ({len(page) / 1024:.0f} KB)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
