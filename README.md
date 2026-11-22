# pz-modding: a Claude skill for Project Zomboid Build 42 mods

A skill (for Claude Code and claude.ai) that takes a Project Zomboid mod from idea to Workshop upload:
Workshop-shaped repo layout, Lua that Build 42 actually accepts, checking every engine call against the
game jar, unit specs, an isolated local dedicated server and clients for multiplayer testing, Workshop
descriptions that do not read like AI wrote them, preview images and screenshots, and a release
checklist.

It is distilled from building and shipping five B42 mods (a trait, a client UI add-on, a driving aid, a
sound mod and a large multiplayer admin system) and every bug that slipped through along the way, a
survey of the 273 mods installed on the author's PC, and the
[PZ wiki's modding pages](https://pzwiki.net/wiki/Modding).
The [AI pitfalls checklist](references/ai-pitfalls.md) is the short version.

## Contents

| File | What |
|---|---|
| [SKILL.md](SKILL.md) | The workflow and non-negotiables. Entry point. |
| [references/layout-and-metadata.md](references/layout-and-metadata.md) | Folder layout, `mod.info`, `workshop.txt`, sandbox options, ModOptions |
| [references/verify-against-game.md](references/verify-against-game.md) | Checking APIs against the jar (CFR on the game's own Java) and vanilla Lua |
| [references/community-patterns.md](references/community-patterns.md) | Idioms from a survey of 273 installed B42 mods and the PZ wiki: hooking, timed actions, loot, ModData sync, scripts, translations, tooling, legal |
| [references/b42-api-gotchas.md](references/b42-api-gotchas.md) | Kahlua quirks, B41 vs B42, MP commands, persistence, sound, Java mods, logs |
| [references/testing.md](references/testing.md) | Plain-Lua specs, isolated local server and clients, in-engine self-test, in-game checklist |
| [references/images.md](references/images.md) | Preview, poster, icons, screenshots |
| [references/workshop-description.md](references/workshop-description.md) | Structure, BBCode, voice, honesty rules |
| [references/release.md](references/release.md) | Versioning, upload, servers |
| [references/ai-pitfalls.md](references/ai-pitfalls.md) | The checklist to run before calling a mod done |
| [scripts/scaffold.py](scripts/scaffold.py) | New mod repo in the Workshop layout |
| [scripts/check_mod.py](scripts/check_mod.py) | Lint for silent packaging failures (B42 layout, B41 translations and scripts, `next()`, `pcall`, loose Lua files, preview size, 8000-char description, duplicate ids, private data) |
| [scripts/test-server.sh](scripts/test-server.sh), [scripts/test-client.sh](scripts/test-client.sh) | Isolated dedicated server and clients (Windows, Git Bash) |
| [scripts/make_preview.py](scripts/make_preview.py) | 256x256 Workshop preview from text or a screenshot (Pillow) |

## Install

**Claude Code:** copy (or clone) this folder to `~/.claude/skills/pz-modding/`.

```bash
git clone https://github.com/JoshuaSHenderson/pz-modding-skill ~/.claude/skills/pz-modding
```

**claude.ai:** zip the folder and upload it under Settings > Capabilities > Skills.

It triggers on Project Zomboid modding requests, or ask for it by name.

## Using the scripts on their own

```bash
python scripts/scaffold.py MyMod "My Mod" --author "You"
python scripts/check_mod.py ProjectZomboid-MyMod/MyMod
cd ProjectZomboid-MyMod
PZ_GAME="/c/Program Files (x86)/Steam/steamapps/common/ProjectZomboid" MOD=MyMod bash ../scripts/test-server.sh
```

Self-check for the scripts: `python tests/test_scripts.py`.

## Reference mods

Open-source mods the skill was built from, useful as worked examples:

- [ProjectZomboid-ADHD-Trait](https://github.com/JoshuaSHenderson/ProjectZomboid-ADHD-Trait): B42 trait, registries, sandbox options
- [ProjectZomboid-ALife-StanceDots](https://github.com/JoshuaSHenderson/ProjectZomboid-ALife-StanceDots): client add-on, map icons, Lua specs, Java bridge sub-mod
- [ProjectZomboid-Driving-Outline](https://github.com/JoshuaSHenderson/ProjectZomboid-Driving-Outline): ModOptions, object outlines
- [ProjectZomboid-Sprinter-Wail](https://github.com/JoshuaSHenderson/ProjectZomboid-Sprinter-Wail): sound scripts and audio prep
- [ProjectZomboid-Server-Event-Manager](https://github.com/JoshuaSHenderson/ProjectZomboid-Server-Event-Manager): server/client architecture, persistence, test rig, modder API

Project Zomboid is a trademark of The Indie Stone. This project is not affiliated with them.

## License

MIT
