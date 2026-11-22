# AI pitfalls checklist

Every item below happened in a real AI-assisted PZ mod. Run this list before saying a mod is done.
`scripts/check_mod.py` catches the ones marked (lint).

## Code that the engine rejects

- [ ] **Invented or B41 API.** Every Java method, field and event checked against the installed jar and
      vanilla Lua (see verify-against-game.md). Real examples: `setRunSpeedModifier` (only the getter
      exists in B42), `HasTrait("X")` string form (gone), `TraitFactory` (gone).
- [ ] **Wrong overload.** Argument count and types checked, not just the name: `splatBloodFloorBig(0.6)`
      failed because the B42 method takes no arguments.
- [ ] **Static called on an instance** (`getCore():getTileScale()` -> `Core.getTileScale()`).
- [ ] **`next()` used** (lint). Kahlua has none; it errors every tick.
- [ ] **`pcall` as fake safety** around Java calls. It does not catch missing methods; it only hides
      that the call was never checked.
- [ ] **Assumed constants.** Enum numbers and magic values the code depends on are verified, or isolated
      as one constant with a `DEBUG` print and flagged to the user.
- [ ] **Java collections iterated as Lua tables** (`#list`, `ipairs(list)`).
- [ ] **Java objects stored in ModData** or across restarts.
- [ ] **Client trusted.** Server re-checks admin and validates every `OnClientCommand` payload.

## Files the engine never reads (silent failures)

- [ ] **Root `mod.info` present** (lint). A restructure that left only `42/mod.info` produced a mod that
      never appeared in the list, with no error. This happened twice.
- [ ] **Translations are B42 JSON** (lint): `Translate/EN/UI.json`, not `UI_EN.txt`. The `.txt` version was
      edited carefully for a whole commit while the game ignored it.
- [ ] **Trait registered** in `media/registries.lua`.
- [ ] **No dead files**: delete files the engine ignores rather than leaving them beside the real ones.
- [ ] **`Contents/` holds only `mods`/`buildings`/`creative`** (lint).
- [ ] **Paths match case** for Linux servers.
- [ ] **One id per folder**; no duplicate ids across folders in the item (lint).

## Behaviour mistakes

- [ ] **State, not transitions.** Fire once on the change ("zombie just spotted you"), with a cooldown,
      not every tick while the state holds.
- [ ] **Dead objects skipped** (corpses keep stale targets).
- [ ] **Outlines/highlights cleared** on every exit path (pooled objects keep flags).
- [ ] **Unloaded squares** never touched.
- [ ] **Game time vs real time** chosen deliberately.
- [ ] **Per-frame work throttled** and cached.
- [ ] **Restart and relog** tested for anything with ongoing state.
- [ ] **Stereo audio** converted to mono for 3D (lint warns on WAV).

## Honesty and process

- [ ] **"Tested" means run.** Say what ran (specs, rig boot, which in-game steps) and what did not.
      Untested paths go into README "Known limits" and the user gets smoke-test steps.
- [ ] **No overclaiming** in descriptions: "compatible with everything", "zero performance impact".
- [ ] **Numbers agree** across mod.info, workshop.txt, README, sandbox defaults and code.
- [ ] **Licences verified** for every sound, model, image and font shipped. Audio named like a stock
      library is not proof of a licence. If unverified, replace with vanilla sounds or the user's own.
- [ ] **No copied code** from other mods; patterns and ideas only, credited when distinctive.
- [ ] **No private data** in the repo, screenshots, logs or Workshop text (lint scans text files).
- [ ] **No test rig output committed** (`.testserver/`, `.testclient*/`, `*.out` gitignored).
- [ ] **AI attribution** matches the user's preference (no unasked tool footers or co-author trailers).
- [ ] **Prose reads human** (see the tells table in workshop-description.md).
- [ ] **Scope held.** Built what was asked; extras proposed, not shipped.
- [ ] **Asked before** pushing, uploading, or touching a live server.
