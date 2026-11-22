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


def read_info(p):
    out = {}
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def png_size(p):
    with p.open("rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


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
        warn(f"{prev}: missing (Workshop card image, 256x256)")
    else:
        if prev.stat().st_size >= 1024 * 1024:
            err(f"{prev}: {prev.stat().st_size} bytes; Steam limit is 1 MB")
        size = png_size(prev)
        if size is None:
            err(f"{prev}: not a PNG")
        elif size != (256, 256):
            warn(f"{prev}: {size[0]}x{size[1]}; Workshop cards are 256x256")

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
        root, b42 = mod / "mod.info", mod / "42" / "mod.info"
        if not root.is_file():
            err(f"{root}: missing - the game never lists the mod without a root mod.info")
            continue
        info = read_info(root)
        if not info.get("id"):
            err(f"{root}: no id=")
        ids.setdefault(info.get("id"), []).append(mod.name)
        if not b42.is_file():
            warn(f"{b42}: missing (B42 convention is a copy in 42/)")
        else:
            info42 = read_info(b42)
            for k in ("id", "name", "modversion", "versionMin", "require"):
                if info.get(k) != info42.get(k):
                    warn(f"{mod.name}: mod.info and 42/mod.info differ on {k}: {info.get(k)!r} vs {info42.get(k)!r}")
        if info.get("poster") and not (mod / info["poster"]).is_file():
            err(f"{root}: poster={info['poster']} not found")
    for mid, folders in ids.items():
        if mid and len(folders) > 1:
            err(f"mod id {mid!r} declared by several folders {folders}: the server loads whichever it scans first")

    for p in sorted(contents.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(item)
        if "Translate" in p.parts and p.suffix == ".txt":
            err(f"{rel}: B41 translation .txt; B42 only reads Translate/<LANG>/<Name>.json")
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
        if p.suffix == ".wav":
            try:
                with wave.open(str(p)) as w:
                    if w.getnchannels() != 1:
                        warn(f"{rel}: stereo WAV; 3D sounds must be mono or they play flat at full volume")
            except (wave.Error, EOFError):
                pass

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
