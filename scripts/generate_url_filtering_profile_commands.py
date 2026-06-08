#!/usr/bin/env python3
"""Generate exhaustive PAN-OS/Panorama URL Filtering profile set commands.

Input should be the live predefined URL category list from the target Panorama or
firewall content version. The script accepts either plain text with one category
per line or XML-ish output containing <entry name="category"> elements.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_BLOCK_CATEGORIES = {
    # Known-dangerous / abuse categories recommended or commonly blocked for egress guardrails.
    "abused-drugs",
    "adult",
    "command-and-control",
    "compromised-website",
    "copyright-infringement",
    "dynamic-dns",
    "encrypted-dns",
    "extremism",
    "gambling",
    "grayware",
    "hacking",
    "malware",
    "newly-registered-domain",
    "parked",
    "phishing",
    "proxy-avoidance-and-anonymizers",
    "ransomware",
    "unknown",
}

CATEGORY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ENTRY_RE = re.compile(r"<entry\s+name=['\"]([^'\"]+)['\"]")


def load_categories(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    found: set[str] = set()

    for match in ENTRY_RE.findall(raw):
        item = match.strip()
        if CATEGORY_RE.match(item):
            found.add(item)

    if not found:
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Accept CLI completion lines like "adult  Adult sites" by taking first token.
            token = re.split(r"\s+", line, maxsplit=1)[0].strip()
            token = token.strip("'\",;:[]{}()")
            if CATEGORY_RE.match(token):
                found.add(token)

    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate exhaustive URL Filtering profile commands from live predefined categories."
    )
    parser.add_argument("--categories-file", required=True, type=Path, help="File containing live predefined URL categories")
    parser.add_argument("--device-group", default="AWS_GWLB_EGRESSCORE_NP")
    parser.add_argument("--profile", default="URLF-EGRESS-PROXY-GUARDRAILS")
    parser.add_argument(
        "--block",
        action="append",
        default=[],
        help="Additional category to block. Can be repeated. Defaults are already included.",
    )
    parser.add_argument(
        "--no-default-blocks",
        action="store_true",
        help="Do not use the built-in default block category set.",
    )
    parser.add_argument(
        "--include-base",
        action="store_true",
        help="Also emit profile description and log-container-page-only commands.",
    )
    args = parser.parse_args()

    categories = load_categories(args.categories_file)
    if not categories:
        print(f"ERROR: no URL categories parsed from {args.categories_file}", file=sys.stderr)
        return 2

    block_set = set(args.block)
    if not args.no_default_blocks:
        block_set |= DEFAULT_BLOCK_CATEGORIES

    unknown_blocks = sorted(block_set - set(categories))
    if unknown_blocks:
        print(
            "WARN: requested block categories not present in live category input: " + ", ".join(unknown_blocks),
            file=sys.stderr,
        )

    prefix = f"set device-group {args.device_group} profiles url-filtering {args.profile}"

    if args.include_base:
        print(f'{prefix} description "AWS EWP egress URL guardrails"')
        print(f"{prefix} log-container-page-only yes")

    for category in categories:
        action = "block" if category in block_set else "alert"
        print(f"{prefix} {action} {category}")

    print(
        f"# Summary: {len(categories)} predefined categories covered, "
        f"{sum(1 for c in categories if c in block_set)} block, "
        f"{sum(1 for c in categories if c not in block_set)} alert",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
