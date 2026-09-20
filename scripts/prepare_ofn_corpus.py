"""Build the reviewed OFN corpus from the collect_ofn.py temporary cache."""
import csv
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urljoin

from collect_ofn import BASE, CACHE, PAGES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/ecommerce'
EVIDENCE = ROOT / 'docs/collection-evidence'
LICENSE_URL = 'https://ofn-user-guide.gitbook.io/ofn-handbook/white-label-users'


def clean(raw):
    text = re.sub(r'^> For the complete documentation index,.*\n', '', raw)
    # Retain meaningful image captions; don't download screenshots or personal data.
    text = re.sub(r'!\[([^\]]*)\]\([^\n]*\)', lambda m: m[1], text)
    text = re.sub(r'<img\b[^>]*>', '', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</?(?:figure|figcaption)[^>]*>', '', text)
    text = re.sub(r'<a\b[^>]*></a>', '', text)
    # Tabs encode payment-method scope, so convert their titles to headings.
    text = re.sub(r'{% tab title="([^"]+)" %}', r'#### \1', text)
    text = re.sub(r'{% hint style="([^"]+)" %}', r'**\1:**', text)
    text = re.sub(r'{% (?:endhint|tabs|endtab|endtabs) %}', '', text)
    text = re.sub(r'\]\((/[^)]+)\)', lambda m: '](' + urljoin(BASE, m[1]) + ')', text)
    text = html.unescape(text).replace('\\\n', '\n')
    text = re.sub(r'^#{1,6}\s*$', '', text, flags=re.M)
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    return re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'


def selected_source(doc_id, raw):
    # Preserve complete question/answer sections, omitting account troubleshooting
    # unrelated to order rules. All exclusions are recorded in the evidence file.
    excluded = []
    if doc_id == 'ofn-buyer-faq':
        parts = re.split(r'(?=^### )', raw, flags=re.M)
        keep = [parts[0]]
        for part in parts[1:]:
            heading = part.splitlines()[0]
            if any(term in heading for term in ('password', "I didn't receive", 'difficulty paying')):
                excluded.append(heading)
            else:
                keep.append(part)
        raw = ''.join(keep)
    return raw, excluded


def write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    logs = json.loads((CACHE / 'fetch-log.json').read_text(encoding='utf-8'))
    index = (CACHE / 'index.txt').read_text(encoding='utf-8')
    records, inputs, audit = [], [], []
    for doc_id, path, audience, category in PAGES:
        if doc_id == 'ofn-buyer-shopping':
            continue  # Scouted, but less focused than the five selected sources.
        raw = (CACHE / (doc_id + '.txt')).read_text(encoding='utf-8')
        entry = next(x for x in logs if x['cache_name'] == doc_id + '.txt')
        assert BASE + path + '.md' in index, 'Source absent from publisher index'
        assert hashlib.sha256(raw.encode('utf-8')).hexdigest() == entry['sha256']
        selected, excluded = selected_source(doc_id, raw)
        body = clean(selected)
        assert '{%' not in body and '<img' not in body and 'token=' not in body
        title = re.search(r'^# (.+)$', body, re.M)[1]
        date = entry['started_at'][:10]
        metadata = dict(doc_id=doc_id, title=title, source_url=BASE+path,
                        retrieved_at=date, document_version='not-stated',
                        audience=audience, category=category, language='en',
                        license_or_permission='CC-BY-SA-4.0',
                        attribution='Open Food Network contributors',
                        license_url='https://creativecommons.org/licenses/by-sa/4.0/',
                        permission_source=LICENSE_URL,
                        source_format='official-markdown',
                        extraction_scope='Selected complete FAQ sections' if excluded else 'Full article text; image assets omitted',
                        changes='Removed documentation navigation and image assets; retained captions and warnings; converted tabs to headings; resolved links')
        front = '\n'.join(k + ': ' + json.dumps(v, ensure_ascii=False) for k, v in metadata.items())
        (OUT / (doc_id+'.md')).write_text('---\n'+front+'\n---\n\n'+body, encoding='utf-8')
        records.append({k: metadata[k] for k in ('doc_id','title','source_url','retrieved_at','document_version','license_or_permission')} | {'file_path': 'data/ecommerce/'+doc_id+'.md'})
        inputs.append({'url': BASE+path, **{k: metadata[k] for k in ('doc_id','title','audience','category','language','document_version','license_or_permission')}})
        audit.append(dict(doc_id=doc_id, title=title, source_url=BASE+path, fetch_url=entry['url'], raw_sha256=entry['sha256'], body_sha256=hashlib.sha256(body.encode()).hexdigest(), body_characters=len(body), audience=audience, category=category, excluded_sections=excluded, headings=re.findall(r'^#{1,6} .+$',body,re.M)))
    # Preserve original candidates and templates, outside the live corpus.
    archive = EVIDENCE / 'shopee-urls-rejected.csv'
    if not archive.exists():
        shutil.copyfile(ROOT/'data/urls.csv', archive)
    for name in ('return-refund-policy.md', 'seller-warranty-policy.md'):
        source = OUT / name
        target = ROOT / 'docs/examples/ecommerce' / name
        if source.exists():
            assert source.resolve().is_relative_to(ROOT) and target.resolve().is_relative_to(ROOT)
            assert 'example.com' in source.read_text(encoding='utf-8'), 'Refuse to move real user data'
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise FileExistsError(target)
            source.rename(target)
    write_csv(OUT/'sources.csv', records, ['doc_id','file_path','title','source_url','retrieved_at','document_version','license_or_permission'])
    write_csv(ROOT/'data/urls.csv', inputs, ['url','doc_id','title','audience','category','language','document_version','license_or_permission'])
    (EVIDENCE/'fetch-log.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (EVIDENCE/'content-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    shutil.copyfile(CACHE/'robots-guide.openfoodnetwork.org.txt', EVIDENCE/'ofn-robots.txt')
    # Store just the complete licence subsection, with source attribution.
    license_text = (CACHE/'license.txt').read_text(encoding='utf-8')
    license_section = license_text.split('### The OFN knowledge resources',1)[1].split('\n## ',1)[0]
    (EVIDENCE/'permission.md').write_text('# OFN knowledge resources: reuse terms\n\nSource: '+LICENSE_URL+'\n\nRetrieved: '+logs[1]['started_at'][:10]+'\n\nAttribution: Open Food Network contributors. CC BY-SA 4.0.\n\nExcerpt: complete knowledge-resources licensing subsection; surrounding software/service sections omitted.\n\n### The OFN knowledge resources'+license_section+'\n',encoding='utf-8')
    print(json.dumps([{'doc_id':x['doc_id'],'characters':x['body_characters'],'audience':x['audience']} for x in audit],ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
