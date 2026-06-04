#!/usr/bin/env python3
"""
Convert Panorama cleanup candidate CSV rows into PAN-OS/Panorama CLI delete commands.

Input is the `panorama_cleanup_candidates.csv` produced by
`panorama_object_cleanup_candidates.py`.

This script is intentionally conservative:
  - emits DELETE commands, not SET commands
  - skips anything with non-zero policy_reference_count unless --include-referenced
  - skips group_member_only rows unless --include-group-member-only
  - supports filtering by scope/kind
  - writes commands to a file for review/change control

Example:
  python3 scripts/panorama_candidates_to_delete_commands.py panorama_cleanup_candidates.csv \
    --out delete-unused-objects.txt

Then review before pasting into Panorama CLI configure mode.
"""

from __future__ import annotations

import argparse
import csv
import shlex
from pathlib import Path

SUPPORTED_KINDS = {
    "address": "address",
    "address-group": "address-group",
    "service": "service",
    "service-group": "service-group",
    "tag": "tag",
}


def q(value: str) -> str:
    # PAN-OS set/delete CLI accepts quoted names; shlex quote gives safe single quotes for spaces/special chars.
    return shlex.quote(value)


def command_for(scope: str, kind: str, name: str) -> str | None:
    cli_kind = SUPPORTED_KINDS.get(kind)
    if not cli_kind:
        return None
    if scope == "shared":
        return f"delete shared {cli_kind} {q(name)}"
    if scope.startswith("device-group:"):
        dg = scope.split(":", 1)[1]
        return f"delete device-group {q(dg)} {cli_kind} {q(name)}"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Panorama CLI delete commands from cleanup candidate CSV")
    ap.add_argument("csv", type=Path, help="panorama_cleanup_candidates.csv")
    ap.add_argument("--out", type=Path, default=Path("panorama_delete_commands.txt"), help="Output command file")
    ap.add_argument("--scope", action="append", help="Only include this scope; can repeat, e.g. shared or device-group:DG1")
    ap.add_argument("--kind", action="append", choices=sorted(SUPPORTED_KINDS), help="Only include this object kind; can repeat")
    ap.add_argument("--include-referenced", action="store_true", help="Allow rows with policy_reference_count > 0. Not recommended.")
    ap.add_argument("--include-group-member-only", action="store_true", help="Include rows with cleanup_reason=group_member_only_no_policy_references")
    ap.add_argument("--limit", type=int, default=0, help="Max commands to emit, useful for staged batches")
    ap.add_argument("--no-commit-comment", action="store_true", help="Do not append commit/validate reminder comments")
    args = ap.parse_args()

    scopes = set(args.scope or [])
    kinds = set(args.kind or [])
    commands: list[str] = []
    skipped = 0

    with args.csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"scope", "kind", "name", "policy_reference_count", "cleanup_reason"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"CSV missing required columns: {', '.join(sorted(missing))}")

        for row in reader:
            scope = row["scope"].strip()
            kind = row["kind"].strip()
            name = row["name"].strip()
            reason = row["cleanup_reason"].strip()
            ref_count = int(row.get("policy_reference_count") or 0)

            if scopes and scope not in scopes:
                skipped += 1
                continue
            if kinds and kind not in kinds:
                skipped += 1
                continue
            if ref_count > 0 and not args.include_referenced:
                skipped += 1
                continue
            if reason == "group_member_only_no_policy_references" and not args.include_group_member_only:
                skipped += 1
                continue

            cmd = command_for(scope, kind, name)
            if not cmd:
                skipped += 1
                continue
            commands.append(cmd)
            if args.limit and len(commands) >= args.limit:
                break

    lines = [
        "# Generated Panorama CLI delete commands",
        "# Review before use. Run from Panorama CLI configure mode.",
        "# Recommended flow: save config snapshot -> paste small batch -> validate/commit -> push scoped device groups.",
        "",
    ]
    lines.extend(commands)
    if not args.no_commit_comment:
        lines.extend([
            "",
            "# Suggested after review/testing:",
            "# validate full",
            "# commit description 'cleanup unused objects - reviewed candidate batch'",
        ])
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"commands written: {args.out.resolve()} ({len(commands)} commands, {skipped} rows skipped)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
