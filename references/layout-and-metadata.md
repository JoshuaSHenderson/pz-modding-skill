# Layout and metadata

## Repo layout (Workshop-shaped)

Keep the repo's item folder **byte-for-byte the shape of a Workshop item**, so packaging is a copy, not
a rebuild:

```
ProjectZomboid-MyMod/                  <- git repo
  README.md  CHANGELOG.md  LICENSE  .gitignore
  MyMod/                               <- Workshop item folder (= ~/Zomboid/Workshop/MyMod)
    workshop.txt
    preview.png                        <- square, max 512x512, 8-bit colour, < 1 MB
    Contents/
      mods/
        MyMod/                         <- the mod (folder name = what players see on disk)
          mod.info                     <- copy of 42/mod.info; insurance, see "Which layout" below
          common/                      <- B42: assets shared by every game version (models, textures, sounds)
            media/...
          42/                          <- B42 version folder: code + mod.info + poster + icon
            mod.info
            poster.png                 <- shown in the in-game mod list
            icon.png                   <- optional small icon in the mod list
            media/
              lua/{client,server,shared}/MyMod/...
              lua/shared/Translate/EN/{UI,Sandbox,IG_UI,ItemName,...}.json
              scripts/MyMod/...  sound/  textures/  ui/  models_X/
              sandbox-options.txt
              registries.lua           <- only if you register traits/other registry ids
          42.13/                       <- optional: a full alternative 42/ for game 42.13+ (see below)
  docs/screenshots/                    <- curated, named PNGs used by README and workshop.txt
  tests/                               <- plain-Lua specs and in-game self-tests
  tools/                               <- image/audio/model build scripts, deploy, rig scripts
```

Anything in the item folder that is not `Contents/` (README, `.git`, `.vscode`, source art) is ignored
by the game and the uploader, so the wiki's recommendation is to make the item folder itself the git
repo, living in `~/Zomboid/Workshop/`. Keeping the repo elsewhere and copying in (this skill's
`release.md`) also works; either way there must be **exactly one copy** of the mod the game can see.

### Which layout (B42)

The B42 loader knows a **`common/`** folder and **version folders** named `42`, `42.13`, `42.20`, ...
(the jar's `ChooseGameInfo`/`ZomboidFileSystem` hold `commonDir`, `versionDir`, `bestVersion`). Per the
PZ wiki "Mod structure" page (revised for 42.22):

- Load order: `common/` first, then the **one** version folder closest to the running game version,
  whose files overwrite same-path files from `common/`. Version folders are not merged with each other;
  each is complete (installed mods like damnlib ship full `42.0`, `42.13`, `42.17`, `42.20` copies).
- Names: `42` = 42.0, `42.13` = 42.13; a third number is ignored (`42.1.5` is treated as 42.1).
- Put `mod.info`, `poster.png`, `icon.png` and code in the version folder; put big assets in `common/`
  so they are not duplicated per version. The wiki says at least one version folder or `common/` is
  needed for the mod to be recognised.
- Use lowercase `common` and `mod.info`: Linux and macOS are case-sensitive.

What the 273 mods installed on the reference PC do: 129 ship root `mod.info` + `common/` + version
folder (the most common), 66 ship `common/` + version folder with no root `mod.info`, 12 ship root
`mod.info` + `42/` without `common/`, and 7 ship only `42/`. Two of our own mods shipped as only
`42/mod.info` (no root `mod.info`, no `common/`) and **did not appear in the mod list**; adding a root
`mod.info` fixed both. So: always ship `common/` (it may be empty) and a version folder with `mod.info`,
and keep a root `mod.info` copy as cheap insurance. `scripts/check_mod.py` errors on the `42/`-only shape.

Rules the uploader and loader enforce:

- `Contents/` may hold **only** `mods`, `buildings` or `creative`. Anything else fails upload with
  "the following folders are the only ones permitted in contents".
- A file at the same path relative to `media/` as a vanilla or other-mod file **replaces** it (Lua,
  scripts, AnimSets). Mods later in the load order win. This is why everything goes under a folder
  named after your mod. `common/` vs version folder makes no difference to clashes between mods.
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
icon=icon.png
description=One or two plain sentences: what it does and how the player meets it.
require=\OtherModId
loadModAfter=\OtherModId
```

The full key list is in the wiki's ScriptsDocs. Only `id` and `name` are strictly needed. Keys seen
across the installed mods, most used first: `description`, `poster`, `id`, `name`, `require`, `icon`,
`author`, `versionMin`, `modversion`, `pzversion`, `incompatible`, `tags`, `loadModAfter`, `pack`,
`url`, `category`, `versionMax`, `tiledef`. `incompatible=\ModA,\ModB` stops the two being enabled
together. A `Translate/<LANG>/Mod.json` with `name`/`description` keys translates the mod list entry.
Watch for a hidden `.txt` extension (`mod.info.txt`) when the file is made on Windows.

| Key | Notes |
|---|---|
| `id` | Stable forever. Renaming loses saved settings and breaks server `Mods=` lines. No spaces. |
| `versionMin` | The oldest B42 build you actually tested on, e.g. `42.21.0` if you rely on a newer API. |
| `require` | Hard dependency. B42 form uses a leading backslash for mods from other items: `require=\ServerEventManager`. Comma-separate several. Mods in the same item have been written without it. |
| `loadModAfter` | Load order only. Use it when your Lua must see another mod's globals at file load. Optional integrations go here, **not** in `require`. |
| `javaJarFile`, `javaPkgName` | Only for Java mods loaded through a loader mod (e.g. ZombieBuddy); the loader asks the player to approve each new jar. |

Keep every `mod.info` copy identical (a version folder may add Java keys the root copy lacks). Bump
`modversion` in all of them on every release; `scripts/check_mod.py` warns when they drift.

`require=` ids: both `\ModId` and plain `ModId` appear in working mods. In Lua,
`getActivatedMods():contains("ModId")` is the usual way to detect an optional mod; a few B42 mods check
`"\\ModId"`. Check the form the target mod's id actually takes in your test, or check both.

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
- `visibility=public` works (all of our published items use it); the wiki also lists numeric values
  `0` public, `1` friends-only, `2` private, `3` unlisted.
- **The in-game uploader overwrites the whole Steam description** with what is in the uploader (from
  `workshop.txt`) and appends `Workshop ID: ...` / `Mod ID: ...` lines. Keep `workshop.txt` as the
  source of truth; never edit the description only on Steam. If you paste the Steam text back into the
  uploader, strip those two appended lines first or they duplicate.

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
them for anything the server decides. Sandbox options have no `module` block. `valueTranslation =` is
also used by installed mods (66 options) to point an enum at a shared set of value labels.

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

Full builder list (vanilla `media/lua/client/PZAPI/ModOptions.lua`): `addTitle`, `addDescription`,
`addSeparator`, `addTextEntry`, `addTickBox`, `addMultipleTickBox`, `addComboBox` (+ `:addItem`),
`addColorPicker`, `addKeyBind`, `addSlider`, `addButton`; most take an optional last `tooltip` argument.
`options:getOption("id")` fetches one later; `options.apply = function(self) ... end` runs on Apply. Values
are saved per PC in `<cache>/Lua/modOptions.ini`.

**Hard rule (PZ wiki, ModOptions page): never put gameplay in ModOptions.** Anything that spawns items,
changes the world, balance, or what other players experience is a **sandbox option**. ModOptions are
per-PC, not per-save and not server-controlled: in MP each player's setting would decide behaviour,
causing desyncs, and the same value would apply to every save. ModOptions are for UI, keybinds, colours,
sounds and other personal display preferences only.

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
