# Layout and metadata

## Repo layout (Workshop-shaped)

Keep the repo's item folder **byte-for-byte the shape of a Workshop item**, so packaging is a copy, not
a rebuild:

```
ProjectZomboid-MyMod/                  <- git repo
  README.md  CHANGELOG.md  LICENSE  .gitignore
  MyMod/                               <- Workshop item folder (copy this to ~/Zomboid/Workshop/MyMod)
    workshop.txt
    preview.png                        <- 256x256, < 1 MB
    Contents/
      mods/
        MyMod/                         <- the mod; copy THIS to ~/Zomboid/mods/MyMod for local play
          mod.info                     <- REQUIRED at the root, or the game never lists the mod
          poster.png                   <- optional, shown in the in-game mod list
          42/
            mod.info                   <- same content again, B42 convention
            poster.png
            media/
              lua/{client,server,shared}/MyMod/...
              lua/shared/Translate/EN/{UI,Sandbox,...}.json
              scripts/  sound/  textures/  ui/  models_X/
              sandbox-options.txt
              registries.lua           <- only if you register traits/other registry ids
  docs/screenshots/                    <- curated, named PNGs used by README and workshop.txt
  tests/                               <- plain-Lua specs and in-game self-tests
  tools/                               <- image/audio/model build scripts, deploy, rig scripts
```

Rules the uploader and loader enforce:

- `Contents/` may hold **only** `mods`, `buildings` or `creative`. Anything else fails upload with
  "the following folders are the only ones permitted in contents".
- Namespace every Lua folder and file under your mod name (`lua/client/MyMod/Thing.lua`).
  `require "MyMod/Thing"` paths are global across all loaded mods; a generic `Utils.lua` collides.
- Two copies of the inner and outer folder share a name. Copying the **outer** folder into
  `~/Zomboid/mods` puts `mod.info` too deep; the mod silently never appears.
- File and folder names are **case-sensitive on Linux dedicated servers**. An asset path that differs
  only in case works on Windows and breaks on the server.
- One mod id per folder. Two folders declaring the same `id=` (e.g. a "PreviousVersion" folder) make
  the server load whichever it scans first, so consecutive boots behave differently.
- A sub-mod (optional add-on in the same Workshop item) is another folder under `Contents/mods/` with
  its own id and `require=`.

## mod.info

```
name=My Mod
id=MyMod
author=Your Name
modversion=1.0.0
versionMin=42.0
poster=poster.png
description=One or two plain sentences: what it does and how the player meets it.
require=\OtherModId
loadModAfter=\OtherModId
```

| Key | Notes |
|---|---|
| `id` | Stable forever. Renaming loses saved settings and breaks server `Mods=` lines. No spaces. |
| `versionMin` | The oldest B42 build you actually tested on, e.g. `42.21.0` if you rely on a newer API. |
| `require` | Hard dependency. B42 form uses a leading backslash for mods from other items: `require=\ServerEventManager`. Comma-separate several. Mods in the same item have been written without it. |
| `loadModAfter` | Load order only. Use it when your Lua must see another mod's globals at file load. Optional integrations go here, **not** in `require`. |
| `javaJarFile`, `javaPkgName` | Only for Java mods loaded through a loader mod (e.g. ZombieBuddy); the loader asks the player to approve each new jar. |

Keep both `mod.info` files identical (the 42/ copy may add Java keys the root copy lacks). Bump
`modversion` in both on every release; `scripts/check_mod.py` warns when they drift.

## workshop.txt

```
version=1
id=
title=My Mod
description=[h1]My Mod[/h1]
description=First line of the page.
description=
tags=Build 42;Interface
visibility=public
```

- One `description=` line per line of the page; an empty `description=` is a blank line. BBCode, not
  Markdown. See [workshop-description.md](workshop-description.md).
- Leave `id=` blank for the first upload. Steam assigns it; write it back and commit, or the next
  upload creates a second item.
- Tags must be ones the Workshop offers (`Build 42`, `Interface`, `Multiplayer`, `Traits`, `Audio`,
  `Vehicles`, `Misc`, ...). Copy them from an existing item rather than inventing them.
- Description total must stay under **8000 characters** (Steam truncates or rejects). The lint counts it.

## Sandbox options

`42/media/sandbox-options.txt`:

```
VERSION = 1,

option MyMod.Range
{
	type = integer, min = 1, max = 100, default = 10,
	page = MyMod, translation = MyMod_Range,
}

option MyMod.Mode
{
	type = enum, numValues = 3, default = 1,
	page = MyMod, translation = MyMod_Mode,
}
```

Types: `boolean`, `integer`, `double`, `enum` (1-based, `numValues`), `string` (`default = ,` for
empty). Read them as `SandboxVars.MyMod.Range`. Sandbox values are synced from the server in MP; use
them for anything the server decides.

`42/media/lua/shared/Translate/EN/Sandbox.json`:

```json
{
  "Sandbox_MyMod": "My Mod",
  "Sandbox_MyMod_Range": "Range (tiles)",
  "Sandbox_MyMod_Range_tooltip": "How far ahead to look. Default 10.",
  "Sandbox_MyMod_Mode_option1": "First",
  "Sandbox_MyMod_Mode_option2": "Second",
  "Sandbox_MyMod_Mode_option3": "Third"
}
```

Raw keys showing in game (e.g. `Sandbox_MyMod_Mode_option1`) mean the translation file is not being
read: wrong name, wrong folder, or B41 `.txt` format.

## Per-player options (client)

B42 has a built-in mod options API; no dependency needed:

```lua
local options = PZAPI.ModOptions:create("MyMod", "My Mod")
local key   = options:addKeyBind("toggle", "Toggle", Keyboard.KEY_K)
local color = options:addColorPicker("color", "Color", 1.0, 0.85, 0.0, 1.0)
local range = options:addSlider("range", "Range (tiles)", 3, 20, 1, 10)
local tick  = options:addTickBox("foliage", "Include foliage", false)
-- read: range:getValue(), tick:getValue(), key:getValue()
```

Rule of thumb: sandbox options for what the server or world decides, ModOptions for personal taste.

## .gitignore baseline

```
__pycache__/
*.bak
*.log
*.out
.testserver*/
.testclient*/
docs/screenshots/raw/
```

Test rig folders hold real logs, usernames, IPs and Steam data. They must never be committed.
