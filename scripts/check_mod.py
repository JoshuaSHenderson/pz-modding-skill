#!/usr/bin/env python3
"""Lint a Project Zomboid B42 Workshop item folder for the silent failures that ship broken mods.

    python check_mod.py <ItemFolder>      # e.g. MyMod (the folder holding workshop.txt and Contents/)

Exit 1 on any ERROR. Stdlib only.
"""
import json
import re
import struct
import sys
import wave
from pathlib import Path

ALLOWED_CONTENTS = {"mods", "buildings", "creative"}
TEXT_EXT = {".lua", ".txt", ".json", ".info", ".md", ".xml"}
PRIVATE = [
    (re.compile(r"\b(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b"), "private IP address"),
    (re.compile(r"[\w.+-]+@[\w-]+\.(?:com|net|org|io)\b"), "email address"),
    (re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+\w+|/home/\w+|/Users/\w+", re.I), "home folder path"),
]
NEXT_CALL = re.compile(r"(?<![\w.:])next\s*\(")
PCALL = re.compile(r"(?<![\w.:])pcall\s*\(")
VERSION_DIR = re.compile(r"\d+(\.\d+)*")
B41_SCRIPT = re.compile(r"^\s*(?:Type\s*=\s*[A-Za-z]+\s*,|recipe\s+\S)", re.M)


def read_info(p):
    out = {}
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def png_size(p):
    """(width, height, bit depth) of a PNG, or None."""
    with p.open("rb") as f:
        head = f.read(25)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24]) + (head[24],)


def check(item):
    errors, warns = [], []
    err, warn = errors.append, warns.append
    item = Path(item)

    ws = item / "workshop.txt"
    if not ws.is_file():
        err(f"{ws}: missing")
    else:
        lines = ws.read_text(encoding="utf-8", errors="replace").splitlines()
        desc = "\n".join(l[len("description="):] for l in lines if l.startswith("description="))
        if len(desc) > 8000:
            err(f"{ws}: description is {len(desc)} chars; Steam limit is 8000")
        if not any(l.startswith("title=") and l[6:].strip() for l in lines):
            err(f"{ws}: no title=")

    prev = item / "preview.png"
    if not prev.is_file():
        warn(f"{prev}: missing (Workshop card image, square, up to 512x512)")
    else:
        if prev.stat().st_size >= 1024 * 1024:
            err(f"{prev}: {prev.stat().st_size} bytes; Steam limit is 1 MB")
        size = png_size(prev)
        if size is None:
            err(f"{prev}: not a PNG")
        else:
            w, h, depth = size
            if w > 512 or h > 512:
                err(f"{prev}: {w}x{h}; the in-game uploader allows at most 512x512")
            if w != h:
                warn(f"{prev}: {w}x{h} is not square")
            if depth != 8:
                warn(f"{prev}: {depth}-bit; the uploader expects 8-bit colour")

    contents = item / "Contents"
    if not contents.is_dir():
        err(f"{contents}: missing")
        return errors, warns
    for d in contents.iterdir():
        if d.name not in ALLOWED_CONTENTS:
            err(f"{d}: only {sorted(ALLOWED_CONTENTS)} are allowed in Contents/ (uploader refuses)")

    ids = {}
    for mod in sorted((contents / "mods").glob("*")):
        if not mod.is_dir():
            continue
        for d in mod.iterdir():
            if d.name.lower() in ("common", "mod.info") and d.name != d.name.lower():
                err(f"{d}: must be lowercase '{d.name.lower()}' (Linux/macOS are case-sensitive)")
        versions = sorted(d for d in mod.iterdir() if d.is_dir() and VERSION_DIR.fullmatch(d.name))
        common = mod / "common"
        infos = [p for p in [mod / "mod.info", common / "mod.info"] + [v / "mod.info" for v in versions] if p.is_file()]
        if not infos:
            err(f"{mod}: no mod.info at the root, in common/ or in a version folder - the game will not list it")
            continue
        if not versions and not common.is_dir():
            warn(f"{mod}: no common/ or version folder (42/) - that is the B41 layout; B42 mods need one")
        if versions and not common.is_dir() and not (mod / "mod.info").is_file():
            err(f"{mod}: only {versions[0].name}/ with no common/ and no root mod.info - this shape was seen not to be listed; add both")
        elif versions and not common.is_dir():
            warn(f"{mod}: no common/ folder (the B42 standard layout per the PZ wiki; it may be empty)")
        for v in versions:
            if not (v / "mod.info").is_file():
                warn(f"{v}: version folder without mod.info")
        info = read_info(infos[0])
        if not info.get("id"):
            err(f"{infos[0]}: no id=")
        ids.setdefault(info.get("id"), []).append(mod.name)
        for other in infos[1:]:
            o = read_info(other)
            for k in ("id", "name", "modversion", "versionMin", "require"):
                if info.get(k) != o.get(k):
                    warn(f"{mod.name}: {infos[0].relative_to(mod)} and {other.relative_to(mod)} differ on {k}: {info.get(k)!r} vs {o.get(k)!r}")
        for p in infos:
            i = read_info(p)
            for key in ("poster", "icon"):
                if i.get(key) and not (p.parent / i[key]).is_file():
                    err(f"{p}: {key}={i[key]} not found next to it")
        for lua_root in [d / "media" / "lua" for d in versions + [common]]:
            for side in ("client", "server", "shared"):
                for f in sorted((lua_root / side).glob("*.lua")):
                    warn(f"{f.relative_to(item)}: loose Lua file; put it under a folder named after the mod so it cannot replace another mod's file")
    for mid, folders in ids.items():
        if mid and len(folders) > 1:
            err(f"mod id {mid!r} declared by several folders {folders}: the server loads whichever it scans first")

    pcalls = []
    for p in sorted(contents.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(item)
        if "Translate" in p.parts and p.suffix == ".txt":
            err(f"{rel}: B41 translation .txt; B42 only reads Translate/<LANG>/<Name>.json")
        if "Translate" in p.parts and p.suffix == ".json" and p.stem.upper().endswith("_" + p.parent.name.upper()):
            err(f"{rel}: language code in a translation file name; since 42.15 it is {p.stem[:-len(p.parent.name) - 1]}.json")
        if p.suffix == ".txt" and "scripts" in p.parts:
            text = p.read_text(encoding="utf-8", errors="replace")
            if B41_SCRIPT.search(text):
                warn(f"{rel}: B41 script syntax (Type = ... or a recipe block); B42 uses ItemType = base:... and craftRecipe")
        if "Translate" in p.parts and p.suffix == ".json":
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except (ValueError, UnicodeDecodeError) as e:
                err(f"{rel}: invalid JSON ({e})")
        if p.suffix == ".lua":
            for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                code = line.split("--", 1)[0]
                if NEXT_CALL.search(code):
                    err(f"{rel}:{n}: next() does not exist in PZ's Kahlua")
                if PCALL.search(code):
                    pcalls.append(f"{rel}:{n}")
        if p.suffix == ".wav":
            try:
                with wave.open(str(p)) as w:
                    if w.getnchannels() != 1:
                        warn(f"{rel}: stereo WAV; 3D sounds must be mono or they play flat at full volume")
            except (wave.Error, EOFError):
                pass

    if pcalls:
        warn(f"{len(pcalls)} pcall use(s), first {pcalls[0]}: fine around your own Lua (e.g. parsing input), "
             "useless around Java calls (it does not catch them, and modders read it as an AI tell); review each")
    for p in sorted(item.rglob("*")):
        if p.is_file() and p.suffix in TEXT_EXT:
            text = p.read_text(encoding="utf-8", errors="replace")
            for rx, what in PRIVATE:
                m = rx.search(text)
                if m:
                    warn(f"{p.relative_to(item)}: looks like a {what}: {m.group(0)!r}")
    return errors, warns


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    errors, warns = check(sys.argv[1])
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} error(s), {len(warns)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
