---
name: pz-modding
description: The go-to workflow for building Project Zomboid Build 42 mods end to end - scaffolding the Workshop layout, writing Lua that the real engine accepts, checking every Java call against the game jar, unit specs, isolated local dedicated servers and clients for multiplayer testing, Workshop descriptions, preview images and screenshots, and the release checklist. Use whenever the user wants to create, fix, test, document, package or publish a Project Zomboid mod (traits, sandbox options, UI, sounds, events, vehicles, server-side systems), mentions mod.info, workshop.txt, Kahlua, B42, Steam Workshop for Zomboid, or asks to spin up a PZ test server.
---

# Project Zomboid Modding (Build 42)

A mod is done when it **loads, works in the real game, and says honestly what it does**. Most broken
PZ mods are not broken by hard bugs: they are broken by a missing `mod.info`, a file format the engine
never reads, or a Java method that does not exist. All three fail **silently**. This skill exists to
catch those before a player does.

## The loop

Follow it in order. Each phase has a reference file; read it when you reach that phase.

| # | Phase | Read | Exit check |
|---|---|---|---|
| 1 | Scope: what the mod does, which side (client / server / shared), SP and/or MP | this file | One-paragraph spec the user agrees with |
| 2 | Scaffold the Workshop-shaped repo | [references/layout-and-metadata.md](references/layout-and-metadata.md) | `python scripts/check_mod.py <ItemFolder>` passes |
| 3 | Find how vanilla and working mods do it, then write the code | [references/verify-against-game.md](references/verify-against-game.md), [references/community-patterns.md](references/community-patterns.md), [references/b42-api-gotchas.md](references/b42-api-gotchas.md) | Every engine call verified (name **and** signature) |
| 4 | Test: specs, local rig, in-game checklist | [references/testing.md](references/testing.md) | Specs pass, mod boots clean on the rig, checklist done or listed as untested |
| 5 | Art: preview, icons, screenshots | [references/images.md](references/images.md) | `preview.png` 256x256 < 1 MB, icons at engine sizes |
| 6 | Words: Workshop description, README, changelog | [references/workshop-description.md](references/workshop-description.md) | Under 8000 chars, no AI tells, claims match tests |
| 7 | Release | [references/release.md](references/release.md) | Versions bumped everywhere, upload folder matches repo |

Before handing anything back, run the [AI pitfalls checklist](references/ai-pitfalls.md). It is the list
of mistakes that actually shipped (or nearly shipped) in real mods, with the fix for each.

## Non-negotiables

1. **Verify, never assume, the engine API.** Grep vanilla Lua under `<game>/media/lua/` and decompile
   `projectzomboid.jar` for Java classes. A call that "looks right" is the single biggest source of
   AI-written PZ bugs. Record how you checked in a comment when it is not obvious.
   The [PZ wiki modding pages](https://pzwiki.net/wiki/Modding) are the community's reference (check each
   page's version banner); Umbrella type stubs in VS Code flag invented calls as you type.
2. **`pcall` does not make a Java call safe.** A missing Java method throws through the Lua bridge
   and `pcall` does not catch it. Don't wrap calls to look defensive; verify them.
3. **Kahlua is not Lua 5.1.** No `next()`, no `goto`, limited stdlib, Java objects not tables. See
   the gotchas file.
4. **Build 42 formats only.** Translations are `Translate/EN/*.json`; traits are script objects plus
   `media/registries.lua`. B41 tutorials and forum posts are usually wrong for B42.
5. **B42 layout.** `common/` plus a version folder (`42/`) holding `mod.info`, `poster.png` and the code,
   and a root `mod.info` copy. A mod shipped as only `42/mod.info` never appeared in the list, with no
   error anywhere.
6. **Test in an isolated home.** Never test with `ProjectZomboidServer.bat` or against the user's real
   `~/Zomboid`: use `scripts/test-server.sh` (it points `user.home` at a throwaway folder).
7. **Say what was not tested.** If a path was never run in game, the README and your reply say so,
   and you ask the user for a smoke test. "Should work" is not a test result.
8. **Server authority in MP.** The server re-checks admin rights and validates every client payload.
   Never trust `args` from `OnClientCommand`.
9. **No private data in a public repo or Workshop page**: no local IPs, usernames, home paths, server
   passwords, emails, or raw logs (logs contain all of those). Test rig folders are gitignored.
10. **Credits and licences are checked before publishing.** Third-party models, sounds and images need
    a licence that allows redistribution, recorded in the README/Workshop text. Unverified = do not ship.
11. **Decorate, don't overwrite.** Wrap vanilla functions (call the original, return its result) and
    soft-override script blocks; never ship a copy of a vanilla file to change one thing. Every file sits
    under a folder named after the mod.
12. **Gameplay settings are sandbox options.** ModOptions are per-PC UI preferences only.

## Quick start (new mod)

```bash
python scripts/scaffold.py MyMod "My Mod" --author "Your Name"   # creates ./ProjectZomboid-MyMod/
cd ProjectZomboid-MyMod && git init
python ../pz-modding-skill/scripts/check_mod.py MyMod           # structural lint
```

Then write the code (phase 3), and boot it:

```bash
PZ_GAME="/c/Program Files (x86)/Steam/steamapps/common/ProjectZomboid" MOD=MyMod bash scripts/test-server.sh
```

## Deciding where code goes

| Folder | Runs on | Use for | First line |
|---|---|---|---|
| `media/lua/shared/` | client, server, SP | data, definitions, pure logic you can unit test | none |
| `media/lua/client/` | clients and SP | UI, input, rendering, sounds, ModOptions | `if isServer() then return end` when it must never run on a server |
| `media/lua/server/` | server and SP host | world changes, spawning, authority, ModData | `if isClient() then return end` |

Put pure logic (validation, maths, schedules, status resolution) in `shared/` modules with no engine
calls at load time, so a plain Lua interpreter can run specs against them. That one choice is what made
the larger reference mods testable.

## Talking to the user

- Show the plan (phase 1) before writing a big mod; small fixes just go.
- When a fact comes from the jar or vanilla Lua, say so; when it is a guess, say that instead and add a
  debug switch so the user can check it in one step (see "unverified constants" in the pitfalls file).
- End every build with: what was tested and how, what was not, and the exact in-game steps for the
  user's smoke test.
- Ask before: pushing to GitHub, uploading to the Workshop, or touching a live server.
