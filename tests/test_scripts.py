"""Self-check for scaffold.py and check_mod.py. Run: python tests/test_scripts.py"""
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(HERE))
import check_mod  # noqa: E402


def png(path, w, h):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    raw = b"".join(b"\0" + b"\0\0\0" * w for _ in range(h))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def has(msgs, needle):
    return any(needle in m for m in msgs)


with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([sys.executable, str(HERE / "scaffold.py"), "TestMod", "Test Mod", "--dest", tmp], check=True)
    item = Path(tmp) / "ProjectZomboid-TestMod" / "TestMod"
    mod = item / "Contents/mods/TestMod"
    errors, warns = check_mod.check(item)
    assert errors == [], errors
    assert warns and all("preview.png" in w for w in warns), warns

    # preview: 512 square is fine, bigger is an error
    png(item / "preview.png", 512, 512)
    assert check_mod.check(item) == ([], []), check_mod.check(item)
    png(item / "preview.png", 600, 600)
    assert has(check_mod.check(item)[0], "512x512")
    png(item / "preview.png", 256, 256)

    # the 42/-only shape that was seen not to be listed
    (mod / "mod.info").unlink()
    shutil.rmtree(mod / "common")
    assert has(check_mod.check(item)[0], "no common/ and no root mod.info")
    (mod / "common").mkdir()
    assert not check_mod.check(item)[0]  # common/ + 42/mod.info is the wiki layout
    (mod / "mod.info").write_text((mod / "42/mod.info").read_text())

    lua = mod / "42/media/lua/client/TestMod/TestMod.lua"
    lua.write_text("if next(t) == nil then end\n-- next( in a comment is fine\nlocal x = t.next(1)\npcall(f)\n")
    errs, warns = check_mod.check(item)
    assert len([e for e in errs if "next()" in e]) == 1, errs
    assert has(warns, "pcall"), warns

    (mod / "42/media/lua/client/Loose.lua").write_text("")
    assert has(check_mod.check(item)[1], "loose Lua file")

    tr = mod / "42/media/lua/shared/Translate/EN"
    (tr / "UI_EN.txt").write_text("UI_EN = {}")
    (tr / "IG_UI_EN.json").write_text("{}")
    (item / "Contents/media").mkdir()
    ws = item / "workshop.txt"
    ws.write_text(ws.read_text() + "description=" + "x" * 8001 + "\n")
    errs = check_mod.check(item)[0]
    for needle in ("B41 translation", "language code", "only ['buildings'", "8000"):
        assert has(errs, needle), (needle, errs)

    scripts = mod / "42/media/scripts/TestMod"
    scripts.mkdir(parents=True)
    (scripts / "items.txt").write_text("module TestMod {\n item Thing {\n  Type = Normal,\n }\n}\n")
    assert has(check_mod.check(item)[1], "B41 script syntax")

    lua.write_text("-- server at 192.168.1.50\n")
    assert has(check_mod.check(item)[1], "private IP")
print("ok")
