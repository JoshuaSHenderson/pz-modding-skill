# Community patterns (what working B42 mods actually do)

Survey of the 273 mods (221 Workshop items, 7208 Lua files) installed on the reference PC, plus the PZ
wiki modding pages (revised for 42.21-42.22). Counts are "mods using it". Use these as the default
idioms; when you need something not here, find a mod that does it in
`<steam>/steamapps/workshop/content/108600/` and read how (learn the method, never copy the code).

## Sources of truth (PZ wiki), most to least trustworthy

1. Game files: vanilla `media/lua`, `media/scripts`, the decompiled jar.
2. Generated API docs: JavaDocs, LuaDocs, PZ API docs (generated from the game, small manual errors).
3. The modding wiki and the modding Discords (fast, sometimes stale: check the page's version banner).
4. Other people's guides (Steam, GitHub, YouTube): go stale when the author leaves.
5. The official forums: archaic.
6. LLMs: "should not be trusted" for API facts; they hallucinate methods and repeat B41 knowledge.

## Tooling the community uses

- **VS Code** with **Umbrella** (EmmyLua/LuaLS type stubs for the whole PZ Lua API: autocomplete and
  "method does not exist" diagnostics catch most hallucinated calls before the game does),
  **ZedScripts** (script file syntax and diagnostics) and **PZ Modding Configs** (defaults for both).
- Translation JSON schemas from the `pz-wiki-modding/pz-translation-data` repo, linked per file with
  `"$schema"` or in `.vscode/settings.json`, validate key prefixes.
- IntelliJ IDEA for reading decompiled Java.
- **Debug mode**: launch with `-debug`. Main menu gets **Reset Lua** (reloads client + shared Lua without
  restarting the game); in game F11 is the Lua debugger, plus debug context menus to spawn items,
  teleport and inspect. Errors show as red counters. `scripts/test-client.sh` takes `RIG_DEBUG=1`.

## Hooking vanilla (decorating), not overwriting

39 mods wrap vanilla functions; the wiki "HIGHLY recommends" it over replacing files. The shape:

```lua
local original_render = ISInventoryPage.render
function ISInventoryPage:render(...)
    local result = original_render(self, ...)   -- always call through, pass self and all args
    -- your extra drawing here
    return result                               -- keep the original's return value
end
```

- Run your code before or after, or short-circuit only for your own case; otherwise always call through,
  so other mods hooking the same function keep working.
- Hook at file load (after `require` of the vanilla file if it lives in a module) or in `OnGameBoot`.
- Most hooked: `ISInventoryPage.prerender/createChildren/render`, `ISInventoryTransferAction.new/isValid`,
  `ISWorldMap.render`, `ISHotbar.*`, `ISToolTipInv.render`, `ISCharacterInfoWindow.createChildren`.
- Java methods can be hooked only for calls made from Lua (PZ wiki, Lua (API)):
  `local index = __classmetatables[IsoPlayer.class].__index; local old = index.getX; function index:getX(...) return old(self, ...) end`.
  Calls made Java-side never see it.
- Overwriting a whole vanilla file is a last resort for compatibility; it breaks every other mod that
  hooks or overwrites the same file.

## Classes: derive

`ISPanel` (153 mods), `ISBaseTimedAction` (137), `ISBaseObject` (62), `ISUIElement` (53),
`ISPanelJoypad` (47), `ISCollapsableWindow` (35), `ISBuildingObject` (20), `ISButton`.

```lua
MyMod_Window = ISCollapsableWindow:derive("MyMod_Window")
```

## Timed actions (B42)

Vanilla B42 keeps timed actions in `media/lua/shared/TimedActions/` and 139 of its 143 define
`complete()`. Only 24 of the 273 installed mods do, so many mods' actions are B41-shaped and unreliable
in B42 multiplayer.

```lua
-- media/lua/shared/TimedActions/MyMod/MyMod_FixThing.lua
require "TimedActions/ISBaseTimedAction"
local MyMod_FixThing = ISBaseTimedAction:derive("MyMod_FixThing")  -- prefixed Type

function MyMod_FixThing:isValid() return self.character:getInventory():contains(self.item) end
function MyMod_FixThing:start() self:setActionAnim("Loot") end       -- client: anims, sounds (vanilla's most used anim)
function MyMod_FixThing:stop() ISBaseTimedAction.stop(self) end
function MyMod_FixThing:perform()                                    -- client: visuals, then finish
    ISBaseTimedAction.perform(self)
end
function MyMod_FixThing:complete()                                   -- the actual world change:
    self.item:setCondition(self.item:getConditionMax())              -- runs on the server in MP,
    return true                                                       -- locally in SP
end
function MyMod_FixThing:getDuration() return 100 end
function MyMod_FixThing:new(character, item)
    local o = ISBaseTimedAction.new(self, character)
    o.item = item
    o.maxTime = o:getDuration()
    return o
end

_G[MyMod_FixThing.Type] = MyMod_FixThing  -- since 42.13 actions must be global to work in MP
return MyMod_FixThing
-- queue it: ISTimedActionQueue.add(MyMod_FixThing:new(player, item))
```

- Since 42.13 (wiki) timed actions must be reachable globally by their `Type` for multiplayer. Prefix
  the Type with the mod name so globals do not collide.
- World changes go in `complete()`, not `perform()`. Vanilla also uses `serverStart()` / `serverStop()`
  for server-side work at start and on cancel.
- In `new`, guard client-only lookups with `if not isServer() then ... end` (the server builds the
  action too). Constructor arguments must be things the server can resolve (player, items, objects).
- Read two vanilla actions close to yours (`ISEatFoodAction`, `ISInventoryTransferAction`) before writing.

## Loot distributions

122 mods add loot. The idiom lives in `media/lua/server/`:

```lua
local function addLoot()
    local list = ProceduralDistributions.list
    table.insert(list["CrateTools"].items, "MyMod.Thing")
    table.insert(list["CrateTools"].items, 0.5)          -- weight follows the item
end
Events.OnPreDistributionMerge.Add(addLoot)              -- or plain file load in server/
```

`OnPreDistributionMerge` (17 mods) and `OnPostDistributionMerge` (47) are the hooks; many just insert at
file load. Distribution table names come from vanilla `media/lua/server/Items/ProceduralDistributions.lua`;
a misspelled table name errors at load.

## Global ModData sync

98 mods use `OnInitGlobalModData`, 61 `ModData.transmit`, 12 `OnReceiveGlobalModData` (an event the engine
fires; no vanilla Lua listens to it, so test the round trip on the rig).

```lua
-- server
Events.OnInitGlobalModData.Add(function() MyMod.data = ModData.getOrCreate("MyMod") end)
local function save() ModData.transmit("MyMod") end          -- push to all clients after a change
-- client
Events.OnReceiveGlobalModData.Add(function(key, data)
    if key ~= "MyMod" or type(data) ~= "table" then return end
    ModData.add("MyMod", data)
end)
Events.OnConnected.Add(function() ModData.request("MyMod") end) -- ask on join
```

Per-object data: `obj:getModData()` (144 mods), then `obj:transmitModData()` (30) to sync an object's
changes in MP.

## Scripts (items, recipes)

- B42 vanilla item scripts use `ItemType = base:normal` / `base:weapon` / `base:clothing` /
  `base:food` / ... and **never** B41 `Type = Normal` (vanilla: 0 uses; 1238 B41-style lines still sit in
  installed mods' B42 folders). Recipes are `craftRecipe` blocks (965 in vanilla, 0 old `recipe`).
- **Soft overrides**: redefining an existing `item` in your own module and file changes only the
  parameters you list; everything else is kept. Use that (or `ScriptManager.instance:getItem("Base.X")`
  + `DoParam("Weight = 2")` from Lua, 17 mods) instead of copying a vanilla script file, which overwrites
  every definition in it and clashes with every other mod that does the same.
- Keep script files at `media/scripts/MyMod/...` so the relative path is unique.
- Read the block's docs (wiki ScriptsDocs) to see whether it soft-overrides or replaces.

## Translations

Since 42.15 translation files are `media/lua/shared/Translate/<LANG>/<Type>.json` with **no language code
in the filename** (`UI.json`, not `UI_EN.json`). The jar reads only that pattern (`Translator`:
`%s/media/lua/shared/Translate/%s/%s.json`). 1146 `.txt` translation files sit in installed mods' B42
folders, ignored by the game: do not copy that pattern.

| File | Key prefix / key | Used by |
|---|---|---|
| `UI.json` | `UI_` | `getText` in UI |
| `IG_UI.json` | `IGUI_` | in-game UI text (most used by mods: 121) |
| `Sandbox.json` | `Sandbox_` | sandbox page, options, tooltips, `_optionN` |
| `ContextMenu.json` | `ContextMenu_` | right-click menus |
| `Tooltip.json` | `Tooltip_` | tooltips |
| `ItemName.json` | full item type, e.g. `MyMod.Thing` | item display names |
| `Recipes.json` | the `craftRecipe` id | recipe names |
| `Mod.json` | `name`, `description` | the mod list entry |
| `Moodles.json`, `Fluids.json`, `Farming.json`, `GameSound.json`, `Entity.json` (`EC_`) | see wiki "Translation" | |

The translator warns about "look-alike unicode" characters in EN text: keep EN strings ASCII (no
curly quotes, no em dashes).

## Context menus

`Events.OnFillWorldObjectContextMenu.Add(function(playerNum, context, worldObjects, test) ... end)`
(33 mods) and `OnFillInventoryObjectContextMenu(playerNum, context, items)` (21). Return early when
`test` is true. Get the player with `getSpecificPlayer(playerNum)`.

## Split-screen

Up to four local players share one client. 70 mods use `getSpecificPlayer(playerNum)`; code that uses
`getPlayer()` (87 mods) only ever sees player 1. Anything driven by an event that passes `playerNum` or
a player object should use that, and per-player state should be keyed by player number.

## Performance (PZ wiki "Mod optimization")

- "Don't need it? Don't run it": check cheap state before an expensive call (`if not z:isSkeleton() then
  z:setSkeleton(true) end` on `OnZombieUpdate`).
- `local` everything; cache globals you read often (`local ProceduralDistributions = ProceduralDistributions`).
- Cache objects you fetch repeatedly within a function or tick.
- `OnZombieUpdate`, `OnPlayerUpdate`, `OnTick`, `OnRenderTick` run constantly; throttle with
  `getTimestampMs()` (55 mods do) and remove one-shot handlers with `Events.X.Remove(fn)` (40 mods).
- Every Lua->Java call costs more than a Lua call; batch and cache.

## Versioning and libraries

- Version folders let one item serve several game builds (`42.0`, `42.13`, `42.20`, ...). Ship only the
  ones you actually test; a version folder you never ran is an untested mod.
- Libraries (damnlib, Gunworks framework, DOME) ship as their own Workshop item; depend on them with
  `require=` and list them on the Workshop page.

## Legal and community (PZ wiki "Modding")

- By modding you accept TIS's Modding Policy: you warrant the mod is your original work and every
  third-party asset is properly licensed. No paywalled or donor-only content; donations are fine.
- You own your mod by default. Reposting or "fixing" someone else's mod needs their permission (a
  licence that allows it, or a direct yes); for abandoned mods, try to reach the author and tell the
  Steam moderators first. Ship a patch mod that depends on theirs instead of a repost.
- License your own mod explicitly (LICENSE file, or TIS's BBCode licence templates: Free-For-All,
  Credit where it's due, Ask For Permission, On Lockdown).
- Feeding someone else's mod to an AI and publishing the output is treated as theft by the community.
