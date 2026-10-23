#!/usr/bin/env python3
"""Fetch a URL, convert it to readable text, cache it, print it (optionally filtered).

Why: research evidence must be verbatim. Everybody (researchers and tools/verify_quotes.py) reads the
SAME cached text, so a quote either appears in it or it does not.

Usage (repository root):
    python3 tools/fetch_text.py URL                      # first 6000 characters
    python3 tools/fetch_text.py URL --grep 'ECTS|credits' [--context 2]   # only matching lines
    python3 tools/fetch_text.py URL --offset 6000 --max 6000
    python3 tools/fetch_text.py URL --links              # list links (anchor text -> URL) to navigate sites
Exit status 2 on HTTP/network error (message on stderr).
"""
import argparse
import gzip
import hashlib
import html
import os
import re
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / ".cache"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 course-research"
BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "table", "ul", "ol", "header", "footer", "td", "th", "dt", "dd"}
SKIP = {"script", "style", "noscript", "svg", "head"}


class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.links, self.skip, self.href, self.anchor = [], [], 0, None, []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        if tag in BLOCK:
            self.out.append("\n")
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.anchor = []

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1
        if tag in BLOCK:
            self.out.append("\n")
        if tag == "a" and self.href:
            self.links.append((" ".join("".join(self.anchor).split()), self.href))
            self.href = None

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)
            if self.href is not None:
                self.anchor.append(data)


def ctx():
    ca = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
    return ssl.create_default_context(cafile=ca) if os.path.exists(ca) else ssl.create_default_context()


def fetch_bytes(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/pdf,*/*;q=0.8",
                                               "Accept-Language": "en,fr;q=0.8,zh;q=0.6", "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx()) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return data, r.headers.get("Content-Type", ""), r.geturl()


def to_text(data, ctype, url):
    if "pdf" in ctype.lower() or url.lower().split("?")[0].endswith(".pdf") or data[:4] == b"%PDF":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as t:
            t.write(data)
        try:
            return subprocess.run(["pdftotext", "-layout", t.name, "-"], capture_output=True, text=True, timeout=120).stdout, []
        finally:
            os.unlink(t.name)
    m = re.search(rb"charset=([\w-]+)", data[:4096], re.I) or re.search(r"charset=([\w-]+)", ctype, re.I)
    enc = (m.group(1).decode() if m and isinstance(m.group(1), bytes) else m.group(1) if m else "utf-8")
    try:
        text = data.decode(enc, errors="replace")
    except LookupError:
        text = data.decode("utf-8", errors="replace")
    p = Extract()
    p.feed(text)
    body = html.unescape("".join(p.out))
    body = re.sub(r"[ \t\r\f\v ]+", " ", body)
    body = re.sub(r"\n\s*\n+", "\n", body)
    return body.strip(), p.links


def get(url, refresh=False):
    """Return (text, links, final_url). Cached by URL."""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()
    f, lf = CACHE / f"{key}.txt", CACHE / f"{key}.links"
    if f.exists() and not refresh:
        links = [tuple(l.split("\t", 1)) for l in lf.read_text(encoding="utf-8").splitlines() if "\t" in l] if lf.exists() else []
        return f.read_text(encoding="utf-8"), links, url
    data, ctype, final = fetch_bytes(url)
    text, links = to_text(data, ctype, final)
    f.write_text(text, encoding="utf-8")
    lf.write_text("\n".join(f"{a}\t{urllib.parse.urljoin(final, h)}" for a, h in links), encoding="utf-8")
    return text, [(a, urllib.parse.urljoin(final, h)) for a, h in links], final


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--grep")
    ap.add_argument("--context", type=int, default=1)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--max", type=int, default=6000)
    ap.add_argument("--links", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    try:
        text, links, final = get(a.url, a.refresh)
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        print(f"FETCH ERROR {a.url}: {e}", file=sys.stderr)
        return 2
    print(f"[{final}] {len(text)} chars", file=sys.stderr)
    if a.links:
        for t, h in links:
            if t and h.startswith("http"):
                print(f"{t[:90]} -> {h}")
        return 0
    if a.grep:
        lines = text.split("\n")
        rx = re.compile(a.grep, re.I)
        keep = set()
        for i, l in enumerate(lines):
            if rx.search(l):
                keep.update(range(max(0, i - a.context), min(len(lines), i + a.context + 1)))
        out = "\n".join(lines[i] for i in sorted(keep))
        print(out[: a.max * 3])
        return 0
    print(text[a.offset: a.offset + a.max])
    return 0


if __name__ == "__main__":
    sys.exit(main())
