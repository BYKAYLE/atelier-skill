"""Same-origin link crawler.

BFS through a page's anchor tags, respecting same-origin, skipping
mailto/tel/javascript, and enforcing a max_pages budget. Returns a list of
URLs in discovery order. Uses a live Playwright page as the extraction
engine so JS-rendered nav links are seen.
"""
from __future__ import annotations

from collections import deque
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse


_EXTRACT_JS = r"""
() => {
  const out = [];
  document.querySelectorAll('a[href]').forEach(a => {
    const href = a.getAttribute('href');
    if (!href) return;
    const label = (a.innerText || a.getAttribute('aria-label') || '').trim().slice(0, 80);
    out.push({ href, label });
  });
  return out;
}
"""


def _same_origin(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return (pa.scheme, pa.netloc) == (pb.scheme, pb.netloc)


def _classify(href: str, base: str) -> str | None:
    if not href:
        return None
    s = href.strip()
    if not s or s.startswith("#"):
        return None
    lower = s.lower()
    for bad in ("mailto:", "tel:", "javascript:", "data:", "sms:", "blob:"):
        if lower.startswith(bad):
            return None
    abs_url, _ = urldefrag(urljoin(base, s))
    return abs_url


def extract_same_origin_links(page, base: str) -> list[dict[str, str]]:
    """Return [{url, label}] for every visible same-origin link on the page."""
    try:
        anchors = page.evaluate(_EXTRACT_JS) or []
    except Exception:
        return []
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for a in anchors:
        url = _classify(a.get("href", ""), base)
        if not url or not _same_origin(url, base):
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append({"url": url, "label": a.get("label", "")})
    return out


class Crawler:
    """BFS queue for pages to visit.

    The orchestrator calls `next_url()` to get the next target,
    navigates + probes it, then calls `record_visit(url, new_links)`
    to push any newly-discovered same-origin links.
    """

    def __init__(self, seed_url: str, max_pages: int = 10,
                 excluded_patterns: list[str] | None = None):
        self.origin = seed_url
        self.max_pages = max_pages
        self.excluded = excluded_patterns or [
            "/logout", "/signout", "/sign-out", "/auth/logout",
        ]
        self._visited: set[str] = set()
        self._queue: deque[str] = deque([seed_url])
        self._enqueued: set[str] = {seed_url}
        self._discovered_count = 1  # seed itself

    def next_url(self) -> str | None:
        while self._queue:
            url = self._queue.popleft()
            if url in self._visited:
                continue
            if any(pat in url for pat in self.excluded):
                continue
            if len(self._visited) >= self.max_pages:
                return None
            return url
        return None

    def record_visit(self, url: str, new_links: list[dict[str, str]]) -> int:
        """Mark url visited; enqueue new same-origin links. Returns how many were newly queued."""
        self._visited.add(url)
        added = 0
        for link in new_links:
            u = link.get("url", "")
            if not u or u in self._visited or u in self._enqueued:
                continue
            if any(pat in u for pat in self.excluded):
                continue
            if len(self._enqueued) >= self.max_pages * 3:  # prevent queue explosion
                break
            self._enqueued.add(u)
            self._queue.append(u)
            self._discovered_count += 1
            added += 1
        return added

    @property
    def visited(self) -> set[str]:
        return set(self._visited)

    @property
    def discovered(self) -> int:
        return self._discovered_count

    @property
    def remaining(self) -> int:
        return len(self._queue)
