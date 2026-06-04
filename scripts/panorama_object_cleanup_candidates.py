#!/usr/bin/env python3
"""
Panorama offline object cleanup candidate analyzer.

Purpose:
  Parse an exported Palo Alto Panorama/PAN-OS XML config and report objects that
  appear unused by real policy after recursively resolving object groups.

This is intentionally READ-ONLY. It does not connect to Panorama and does not
  delete anything.

Example:
  python3 scripts/panorama_object_cleanup_candidates.py panorama.xml \
    --csv cleanup_candidates.csv \
    --refs refs.csv \
    --duplicates duplicates.csv

Notes:
  - Best first pass for address/address-group/service/service-group cleanup.
  - Counts direct policy references and inherited references through groups.
  - Handles shared + device-group scope resolution with basic parent-dg support.
  - Treat output as cleanup candidates, not automatic delete truth. Review before
    deleting, especially automation-owned and shared/global objects.
"""

from __future__ import annotations

import argparse
import csv
import ipaddress
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

OBJECT_CONTAINERS = {
    "address": "address",
    "address-group": "address-group",
    "service": "service",
    "service-group": "service-group",
    "application-group": "application-group",
    "tag": "tag",
}

GROUP_MEMBER_KINDS = {"address-group", "service-group", "application-group"}

# Rule fields that hold object names. This is intentionally conservative.
RULE_REF_FIELDS = {
    "address": {"source", "destination", "source-hip", "destination-hip"},
    "service": {"service"},
    "application": {"application"},
    "tag": {"tag", "category"},
}

BUILT_INS = {
    "any",
    "application-default",
    "none",
    "unknown",
    "predefined",
    "default",
    "not-applicable",
}

POLICY_CONTAINER_NAMES = {
    "security",
    "nat",
    "pbf",
    "decryption",
    "tunnel-inspection",
    "authentication",
    "dos",
    "qos",
    "policy-based-forwarding",
}


@dataclass(frozen=True)
class ObjKey:
    scope: str
    kind: str
    name: str


@dataclass
class ObjDef:
    key: ObjKey
    value: str = ""
    members: set[str] = field(default_factory=set)
    description: str = ""
    tags: set[str] = field(default_factory=set)
    xpath_hint: str = ""
    entry_id: int = 0


@dataclass
class Ref:
    ref_name: str
    ref_family: str
    ref_scope: str
    rulebase: str
    policy_type: str
    rule_name: str
    field: str
    resolved_to: ObjKey | None
    via_group: str = ""


@dataclass
class GlobalRef:
    object_key: ObjKey
    ref_scope: str
    ref_xpath: str
    ref_tag: str
    ref_text: str
    context: str


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def direct_children_named(node: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in list(node) if strip_ns(c.tag) == name]


def child_text(node: ET.Element, name: str) -> str:
    c = next((x for x in list(node) if strip_ns(x.tag) == name), None)
    return (c.text or "").strip() if c is not None and c.text else ""


def members_of(node: ET.Element, child_name: str = "member") -> set[str]:
    out = set()
    for m in node.iter():
        if strip_ns(m.tag) == child_name and m.text:
            val = m.text.strip()
            if val:
                out.add(val)
    return out


def entry_name(node: ET.Element) -> str:
    return node.attrib.get("name", "").strip()


def find_device_groups(root: ET.Element) -> dict[str, ET.Element]:
    dgs: dict[str, ET.Element] = {}
    for dg_container in root.iter():
        if strip_ns(dg_container.tag) != "device-group":
            continue
        for e in direct_children_named(dg_container, "entry"):
            name = entry_name(e)
            if name:
                dgs[name] = e
    return dgs


def find_shared(root: ET.Element) -> ET.Element | None:
    for c in root.iter():
        if strip_ns(c.tag) == "shared":
            return c
    return None


def get_scope_for_node(node: ET.Element, parents: dict[int, ET.Element]) -> str:
    cur = node
    while id(cur) in parents:
        cur = parents[id(cur)]
        if strip_ns(cur.tag) == "entry" and entry_name(cur):
            parent = parents.get(id(cur))
            if parent is not None and strip_ns(parent.tag) == "device-group":
                return f"device-group:{entry_name(cur)}"
        if strip_ns(cur.tag) == "shared":
            return "shared"
    return "unknown"


def build_parent_map(root: ET.Element) -> dict[int, ET.Element]:
    parents = {}
    for p in root.iter():
        for c in list(p):
            parents[id(c)] = p
    return parents


def xpath_hint(node: ET.Element, parents: dict[int, ET.Element]) -> str:
    parts = []
    cur: ET.Element | None = node
    while cur is not None:
        t = strip_ns(cur.tag)
        n = entry_name(cur)
        parts.append(f"{t}[@name='{n}']" if n else t)
        cur = parents.get(id(cur))
    return "/" + "/".join(reversed(parts[-10:]))


def parse_objects(root: ET.Element, parents: dict[int, ET.Element]) -> dict[ObjKey, ObjDef]:
    objects: dict[ObjKey, ObjDef] = {}
    for container in root.iter():
        cname = strip_ns(container.tag)
        kind = OBJECT_CONTAINERS.get(cname)
        if not kind:
            continue
        # Avoid catching rule fields named service/application/tag as object containers.
        entries = direct_children_named(container, "entry")
        if not entries:
            continue
        scope = get_scope_for_node(container, parents)
        if scope == "unknown":
            continue
        for e in entries:
            name = entry_name(e)
            if not name:
                continue
            members = set()
            if kind in GROUP_MEMBER_KINDS:
                static = next((c for c in list(e) if strip_ns(c.tag) == "static"), None)
                if static is not None:
                    members = members_of(static)
            value = summarize_object_value(kind, e)
            desc = child_text(e, "description")
            tags_node = next((c for c in list(e) if strip_ns(c.tag) == "tag"), None)
            tags = members_of(tags_node) if tags_node is not None else set()
            key = ObjKey(scope, kind, name)
            objects[key] = ObjDef(key, value, members, desc, tags, xpath_hint(e, parents), id(e))
    return objects


def summarize_object_value(kind: str, e: ET.Element) -> str:
    if kind == "address":
        for k in ("ip-netmask", "ip-range", "fqdn", "wildcard"):
            v = child_text(e, k)
            if v:
                return f"{k}:{v}"
    if kind == "service":
        proto_parts = []
        proto = next((c for c in list(e) if strip_ns(c.tag) == "protocol"), None)
        if proto is not None:
            for p in list(proto):
                pname = strip_ns(p.tag)
                port = child_text(p, "port")
                override = child_text(p, "override")
                proto_parts.append(f"{pname}/{port or override}".rstrip("/"))
        return ";".join(proto_parts)
    if kind.endswith("group"):
        static = next((c for c in list(e) if strip_ns(c.tag) == "static"), None)
        if static is not None:
            return "members:" + ",".join(sorted(members_of(static))[:50])
        dynamic = next((c for c in list(e) if strip_ns(c.tag) == "dynamic"), None)
        if dynamic is not None:
            return "dynamic-filter:" + child_text(dynamic, "filter")
    return ""


def parse_device_group_parents(dgs: dict[str, ET.Element]) -> dict[str, str]:
    out = {}
    for name, node in dgs.items():
        parent = child_text(node, "parent-dg") or child_text(node, "parent")
        if parent:
            out[name] = parent
    return out


def candidate_scopes(scope: str, dg_parents: dict[str, str]) -> list[str]:
    if scope == "shared":
        return ["shared"]
    if scope.startswith("device-group:"):
        dg = scope.split(":", 1)[1]
        scopes = []
        seen = set()
        while dg and dg not in seen:
            seen.add(dg)
            scopes.append(f"device-group:{dg}")
            dg = dg_parents.get(dg, "")
        scopes.append("shared")
        return scopes
    return [scope, "shared"]


def resolve_name(name: str, family: str, scope: str, objects: dict[ObjKey, ObjDef], dg_parents: dict[str, str]) -> ObjKey | None:
    if not name or name in BUILT_INS:
        return None
    kinds = []
    if family == "address":
        kinds = ["address", "address-group"]
    elif family == "service":
        kinds = ["service", "service-group"]
    elif family == "application":
        # Built-in applications are not object definitions in the exported custom object tree.
        kinds = ["application-group"]
    elif family == "tag":
        kinds = ["tag"]
    for s in candidate_scopes(scope, dg_parents):
        for k in kinds:
            key = ObjKey(s, k, name)
            if key in objects:
                return key
    return None


def is_rule_entry(e: ET.Element, parents: dict[int, ET.Element]) -> tuple[bool, str, str]:
    """Return (is_rule, rulebase, policy_type)."""
    cur = parents.get(id(e))
    saw_rules = False
    policy_type = ""
    rulebase = ""
    while cur is not None:
        t = strip_ns(cur.tag)
        if t == "rules":
            saw_rules = True
        elif saw_rules and not policy_type and t in POLICY_CONTAINER_NAMES:
            policy_type = t
        elif saw_rules and t.endswith("rulebase"):
            rulebase = t
            return True, rulebase, policy_type or "unknown"
        cur = parents.get(id(cur))
    return False, "", ""


def parse_policy_refs(root: ET.Element, parents: dict[int, ET.Element], objects: dict[ObjKey, ObjDef], dg_parents: dict[str, str]) -> list[Ref]:
    refs: list[Ref] = []
    for e in root.iter():
        if strip_ns(e.tag) != "entry" or not entry_name(e):
            continue
        ok, rulebase, policy_type = is_rule_entry(e, parents)
        if not ok:
            continue
        scope = get_scope_for_node(e, parents)
        rule_name = entry_name(e)
        for family, fields in RULE_REF_FIELDS.items():
            for field in fields:
                fnode = next((c for c in list(e) if strip_ns(c.tag) == field), None)
                if fnode is None:
                    continue
                for name in members_of(fnode):
                    if name in BUILT_INS:
                        continue
                    resolved = resolve_name(name, family, scope, objects, dg_parents)
                    refs.append(Ref(name, family, scope, rulebase, policy_type, rule_name, field, resolved))
    return refs


def group_family(kind: str) -> str:
    if kind in {"address", "address-group"}:
        return "address"
    if kind in {"service", "service-group"}:
        return "service"
    if kind == "application-group":
        return "application"
    if kind == "tag":
        return "tag"
    return kind


def propagate_group_refs(objects: dict[ObjKey, ObjDef], refs: list[Ref], dg_parents: dict[str, str]) -> list[Ref]:
    """If a group is policy-referenced, mark all transitive members as referenced via that group."""
    by_key_refs = defaultdict(list)
    for r in refs:
        if r.resolved_to:
            by_key_refs[r.resolved_to].append(r)

    expanded: list[Ref] = []
    for group_key, direct_refs in list(by_key_refs.items()):
        if group_key.kind not in GROUP_MEMBER_KINDS:
            continue
        for base_ref in direct_refs:
            q = deque([(group_key, group_key.name)])
            seen = set()
            while q:
                cur_key, via = q.popleft()
                if cur_key in seen:
                    continue
                seen.add(cur_key)
                obj = objects.get(cur_key)
                if not obj:
                    continue
                fam = group_family(cur_key.kind)
                for member_name in obj.members:
                    mkey = resolve_name(member_name, fam, cur_key.scope, objects, dg_parents)
                    if not mkey:
                        continue
                    expanded.append(Ref(
                        ref_name=member_name,
                        ref_family=fam,
                        ref_scope=base_ref.ref_scope,
                        rulebase=base_ref.rulebase,
                        policy_type=base_ref.policy_type,
                        rule_name=base_ref.rule_name,
                        field=base_ref.field,
                        resolved_to=mkey,
                        via_group=via,
                    ))
                    if mkey.kind in GROUP_MEMBER_KINDS:
                        q.append((mkey, via))
    return refs + expanded


def collect_group_internal_refs(objects: dict[ObjKey, ObjDef], dg_parents: dict[str, str]) -> set[ObjKey]:
    internal = set()
    for key, obj in objects.items():
        if key.kind not in GROUP_MEMBER_KINDS:
            continue
        fam = group_family(key.kind)
        for m in obj.members:
            mk = resolve_name(m, fam, key.scope, objects, dg_parents)
            if mk:
                internal.add(mk)
    return internal


def is_within_node(node: ET.Element, ancestor_id: int, parents: dict[int, ET.Element]) -> bool:
    cur: ET.Element | None = node
    while cur is not None:
        if id(cur) == ancestor_id:
            return True
        cur = parents.get(id(cur))
    return False


def global_name_refs(root: ET.Element, parents: dict[int, ET.Element], objects: dict[ObjKey, ObjDef]) -> list[GlobalRef]:
    """Conservatively scan the entire XML for exact object-name text references.

    This intentionally scans beyond known rulebases/templates/policies. It records any
    element text exactly equal to an object name, excluding the object's own
    definition subtree. This may include false positives, but that is safer for
    cleanup than missing config dependencies.
    """
    by_name: dict[str, list[ObjKey]] = defaultdict(list)
    for key in objects:
        by_name[key.name].append(key)

    refs: list[GlobalRef] = []
    for node in root.iter():
        text = (node.text or "").strip()
        if not text or text not in by_name or text in BUILT_INS:
            continue
        ref_scope = get_scope_for_node(node, parents)
        ref_tag = strip_ns(node.tag)
        hint = xpath_hint(node, parents)
        context_parts = []
        cur = parents.get(id(node))
        for _ in range(4):
            if cur is None:
                break
            t = strip_ns(cur.tag)
            n = entry_name(cur)
            context_parts.append(f"{t}:{n}" if n else t)
            cur = parents.get(id(cur))
        context = " <- ".join(context_parts)
        for key in by_name[text]:
            obj = objects[key]
            if obj.entry_id and is_within_node(node, obj.entry_id, parents):
                continue
            refs.append(GlobalRef(key, ref_scope, hint, ref_tag, text, context))
    return refs


def duplicate_value_rows(objects: dict[ObjKey, ObjDef]) -> list[dict[str, str]]:
    buckets = defaultdict(list)
    for obj in objects.values():
        if obj.key.kind not in {"address", "service"} or not obj.value:
            continue
        norm = normalize_value(obj.value)
        buckets[(obj.key.kind, norm)].append(obj)
    rows = []
    for (kind, norm), vals in sorted(buckets.items(), key=lambda x: (x[0][0], x[0][1])):
        if len(vals) < 2:
            continue
        for o in vals:
            rows.append({
                "kind": kind,
                "normalized_value": norm,
                "scope": o.key.scope,
                "name": o.key.name,
                "raw_value": o.value,
                "description": o.description,
                "tags": ";".join(sorted(o.tags)),
            })
    return rows


def normalize_value(value: str) -> str:
    if value.startswith("ip-netmask:"):
        raw = value.split(":", 1)[1]
        try:
            # Canonicalize IP networks but keep host /32 behavior.
            return "ip-netmask:" + str(ipaddress.ip_network(raw, strict=False))
        except ValueError:
            return value.lower()
    return value.lower()


def write_csv(path: Path, rows: Iterable[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def main() -> int:
    ap = argparse.ArgumentParser(description="Offline Panorama XML object cleanup candidate analyzer")
    ap.add_argument("xml", type=Path, help="Exported Panorama/PAN-OS XML config")
    ap.add_argument("--csv", type=Path, default=Path("panorama_cleanup_candidates.csv"), help="Object candidate CSV output")
    ap.add_argument("--refs", type=Path, default=Path("panorama_object_refs.csv"), help="Reference detail CSV output")
    ap.add_argument("--duplicates", type=Path, default=Path("panorama_duplicate_values.csv"), help="Duplicate address/service value CSV output")
    ap.add_argument("--global-refs", type=Path, default=Path("panorama_global_refs.csv"), help="Conservative whole-config exact-name reference CSV output")
    ap.add_argument("--include-groups", action="store_true", help="Include groups in zero-policy-reference candidate output")
    args = ap.parse_args()

    print(f"loading XML: {args.xml}", flush=True)
    try:
        tree = ET.parse(args.xml)
        root = tree.getroot()
    except Exception as e:
        print(f"failed to parse XML: {e}", file=sys.stderr, flush=True)
        return 2

    print("building XML parent map...", flush=True)
    parents = build_parent_map(root)
    print("discovering device groups...", flush=True)
    dgs = find_device_groups(root)
    dg_parents = parse_device_group_parents(dgs)
    print(f"device groups discovered: {len(dgs)}", flush=True)
    print("parsing objects...", flush=True)
    objects = parse_objects(root, parents)
    print(f"objects parsed: {len(objects)}", flush=True)
    print("parsing policy references...", flush=True)
    direct_refs = parse_policy_refs(root, parents, objects, dg_parents)
    print(f"direct policy refs parsed: {len(direct_refs)}", flush=True)
    print("expanding recursive group references...", flush=True)
    all_refs = propagate_group_refs(objects, direct_refs, dg_parents)
    internal_group_refs = collect_group_internal_refs(objects, dg_parents)
    print("scanning whole config for exact object-name references...", flush=True)
    global_refs = global_name_refs(root, parents, objects)

    policy_ref_counts = defaultdict(int)
    direct_policy_ref_counts = defaultdict(int)
    ref_labels = defaultdict(set)
    unresolved = []

    for r in all_refs:
        if r.resolved_to:
            policy_ref_counts[r.resolved_to] += 1
            ref_labels[r.resolved_to].add(f"{r.ref_scope}/{r.rulebase}/{r.policy_type}/{r.rule_name}/{r.field}" + (f" via {r.via_group}" if r.via_group else ""))
        elif r.ref_name not in BUILT_INS and r.ref_family in {"address", "service", "tag"}:
            unresolved.append(r)
    for r in direct_refs:
        if r.resolved_to:
            direct_policy_ref_counts[r.resolved_to] += 1

    global_ref_counts = defaultdict(int)
    for gr in global_refs:
        global_ref_counts[gr.object_key] += 1

    candidate_rows = []
    for key, obj in sorted(objects.items(), key=lambda kv: (kv[0].scope, kv[0].kind, kv[0].name)):
        if not args.include_groups and key.kind in GROUP_MEMBER_KINDS:
            continue
        count = policy_ref_counts[key]
        direct_count = direct_policy_ref_counts[key]
        if count == 0:
            reason = "zero_policy_references"
            if key in internal_group_refs:
                reason = "group_member_only_no_policy_references"
            candidate_rows.append({
                "scope": key.scope,
                "kind": key.kind,
                "name": key.name,
                "value": obj.value,
                "policy_reference_count": str(count),
                "direct_policy_reference_count": str(direct_count),
                "global_reference_count": str(global_ref_counts[key]),
                "cleanup_reason": reason,
                "description": obj.description,
                "tags": ";".join(sorted(obj.tags)),
                "xpath_hint": obj.xpath_hint,
            })

    ref_rows = []
    for r in sorted(all_refs, key=lambda x: (x.ref_scope, x.rulebase, x.policy_type, x.rule_name, x.field, x.ref_name, x.via_group)):
        ref_rows.append({
            "ref_scope": r.ref_scope,
            "rulebase": r.rulebase,
            "policy_type": r.policy_type,
            "rule_name": r.rule_name,
            "field": r.field,
            "ref_name": r.ref_name,
            "ref_family": r.ref_family,
            "resolved_scope": r.resolved_to.scope if r.resolved_to else "",
            "resolved_kind": r.resolved_to.kind if r.resolved_to else "",
            "resolved_name": r.resolved_to.name if r.resolved_to else "",
            "via_group": r.via_group,
        })

    dup_rows = duplicate_value_rows(objects)
    global_ref_rows = []
    for gr in sorted(global_refs, key=lambda x: (x.object_key.scope, x.object_key.kind, x.object_key.name, x.ref_scope, x.ref_xpath)):
        global_ref_rows.append({
            "scope": gr.object_key.scope,
            "kind": gr.object_key.kind,
            "name": gr.object_key.name,
            "ref_scope": gr.ref_scope,
            "ref_tag": gr.ref_tag,
            "ref_text": gr.ref_text,
            "context": gr.context,
            "ref_xpath": gr.ref_xpath,
        })

    write_csv(args.csv, candidate_rows, [
        "scope", "kind", "name", "value", "policy_reference_count", "direct_policy_reference_count",
        "global_reference_count", "cleanup_reason", "description", "tags", "xpath_hint",
    ])
    write_csv(args.refs, ref_rows, [
        "ref_scope", "rulebase", "policy_type", "rule_name", "field", "ref_name", "ref_family",
        "resolved_scope", "resolved_kind", "resolved_name", "via_group",
    ])
    write_csv(args.duplicates, dup_rows, [
        "kind", "normalized_value", "scope", "name", "raw_value", "description", "tags",
    ])
    write_csv(args.global_refs, global_ref_rows, [
        "scope", "kind", "name", "ref_scope", "ref_tag", "ref_text", "context", "ref_xpath",
    ])

    print(f"policy refs parsed: direct={len(direct_refs)} expanded={len(all_refs)} unresolved_direct={len(unresolved)}", flush=True)
    print(f"cleanup candidates written: {args.csv.resolve()} ({len(candidate_rows)} rows)", flush=True)
    print(f"reference details written: {args.refs.resolve()} ({len(ref_rows)} rows)", flush=True)
    print(f"duplicate values written: {args.duplicates.resolve()} ({len(dup_rows)} rows)", flush=True)
    print(f"global references written: {args.global_refs.resolve()} ({len(global_ref_rows)} rows)", flush=True)
    if unresolved:
        print("warning: unresolved object names exist in policy refs; review refs CSV for blanks", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
