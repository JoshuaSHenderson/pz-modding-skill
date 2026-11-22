#!/usr/bin/env python3
"""Create a new Build 42 mod repo in the Workshop-shaped layout.

    python scaffold.py MyMod "My Mod" [--author NAME] [--dest DIR]

Writes DIR/ProjectZomboid-MyMod/ (default DIR = current folder). Refuses to overwrite. Stdlib only.
"""
import argparse
import re
from pathlib import Path

GITIGNORE = """__pycache__/
*.bak
*.log
*.out
.testserver*/
.testclient*/
docs/screenshots/raw/
"""


def files(mod_id, name, author):
    info = (f"name={name}\nid={mod_id}\nauthor={author}\nmodversion=0.1.0\nversionMin=42.0\n"
            f"description=TODO: one or two plain sentences on what it does.\n")
    m = f"{mod_id}/Contents/mods/{mod_id}"
    lua = f"{m}/42/media/lua"
    return {
        f"{m}/mod.info": info,                      # insurance copy, see references/layout-and-metadata.md
        f"{m}/42/mod.info": info,
        f"{m}/common/.gitkeep": "",                 # B42 needs common/; put big assets (models, textures) here
        f"{mod_id}/workshop.txt": (
            f"version=1\nid=\ntitle={name}\ndescription=[h1]{name}[/h1]\n"
            "description=TODO: the problem, then what the mod does about it.\ndescription=\n"
            "description=[h2]Features[/h2]\ndescription=[list]\ndescription=[*][b]TODO.[/b] How it behaves, with the default.\n"
            "description=[/list]\ndescription=\ndescription=[b]Build 42 only.[/b]\n"
            "tags=Build 42\nvisibility=public\n"),
        f"{lua}/shared/{mod_id}/Logic.lua": (
            f"-- Pure logic: no engine calls at load time, so tests/spec.lua can run it in plain Lua.\n"
            f"local {mod_id} = {mod_id} or {{}}\n\nfunction {mod_id}.clamp(n, lo, hi)\n"
            f"    return math.max(lo, math.min(hi, n))\nend\n\nreturn {mod_id}\n"),
        f"{lua}/client/{mod_id}/{mod_id}.lua": (
            f"if isServer() then return end\nrequire \"{mod_id}/Logic\"\n\n"
            f"Events.OnGameStart.Add(function()\n    print(\"[{mod_id}] loaded\")\nend)\n"),
        f"{lua}/shared/Translate/EN/UI.json": "{\n}\n",
        "tests/spec.lua": (
            "-- run from repo root: lua tests/spec.lua\nnext = nil -- PZ has no next()\n"
            "function isClient() return false end\nfunction isServer() return false end\n"
            f"package.path = \"{lua}/shared/?.lua;\" .. package.path\n"
            f"local M = require \"{mod_id}/Logic\"\n"
            "assert(M.clamp(5, 0, 3) == 3, \"clamp high\")\nassert(M.clamp(-1, 0, 3) == 0, \"clamp low\")\n"
            "print(\"spec ok\")\n"),
        ".gitignore": GITIGNORE,
        "CHANGELOG.md": "# Changelog\n\n## 0.1.0\n\nFirst version.\n",
        "README.md": (
            f"# {name} (Project Zomboid B42)\n\nMod id `{mod_id}`.\n\nTODO: what it does.\n\n"
            "## Options\n\n## How it works\n\n## Install\n\n"
            f"Copy `{mod_id}/Contents/mods/{mod_id}` to `%USERPROFILE%\\Zomboid\\mods\\`, restart the game, enable it.\n\n"
            "## Test\n\n```\nlua tests/spec.lua\n```\n\n## Known limits\n\n## License\n"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mod_id")
    ap.add_argument("name")
    ap.add_argument("--author", default="TODO")
    ap.add_argument("--dest", default=".")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", a.mod_id):
        ap.error("mod_id: letters, digits and _ only, starting with a letter")
    root = Path(a.dest) / f"ProjectZomboid-{a.mod_id}"
    if root.exists():
        ap.error(f"{root} already exists")
    for rel, text in files(a.mod_id, a.name, a.author).items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
    print(f"created {root}")


if __name__ == "__main__":
    main()
