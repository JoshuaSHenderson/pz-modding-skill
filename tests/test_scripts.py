"""Self-check for scaffold.py and check_mod.py. Run: python tests/test_scripts.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(HERE))
import check_mod  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([sys.executable, str(HERE / "scaffold.py"), "TestMod", "Test Mod", "--dest", tmp], check=True)
    item = Path(tmp) / "ProjectZomboid-TestMod" / "TestMod"
    errors, warns = check_mod.check(item)
    assert errors == [], errors
    assert any("preview.png" in w for w in warns), warns

    mod = item / "Contents/mods/TestMod"
    (mod / "mod.info").unlink()
    assert any("root mod.info" in e for e in check_mod.check(item)[0])
    (mod / "mod.info").write_text((mod / "42/mod.info").read_text())

    lua = mod / "42/media/lua/client/TestMod/TestMod.lua"
    lua.write_text("if next(t) == nil then end\n-- next( in a comment is fine\nlocal x = t.next(1)\n")
    errs = check_mod.check(item)[0]
    assert len([e for e in errs if "next()" in e]) == 1, errs

    (mod / "42/media/lua/shared/Translate/EN/UI_EN.txt").write_text("UI_EN = {}")
    (item / "Contents/media").mkdir()
    ws = item / "workshop.txt"
    ws.write_text(ws.read_text() + "description=" + "x" * 8001 + "\n")
    errs = check_mod.check(item)[0]
    for needle in ("B41 translation", "only ['buildings'", "8000"):
        assert any(needle in e for e in errs), (needle, errs)

    lua.write_text("-- server at 192.168.1.50\n")
    assert any("private IP" in w for w in check_mod.check(item)[1])
print("ok")
