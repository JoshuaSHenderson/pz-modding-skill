# Build 42 Lua and engine gotchas

Each item here cost a real mod a release, a crash report or a day of debugging.

## Kahlua (PZ's Lua)

| Gotcha | Do instead |
|---|---|
| **No `next()`.** Calling it errors every tick. `next(t) == nil` is the usual AI way to test empty. | `local function empty(t) for _ in pairs(t) do return false end return true end` |
| `pcall` does **not** catch a missing / wrong-signature Java method. The trace even points at the `pcall` line. | Verify the call against the jar. Use `pcall` only around your own Lua that may error. |
| Static Java methods called on an instance return "tried to call nil" (`getCore():getTileScale()`). | Call on the class: `Core.getTileScale()`. |
| Java collections are not Lua tables. `#list` and `ipairs(list)` do not work on `ArrayList`. | `for i = 0, list:size() - 1 do local x = list:get(i) end` |
| Java numbers and strings come back as Lua values, but Java `null` is `nil` and an empty Java string is not `nil`. | Check both where it matters. |
| Integer division, `string.format("%d", 1.5)` and some `os`/`io` functions behave differently or are missing. | Use `math.floor`, test in game, prefer `getFileWriter` / `getFileReader` for files. |
| Globals are shared across **all** mods. | `local` everything; one global table per mod (`MyMod = MyMod or {}`). |

## Build 42 vs Build 41

| B41 (do not use) | B42 |
|---|---|
| `Translate/EN/UI_EN.txt` Lua-table files | `Translate/EN/UI.json`, `Sandbox.json`, ... The engine only reads `media/lua/shared/Translate/<LANG>/<Name>.json`. A `.txt` file sits there ignored and every label shows its raw key. |
| `TraitFactory.addTrait(...)` | Trait is a script object `character_trait_definition mymod:mytrait` in `media/scripts/`, **plus** `media/registries.lua` calling `CharacterTrait.register("mymod:mytrait")`. Without the registration the script is dropped at load with `NullPointerException ... "this.characterTraitType" is null` and the mod silently does nothing. |
| `player:HasTrait("Name")` (string) | `player:hasTrait(CharacterTrait)` with the registered object; store it from `registries.lua` (`MyMod.TRAIT = CharacterTrait.register(...)`). |
| `setRunSpeedModifier`, `setInfectionLevel` | Removed. Movement buffs via trait `XPBoosts = Fitness=2;Sprinting=3`; infection via `getBodyDamage():setInfected(true)`. |
| Mod content at `media/` in the mod root | Content in `42/media/`; `mod.info` at root and in `42/`. |

Translation text style: vanilla trait descriptions are two or three clipped mechanical lines joined by
`<br>` ("Faster running speed.<br>Can run for longer without tiring."). Match it.

## Client / server / multiplayer

- `isClient()` is true on an MP client, `isServer()` on a dedicated server or host; both false in SP.
  SP runs client **and** server folders in one Lua state.
- Client -> server: `sendClientCommand(player, "MyMod", "cmd", args)`; server listens on
  `Events.OnClientCommand.Add(function(module, command, player, args) ... end)`.
- Server -> client: `sendServerCommand("MyMod", "cmd", args)` (all) or `sendServerCommand(player, "MyMod", "cmd", args)`;
  client listens on `Events.OnServerCommand`. In SP these server commands do **not** reach your client
  code, so an MP-only feature must say so.
- Always check `module == "MyMod"` first, then `type(args) == "table"`, then validate every field (types,
  ranges, known ids). Re-check admin on the server: `player:getAccessLevel()` lowercased equals `"admin"`.
- Rate-limit anything a client can spam (one reply per player per few seconds).
- An empty table sent over the network may arrive as `nil`.
- Every player needs the same mod files as the server; a mismatch blocks joining. Restart the server
  after any Lua change before testing with clients.

## Persistence

- `ModData.getOrCreate("MyMod")` (global) or `obj:getModData()` (per object) saves with the world.
  Store **plain values only**: numbers, strings, booleans, tables of those. Never Java objects
  (squares, zombies, players, items) or functions; store coordinates and ids and look them up again.
- Global ModData is ready in `Events.OnInitGlobalModData`, not at file load.
- After a restart, Lua locals, closures, pending deferred jobs and zombie references are gone. Anything
  an ongoing system needs must be rebuildable from saved data. Test a restart mid-feature.
- Removing a mod from a server's `Mods=` while its items are in the save deletes those items from every
  container permanently. Say so in the README if the mod adds items.

## World and objects

- Never touch a square that is not loaded: `getCell():getGridSquare(x, y, z)` can return `nil`.
  The server cannot see unloaded ground; defer until a player is near.
- Objects are **pooled and reused** (trees especially). Flags you set on one (outline, highlight) can
  show up on a "different" object later. Clear what you set, every time.
- `setHighlighted` on trees renders only one tree per frame (a static on `IsoTree`); outlines via
  `setOutlineHighlight(playerNum, true)` + `setOutlineHlAttached`.
- A-Life-style NPC mods implement NPCs as zombie shells: they are in `getCell():getZombieList()`.
  Filter by their mod data before treating every zombie as a zombie.
- Zombie counts you spawn: batch across ticks and cap them; a single huge spawn stalls the server.

## Ticks and performance

- `Events.OnTick` runs every frame. Throttle scans (`getTimestampMs()` gate, 4-6 times a second is
  plenty for UI marks) and cache per-object results for a few hundred ms.
- `EveryOneMinute` is game minutes: its real-time rate depends on the server's day length. Use real
  clock (`getTimestampMs()` / `os.time()`) for anything the player feels in seconds, and ignore huge
  frame gaps (pause, loading).
- Do not rebuild UI lists or re-wrap text every frame.

## Sound

- Sound scripts: `media/scripts/<mod>_sounds.txt`, `module MyMod { sound MySound { category = Zombie,
  is3D = true, clip { file = media/sound/MyMod/x.wav, distanceMin = 15, distanceMax = 75, } } }`.
- **3D sound must be mono.** FMOD only positions mono clips; a stereo file plays flat at full volume
  wherever the source is.
- `volume` is capped at 1.0. Loudness comes from the file's level (normalise, soft-clip) and
  `distanceMin` (full volume inside it, no falloff).
- Fade in 5-10 ms and out a few hundred ms; a hard cut clicks.
- Redefining a vanilla sound name in `module Base` replaces it everywhere the engine plays it.
- Pick `category` so the player's volume slider applies.
- Play from Lua: `obj:getEmitter():playSound("MySound")` (zombies) or `player:playSound("MySound")`.

## Java mods

Lua cannot reach everything (e.g. another mod's projection matrix). A small Java bridge loaded by a
loader mod (ZombieBuddy) works, but: the player must approve each jar, a game update can break the
loader, and internals you reflect into can be renamed. Ship it as an **optional sub-mod**, hide the
feature (never draw it wrong) when the bridge is missing, and log one clear line saying why. Build with
the game's JRE and the Eclipse compiler (`ecj`) when there is no JDK; a jar is a zip.

## Logs worth knowing

| Where | What |
|---|---|
| `~/Zomboid/console.txt` | Client and SP log, current session. First place to look. |
| `~/Zomboid/Logs/` | Dated DebugLogs, chat, connections. A server keeps only the current `*DebugLog-server.txt`; copy it aside before restarting if you need a baseline. |
| Server stdout | The rig scripts capture it to a `.out` file. |
| `SERVER STARTED` | The real "dedicated server is ready" marker. |

Prefix every print with your mod tag (`print("[MyMod] ...")`) so you can grep it. Harmless noise you
will see: `NoSuchFileException` for `AnimSets`/`actiongroups` folders at mod load.
