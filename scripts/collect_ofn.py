"""Fetch a bounded selection of official, openly licensed OFN documentation.

Raw responses stay in the OS temporary directory, never in the corpus.
Every request is sequential and starts at least 1.1 s after the previous ends.
"""
import hashlib
import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

AGENT = 'Day7DataFoundationsCourse/1.0 (+educational-lab)'
BASE = 'https://guide.openfoodnetwork.org/'
PAGES = [
    ('ofn-buyer-shopping', 'shopping-with-open-food-network/shopping-and-placing-an-order', 'buyer', 'order-policy'),
    ('ofn-buyer-faq', 'shopping-with-open-food-network/frequently-asked-questions', 'buyer', 'order-changes'),
    ('ofn-buyer-subscriptions', 'shopping-with-open-food-network/regular-automated-orders', 'buyer', 'subscriptions'),
    ('ofn-seller-refunds', 'basic-features/orders/refunds-and-adjusting-payments', 'seller', 'refunds-policy'),
    ('ofn-seller-orders', 'basic-features/orders/view-orders', 'seller', 'order-changes'),
    ('ofn-seller-subscriptions', 'basic-features/subscriptions/subscriptions-creating-and-managing-orders', 'seller', 'subscriptions'),
]
CACHE = Path(tempfile.gettempdir()) / 'k4-ofn-collection'
CACHE.mkdir(exist_ok=True)
LOG = []
ROBOTS = {}
last_end = 0.0


def fetch(url, key, check=True):
    global last_end
    origin = '{0.scheme}://{0.netloc}'.format(urlsplit(url))
    if check:
        if origin not in ROBOTS:
            body = fetch(origin + '/robots.txt', 'robots-' + urlsplit(url).netloc, False)
            parser = RobotFileParser()
            parser.parse(body.splitlines())
            ROBOTS[origin] = parser
        if not ROBOTS[origin].can_fetch(AGENT, url):
            raise RuntimeError('Disallowed by robots: ' + url)
    time.sleep(max(0, 1.1 - (time.monotonic() - last_end)))
    started = datetime.now(timezone.utc).isoformat()
    with urlopen(Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/markdown,text/plain,text/html;q=0.9'}), timeout=35) as r:
        raw = r.read()
        final = r.geturl()
        known_robots_redirect = (not check and final == BASE + 'robots.txt' and url == 'https://ofn-user-guide.gitbook.io/robots.txt')
        if urlsplit(final).netloc != urlsplit(url).netloc and not known_robots_redirect:
            raise RuntimeError('Unexpected cross-domain redirect: ' + final)
        body = raw.decode(r.headers.get_content_charset() or 'utf-8')
        LOG.append(dict(url=url, final_url=final, status=r.status, content_type=r.headers.get_content_type(), started_at=started, finished_at=datetime.now(timezone.utc).isoformat(), sha256=hashlib.sha256(raw).hexdigest(), cache_name=key+'.txt'))
    last_end = time.monotonic()
    (CACHE / (key+'.txt')).write_text(body, encoding='utf-8', newline='')
    print(key, len(body), final, flush=True)
    return body


if __name__ == '__main__':
    # The publisher's reuse statement, not the software's AGPL licence.
    fetch('https://ofn-user-guide.gitbook.io/ofn-handbook/white-label-users.md', 'license')
    fetch(BASE + 'llms.txt', 'index')
    for doc_id, path, _, _ in PAGES:
        fetch(BASE + path + '.md', doc_id)
    (CACHE / 'fetch-log.json').write_text(json.dumps(LOG, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Cache:', CACHE)
