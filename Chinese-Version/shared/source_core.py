"""Frozen text and source-linked extraction for yuri adaptation.

Provenance design references TavernWeave build-work-library at f9863d2.
This small text adapter is original code; no TavernWeave implementation is copied.
"""
import hashlib
import json
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonstandard JSON number")))


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def validate_schema(value, name):
    from jsonschema import Draft202012Validator
    schema = load(HERE / "assets" / name)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda x: str(list(x.path)))
    if errors:
        raise ValueError("; ".join(f"{list(e.path)}: {e.message}" for e in errors[:8]))


def safe(root, relative):
    path = Path(root) / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts or "\\" in str(relative) or not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("path escapes project")
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("linked source paths are unsupported")
    return path


def epub_members(path, include_short=False):
    """Read narrative spine members without rendering, fetching or executing HTML."""
    with zipfile.ZipFile(path) as archive:
        container = ET.fromstring(archive.read("META-INF/container.xml"))
        opf_name = next(n.attrib["full-path"] for n in container.iter() if n.tag.endswith("rootfile"))
        opf = ET.fromstring(archive.read(opf_name))
        items = {n.attrib["id"]: n.attrib for n in opf.iter() if n.tag.endswith("}item")}
        refs = [n.attrib["idref"] for n in opf.iter() if n.tag.endswith("}itemref")]
        for ref in refs:
            item = items[ref]
            if item.get("media-type") not in ("application/xhtml+xml", "text/html") or "nav" in item.get("properties", "").split():
                continue
            member = posixpath.normpath(posixpath.join(posixpath.dirname(opf_name), item["href"].split("#")[0]))
            if member.startswith(("../", "/")) or archive.getinfo(member).file_size > 16 * 1024 * 1024:
                raise ValueError("unsupported EPUB member path or size")
            root = ET.fromstring(archive.read(member))
            paragraphs = ["".join(n.itertext()).strip() for n in root.iter() if n.tag.split("}")[-1] in ("p", "h1", "h2", "h3")]
            text = "\n".join(p for p in paragraphs if p)
            # Covers, copyright pages and tables of contents are not narrative chapters.
            if text and (include_short or len(text) >= 800):
                yield member, text


def epub_text(path, chapter=1):
    for index, value in enumerate(epub_members(path), 1):
        if index == chapter:
            return value
    raise ValueError("requested narrative EPUB spine member is unavailable")


def select_text(path, chapter=None, max_chars=6000, encoding="utf-8-sig", all_text=False, max_file_mib=64):
    if not all_text and not 100 <= max_chars <= 100000:
        raise ValueError("max-chars must be between 100 and 100000")
    if all_text and chapter is not None:
        raise ValueError("--all and --chapter are separate selection modes")
    path = Path(path)
    if max_file_mib <= 0 or path.stat().st_size > max_file_mib * 1024 * 1024:
        raise ValueError("input exceeds the selected max-file-mib byte limit")
    if path.suffix.lower() == ".epub":
        if all_text:
            members, pieces, offset = [], [], 0
            for name, body in epub_members(path, include_short=True):
                if pieces:
                    pieces.append("\n\n"); offset += 2
                members.append({"member": name, "start": offset, "end": offset + len(body)})
                pieces.append(body); offset += len(body)
            text = "".join(pieces)
            if not text:
                raise ValueError("no supported narrative EPUB members")
            location = {"epub_members": members, "unit_kind": "readable_spine_collection"}
        else:
            member, text = epub_text(path, chapter or 1)
            location = {"epub_member": member, "unit_kind": "narrative_spine_member"}
    elif path.suffix.lower() in (".txt", ".md"):
        text = path.read_text(encoding=encoding)
        location = {"unit_kind": "normalized_text"}
    else:
        raise ValueError("use TXT, Markdown, or EPUB; agent tools save accessible webpages as text snapshots")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    full_size, start = len(text), 0
    if chapter is not None and path.suffix.lower() != ".epub":
        marks = list(re.finditer(r"(?m)^(?:第[零〇一二三四五六七八九十百千万两0-9]+[章回节].*|Chapter\s+\d+.*)$", text))
        if not 1 <= chapter <= len(marks):
            raise ValueError("requested chapter not found; omit --chapter for paragraph-bounded excerpts")
        start = marks[chapter - 1].start()
        text = text[start:marks[chapter].start() if chapter < len(marks) else len(text)]
        location["chapter_ordinal"] = chapter
    selected_size = len(text)
    if not all_text and len(text) > max_chars:
        end = text.rfind("\n", 0, max_chars)
        text = text[:end if end > max_chars // 2 else max_chars]
    location.update(normalized_start=start, normalized_end=start + len(text), selected_unit_characters=selected_size,
                    source_text_characters=full_size, frozen_characters=len(text), partial=len(text) < full_size)
    return text, location


def ingest(input_path, project, source_id, kind, chapter=None, max_chars=6000, url=None, encoding="utf-8-sig", all_text=False, chunk_chars=6000, max_file_mib=64):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", source_id):
        raise ValueError("use a stable lower-case source ID")
    if kind not in ("post", "novel"):
        raise ValueError("kind must be post or novel")
    if chapter is not None and chapter < 1:
        raise ValueError("chapter must be positive")
    project = Path(project)
    if (project / "sources.json").exists():
        manifest = load(project / "sources.json")
        extraction = load(project / "extracted.json")
    else:
        if project.exists() and any(project.iterdir()):
            raise ValueError("new source projects need an empty directory")
        manifest = {"schema_version": "1.0", "sources": []}
        extraction = {"schema_version": "2.0", "review_status": "pending", "entities": [], "claims": [],
                      "relationships": [], "constraints": [], "events": [], "unresolved": []}
    if any(s["id"] == source_id for s in manifest["sources"]):
        raise ValueError("source IDs are immutable; use a new ID for changed material")
    if not 100 <= chunk_chars <= 100000:
        raise ValueError("chunk-chars must be between 100 and 100000")
    text, coverage = select_text(input_path, chapter, max_chars, encoding, all_text, max_file_mib)
    if all_text:
        coverage.update(reading_mode="all", chunk_chars=chunk_chars)
    project.mkdir(parents=True, exist_ok=True)
    (project / "sources").mkdir(exist_ok=True)
    frozen = safe(project, f"sources/{source_id}.txt")
    if frozen.exists():
        raise ValueError("frozen source already exists")
    frozen.write_text(text, encoding="utf-8", newline="\n")
    from datetime import datetime, timezone
    manifest["sources"].append({"id": source_id, "kind": kind, "filename": Path(input_path).name,
        "url": url, "captured_at": datetime.now(timezone.utc).isoformat(), "original_sha256": digest(Path(input_path).read_bytes()),
        "text_path": frozen.relative_to(project).as_posix(), "text_sha256": digest(frozen.read_bytes()),
        "coverage": coverage, "offset_basis": "Unicode code points in frozen UTF-8 LF text", "original_bytes_retained": False})
    extraction["review_status"] = "pending"
    dump(project / "sources.json", manifest)
    dump(project / "extracted.json", extraction)
    if all_text:
        ledger = load(project / "units.json") if (project / "units.json").exists() else {"schema_version": "1.0", "units": []}
        for ordinal, (start, end) in enumerate(text_units(text, chunk_chars), 1):
            ledger["units"].append({"id": f"{source_id}-{ordinal:06d}", "source_id": source_id,
                "text_sha256": digest(frozen.read_bytes()), "start": start, "end": end,
                "unit_sha256": digest(text[start:end].encode("utf-8")), "status": "pending"})
        dump(project / "units.json", ledger)
    return manifest["sources"][-1]


def text_units(text, limit):
    """Cover every codepoint, favoring chapter and paragraph boundaries."""
    chapters = [m.start() for m in re.finditer(r"(?m)^(?:第[零〇一二三四五六七八九十百千万两0-9]+[章回节].*|Chapter\s+\d+.*)$", text)]
    start = 0
    while start < len(text):
        ceiling = min(start + limit, len(text))
        next_chapter = next((p for p in chapters if start < p <= ceiling), None)
        if next_chapter is not None:
            end = next_chapter
        elif ceiling < len(text):
            newline = text.rfind("\n", start + limit // 2, ceiling)
            end = newline + 1 if newline >= 0 else ceiling
        else:
            end = ceiling
        yield start, end
        start = end


def read_unit(project, unit_id=None):
    project = Path(project)
    units = load(project / "units.json")["units"]
    unit = next((u for u in units if u["id"] == unit_id), None) if unit_id else next((u for u in units if u["status"] == "pending"), None)
    if unit is None:
        return {"complete": all(u["status"] == "agent_reviewed" for u in units), "units": len(units)}
    source = next(s for s in load(project / "sources.json")["sources"] if s["id"] == unit["source_id"])
    raw = safe(project, source["text_path"]).read_bytes()
    if digest(raw) != unit["text_sha256"] or digest(raw) != source["text_sha256"]:
        raise ValueError("source changed after unit planning")
    text = raw.decode("utf-8")[unit["start"]:unit["end"]]
    if digest(text.encode("utf-8")) != unit["unit_sha256"]:
        raise ValueError("unit range/hash mismatch")
    return {**unit, "text": text, "complete": False}


def review_unit(project, unit_id):
    unit = read_unit(project, unit_id)
    if "text" not in unit:
        raise ValueError("unknown unit ID")
    validate_extraction(project)
    ledger = load(Path(project) / "units.json")
    next(u for u in ledger["units"] if u["id"] == unit_id)["status"] = "agent_reviewed"
    dump(Path(project) / "units.json", ledger)
    return source_coverage(project)


def source_coverage(project):
    path = Path(project) / "units.json"
    if not path.exists():
        return {"mode": "frozen_excerpt", "complete_work_claimed": False}
    units = load(path)["units"]
    sources = load(Path(project) / "sources.json")["sources"]
    ids = [u["id"] for u in units]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate reading unit ID")
    for source in sources:
        selected = sorted((u for u in units if u["source_id"] == source["id"]), key=lambda u: u["start"])
        if not selected and source["coverage"].get("reading_mode") != "all":
            continue
        raw = safe(project, source["text_path"]).read_bytes()
        text, end = raw.decode("utf-8"), 0
        for unit in selected:
            if unit["start"] != end or unit["end"] <= end or unit["end"] > len(text) or unit["text_sha256"] != digest(raw) or unit["status"] not in ("pending", "agent_reviewed"):
                raise ValueError("reading units have a gap, overlap, stale source or invalid status")
            if digest(text[unit["start"]:unit["end"]].encode("utf-8")) != unit["unit_sha256"]:
                raise ValueError("reading unit hash mismatch")
            end = unit["end"]
        if end != len(text) or digest(raw) != source["text_sha256"]:
            raise ValueError("reading units do not cover the registered source")
    reviewed = [u["id"] for u in units if u["status"] == "agent_reviewed"]
    return {"mode": "segmented_source", "units": len(units), "reviewed_unit_ids": reviewed,
            "complete_work_claimed": len(reviewed) == len(units),
            "limitation": "Unit review flags are agent acknowledgments, not proof of semantic completeness."}


def validate_extraction(project):
    project = Path(project)
    manifest, extraction = load(project / "sources.json"), load(project / "extracted.json")
    validate_schema(manifest, "sources.schema.json")
    validate_schema(extraction, "source-extraction.schema.json")
    texts = {}
    for source in manifest["sources"]:
        if source["id"] in texts:
            raise ValueError("duplicate source ID")
        raw = safe(project, source["text_path"]).read_bytes()
        if digest(raw) != source["text_sha256"]:
            raise ValueError("frozen source hash mismatch")
        texts[source["id"]] = raw.decode("utf-8")
    def evidence(items):
        for item in items:
            text = texts.get(item["source_id"])
            if text is None or not 0 <= item["start"] < item["end"] <= len(text) or text[item["start"]:item["end"]] != item["quote"]:
                raise ValueError("evidence is outside frozen text or its quote differs")
    all_ids = set()
    entities = {e["id"] for e in extraction["entities"]}
    claims = {c["id"] for c in extraction["claims"]}
    for group in ("entities", "claims", "relationships", "constraints", "events", "unresolved"):
        for record in extraction[group]:
            if record["id"] in all_ids:
                raise ValueError("duplicate extraction ID")
            all_ids.add(record["id"])
            evidence(record.get("evidence", []))
            if not set(record.get("entity_ids", [])).issubset(entities) or not set(record.get("claim_ids", [])).issubset(claims):
                raise ValueError("broken extraction reference")
            if group == "relationships" and not {record["from_id"], record["to_id"]}.issubset(entities):
                raise ValueError("unknown relationship endpoint")
    return manifest, extraction
