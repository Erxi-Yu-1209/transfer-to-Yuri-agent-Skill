"""Thin SillyTavern file adapter over the unmodified Foreverse MIT exporter.

PNG embedding/build_v2/to_v3 are upstream code. Metadata attribution corrections,
bounded reading and explicit worldbook copying below are Workbench integration.
"""
import base64
import copy
import json
import struct
import zlib
from pathlib import Path
from vendor import card_md_to_st as upstream
from source_core import dump, load


def from_markdown(path):
    card, _ = upstream.build_v2(Path(path))
    front, _ = upstream.parse_front(Path(path).read_text(encoding="utf-8"))
    # The code's author is not the author of this newly generated roleplay card.
    if not front.get("creator"):
        card["data"]["creator"] = "Yuri Card Workbench"
    return card


def versions(card):
    if card.get("spec") not in ("chara_card_v2", "chara_card_v3") or not isinstance(card.get("data"), dict):
        raise ValueError("expected a v2/v3 wrapped character card")
    v2 = copy.deepcopy(card)
    v2.update(spec="chara_card_v2", spec_version="2.0")
    v3 = upstream.to_v3(v2)
    # Avoid attributing the source work itself to the exporter repository.
    v3["data"]["source"] = copy.deepcopy(card["data"].get("source", []))
    return v2, v3


def read_png(path):
    raw = Path(path).read_bytes()
    if not raw.startswith(upstream.PNG_SIG):
        raise ValueError("not a PNG")
    found, pos, ended = {}, 8, False
    while pos < len(raw):
        if pos + 12 > len(raw):
            raise ValueError("truncated PNG chunk")
        size = struct.unpack(">I", raw[pos:pos + 4])[0]
        if pos + size + 12 > len(raw) or size > 64 * 1024 * 1024:
            raise ValueError("invalid PNG chunk size")
        kind, body = raw[pos + 4:pos + 8], raw[pos + 8:pos + size + 8]
        crc = struct.unpack(">I", raw[pos + size + 8:pos + size + 12])[0]
        if zlib.crc32(kind + body) & 0xffffffff != crc:
            raise ValueError("PNG CRC mismatch")
        if kind == b"tEXt" and body.split(b"\0", 1)[0] in (b"chara", b"ccv3"):
            key, payload = body.split(b"\0", 1)
            if key in found:
                raise ValueError("duplicate card payload")
            decoded = base64.b64decode(payload, validate=True)
            if len(decoded) > 16 * 1024 * 1024:
                raise ValueError("card payload too large")
            found[key] = json.loads(decoded)
        pos += size + 12
        if kind == b"IEND":
            ended = True
            if pos != len(raw):
                raise ValueError("trailing PNG bytes")
            break
    if not ended:
        raise ValueError("PNG is missing IEND")
    if not found:
        raise ValueError("no supported uncompressed chara/ccv3 tEXt card payload")
    if b"chara" in found and b"ccv3" in found:
        left, right = copy.deepcopy(found[b"chara"]["data"]), copy.deepcopy(found[b"ccv3"]["data"])
        for data in (left, right):
            data.pop("group_only_greetings", None)
            data.pop("source", None)
        if left != right:
            raise ValueError("v2/v3 payloads disagree; select and reconcile explicitly")
    return found.get(b"ccv3", found.get(b"chara"))


def write_new(path, value, binary=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb" if binary else "x", **({} if binary else {"encoding": "utf-8"})) as stream:
        stream.write(value if binary else json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def pack(card_path, avatar, output):
    v2, v3 = versions(load(card_path))
    # Decode/encode stays in the established upstream component; no image redraw.
    write_new(output, upstream.embed_card_in_png(Path(avatar).read_bytes(), v2, v3), True)


def extract_worldbook(card_path, output):
    card = read_png(card_path) if Path(card_path).suffix.lower() == ".png" else load(card_path)
    book = copy.deepcopy(card["data"].get("character_book"))
    if not isinstance(book, dict) or not isinstance(book.get("entries"), (list, dict)):
        raise ValueError("card has no structured worldbook to extract; embedded prose needs an authored migration")
    if isinstance(book["entries"], list):
        entries = {}
        for index, entry in enumerate(book["entries"]):
            key = str(entry.get("id", f"entry-{index:05d}"))
            if key in entries:
                raise ValueError("duplicate worldbook entry IDs")
            entries[key] = entry
        book["entries"] = entries
    write_new(output, book)


def embed_worldbook(card_path, book_path, output, replace=False):
    card, book = load(card_path), copy.deepcopy(load(book_path))
    if card["data"].get("character_book") and not replace:
        raise ValueError("card already has a worldbook; use --replace for explicit replacement")
    if isinstance(book.get("entries"), dict):
        book["entries"] = list(book["entries"].values())
    if not isinstance(book.get("entries"), list):
        raise ValueError("worldbook needs entries")
    card["data"]["character_book"] = book
    write_new(output, card)
