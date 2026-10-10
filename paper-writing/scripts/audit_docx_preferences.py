#!/usr/bin/env python3
"""Read-only Word preference audit. No document rewriting or content certification."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
FALSE = {"0", "false", "off", "no"}


def member(archive: ZipFile, name: str) -> bytes:
    try:
        return archive.read(name)
    except KeyError:
        return archive.read(name.replace("/", "\\"))


def property_node(properties, name):
    return properties.find(W + name) if properties is not None else None


def enabled(node):
    return node is not None and node.get(W + "val", "1").lower() not in FALSE


def audit(path: Path) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with ZipFile(path) as package:
        document = ET.fromstring(member(package, "word/document.xml"))
        try:
            styles_xml = ET.fromstring(member(package, "word/styles.xml"))
        except KeyError:
            styles_xml = ET.Element(W + "styles")
    styles = {}
    default_style = "Normal"
    for style in styles_xml.findall(W + "style"):
        if style.get(W + "type") != "paragraph":
            continue
        sid = style.get(W + "styleId", "")
        styles[sid] = style
        if style.get(W + "default") == "1":
            default_style = sid
    defaults = styles_xml.find(f"{W}docDefaults/{W}pPrDefault/{W}pPr")

    def resolve(ppr, sid, name):
        direct = property_node(ppr, name)
        if direct is not None:
            return direct, "direct"
        seen = set()
        while sid and sid not in seen:
            seen.add(sid)
            style = styles.get(sid)
            if style is None:
                break
            value = property_node(style.find(W + "pPr"), name)
            if value is not None:
                return value, f"style:{sid}"
            parent = style.find(W + "basedOn")
            sid = parent.get(W + "val") if parent is not None else None
        return property_node(defaults, name), "document-defaults"

    paragraphs = list(document.iter(W + "p"))
    flags, outlines, borders = [], [], []
    for index, paragraph in enumerate(paragraphs, 1):
        text = "".join(element.text or "" for element in paragraph.iter(W + "t"))
        ppr = paragraph.find(W + "pPr")
        style_ref = property_node(ppr, "pStyle")
        sid = style_ref.get(W + "val", default_style) if style_ref is not None else default_style
        description = {"paragraph": index, "style": sid, "text_preview": text[:90]}
        for option in ("keepLines", "keepNext", "pageBreakBefore"):
            node, origin = resolve(ppr, sid, option)
            if enabled(node):
                flags.append({**description, "option": option, "origin": origin})
        node, origin = resolve(ppr, sid, "outlineLvl")
        if node is not None:
            try:
                level = int(node.get(W + "val", "9"))
            except ValueError:
                level = 9
            if 0 <= level <= 8:
                outlines.append({**description, "level": level, "origin": origin})
        if sid.lower().startswith(("title", "heading")):
            node, origin = resolve(ppr, sid, "pBdr")
            if node is not None and any(child.get(W + "val", "single") not in {"nil", "none"} for child in node):
                borders.append({**description, "origin": origin})

    instructions = []
    for element in document.iter():
        if element.tag == W + "instrText":
            instructions.append(element.text or "")
        elif element.tag == W + "fldSimple":
            instructions.append(element.get(W + "instr", ""))
    field_text = " ".join(instructions)
    field_counts = {
        "endnote_citations": len(re.findall(r"\bADDIN\s+EN\.CITE(?:\s|$)", field_text, re.I)),
        "endnote_bibliographies": len(re.findall(r"\bADDIN\s+EN\.REFLIST(?:\s|$)", field_text, re.I)),
        "zotero_citations": len(re.findall(r"\bADDIN\s+ZOTERO_ITEM(?:\s|$)", field_text, re.I)),
        "zotero_bibliographies": len(re.findall(r"\bADDIN\s+ZOTERO_BIBL(?:\s|$)", field_text, re.I)),
    }
    unchanged = hashlib.sha256(path.read_bytes()).hexdigest() == digest
    if not unchanged:
        raise RuntimeError("Document changed while being audited; re-read the saved version.")
    return {
        "path": str(path.resolve()), "sha256": digest, "source_unchanged": unchanged,
        "scope": "word/document.xml paragraphs and inherited paragraph styles",
        "paragraph_count": len(paragraphs), "table_count": sum(1 for _ in document.iter(W + "tbl")),
        "pagination_options": flags, "collapsible_outline_levels": outlines,
        "title_or_heading_borders": borders, "citation_field_counts": field_counts,
        "interpretation": "Only structural findings; verify layout, full field integrity and scientific content separately. Existing templates may intentionally contain flagged settings."
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("--baseline", type=Path, help="Optional previous version for field-count comparison")
    parser.add_argument("--json", type=Path, dest="json_path", help="Optional new audit report; never the input DOCX")
    args = parser.parse_args()
    input_paths = [args.document] + ([args.baseline] if args.baseline else [])
    if args.json_path and args.json_path.resolve() in {p.resolve() for p in input_paths}:
        parser.error("JSON output must be different from both input documents")
    report = audit(args.document)
    if args.baseline:
        original = audit(args.baseline)
        report["baseline"] = {"path": original["path"], "sha256": original["sha256"], "source_unchanged": original["source_unchanged"]}
        report["field_count_delta"] = {
            key: value - original["citation_field_counts"][key]
            for key, value in report["citation_field_counts"].items()
        }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
