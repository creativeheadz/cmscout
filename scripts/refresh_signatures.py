#!/usr/bin/env python3
"""Refresh CMSmap enumeration lists from upstream directories (prototype).

Sources (all free, no API key):
  WP plugins/themes - wordpress.org SVN root listings. These include
    closed plugins, which is correct for a scanner: abandoned code
    stays installed on real sites.
  Drupal modules - drupal.org api-d7 node.json, paginated.

Writes refreshed lists to OUTDIR for review; never touches cmscout/data
in place. Joomla (JED has no bulk API - scrape job) and WPScan vuln
enrichment (25 req/day free) are follow-ups.

Usage:
  scripts/refresh_signatures.py /tmp/sig-review [--drupal-pages N]
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

UA = {"User-Agent": "CMSmap-signature-refresh/0.1 (research prototype)"}
HREF = re.compile(r'<li><a href="([^"/]+)/">')


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def wp_slugs(kind):
    html = fetch("https://%s.svn.wordpress.org/" % kind).decode("utf-8", "replace")
    return sorted(set(HREF.findall(html)))


def drupal_modules(max_pages=None, polite=0.4):
    names = []
    page = 0
    while True:
        if max_pages is not None and page >= max_pages:
            break
        data = json.loads(fetch(
            "https://www.drupal.org/api-d7/node.json"
            "?type=project_module&limit=100&page=%d" % page))
        items = data.get("list", [])
        if not items:
            break
        for item in items:
            name = item.get("field_project_machine_name")
            if name:
                names.append(name)
        page += 1
        time.sleep(polite)
    return sorted(set(names))


def report(label, fresh, current_path):
    current = set()
    if os.path.isfile(current_path):
        with open(current_path) as f:
            current = set(line.strip() for line in f if line.strip())
    fresh_set = set(fresh)
    print("%-14s fresh=%6d current=%6d overlap=%6d new=%6d gone=%6d" % (
        label, len(fresh_set), len(current),
        len(fresh_set & current),
        len(fresh_set - current), len(current - fresh_set)))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--drupal-pages", type=int, default=None,
                    help="cap Drupal pagination (omit for full pull)")
    args = ap.parse_args(argv)
    os.makedirs(args.outdir, exist_ok=True)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    Collected = [
        ("wp_plugins", wp_slugs("plugins"), "cmscout/data/wp_plugins.txt"),
        ("wp_themes", wp_slugs("themes"), "cmscout/data/wp_themes.txt"),
        ("dru_modules", drupal_modules(args.drupal_pages),
         "cmscout/data/dru_plugins.txt"),
    ]
    for label, fresh, relpath in Collected:
        out = os.path.join(args.outdir, label + ".txt")
        with open(out, "w") as f:
            f.write("\n".join(fresh) + "\n")
        report(label, fresh, os.path.join(root, relpath))
        print("  wrote %s" % out)


if __name__ == "__main__":
    main(sys.argv[1:])
