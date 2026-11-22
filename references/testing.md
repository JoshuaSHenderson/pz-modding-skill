# Testing

Three layers. Do all that apply, and report which ran.

| Layer | Catches | Cost |
|---|---|---|
| 1. Plain-Lua specs | logic bugs in pure modules (validation, maths, status resolution, filters) | seconds |
| 2. Isolated local server (+ self-test) | load errors, wrong API, server-side behaviour, MP sync, restarts | 1-3 minutes per boot |
| 3. In-game checklist | anything visual, audio, UI, feel; the real mod list | the user's time |

`python scripts/check_mod.py <ItemFolder>` runs before all of them: it catches the silent packaging
failures (missing root `mod.info`, B41 translation files, `next(`, oversized preview) in a second.

## 1. Plain-Lua specs

Any Lua 5.1-compatible interpreter works: `lua`, `luajit`, or with neither installed
`python -c "import lupa; lupa.LuaRuntime().execute(open('tests/spec.lua').read())"`
(`pip install lupa`), or LuaJ on the game's own Java.

Pattern: stub only the globals the module touches, load the real file, assert.

```lua
-- tests/spec.lua   run from repo root: lua tests/spec.lua
next = nil                                   -- PZ has no next(); make the spec fail like the game would
function isClient() return false end
function isServer() return false end
Events = setmetatable({}, { __index = function() return { Add = function() end } end })

local MOD = "MyMod/Contents/mods/MyMod/42/media/lua/"
package.path = MOD .. "shared/?.lua;" .. package.path
local Logic = require "MyMod/Logic"

local n = 0
local function check(name, got, want)
    n = n + 1
    if got ~= want then error(name .. ": got " .. tostring(got) .. ", want " .. tostring(want), 2) end
end

check("clamps high", Logic.clamp(500), 200)
check("rejects junk", (Logic.validate({ count = "x" })), false)
print(n .. " checks passed")
```

Tips:

- Set `next = nil` at the top so a stray `next()` fails in the spec, not on a player's server.
- A fake player is a table with the methods you call: `{ getUsername = function() return "a" end }`.
  `setmetatable(player, { __index = function() return function() return nil end end })` makes every
  other method return nil.
- Write the spec for a bug before fixing it; check the spec fails with the fix reverted (a spec that
  passes either way tests nothing).
- UI and rendering are not worth stubbing. Test them in game.

## 2. Isolated local dedicated server

`scripts/test-server.sh` boots a real dedicated server from the game install with:

- `-Duser.home` pointed at a throwaway folder (`.testserver/` in the repo), so it **cannot** touch the
  user's real `~/Zomboid` saves, mods or server configs,
- `-nosteam`, so no Steam login is needed and clients join by IP,
- a fresh copy of your mod (and any Workshop dependencies) copied in on every boot, so the rig never
  runs stale files,
- a generated `<name>.ini` with `Mods=`, `Open=true`, `Public=false`, and an admin password.

```bash
# from the mod repo root (Git Bash on Windows)
PZ_GAME="/c/Program Files (x86)/Steam/steamapps/common/ProjectZomboid" MOD=MyMod bash scripts/test-server.sh > .testserver.out 2>&1 &
# with Workshop dependencies (folders under steamapps/workshop/content/108600)
DEPS="3803984183/mods/ProjectALifeNPCs" MOD=MyMod bash scripts/test-server.sh
# wait for ready
until grep -q "SERVER STARTED" .testserver.out; do sleep 5; done
grep -n "\[MyMod\]\|ERROR\|Exception" .testserver.out | head -50
```

Debug mode: `RIG_DEBUG=1 bash scripts/test-client.sh 1` adds `-debug` to a client (the dedicated server
logs `unknown option "-debug"` and ignores it, so the server script does not pass it). On the client that gives the F11 Lua
debugger, debug context menus (spawn items, teleport) and **Reset Lua** on the main menu, which reloads
client and shared Lua without restarting the game. Server-side Lua still needs a server restart.

**Never use `ProjectZomboidServer.bat` for testing.** It ignores arguments and starts the default
`servertest` on the real `~/Zomboid`.

Joining it:

```bash
bash scripts/test-client.sh 1     # user admin / password from RIG_PASS (default: rigtest)
bash scripts/test-client.sh 2     # second player, any other name - for MP sync tests
```

Each client gets its own throwaway home (`.testclient1/`, `.testclient2/`) and a copy of the server's
mods. Join with **IP 127.0.0.1, port 16261**. Two clients on one PC need RAM: about 3 GB for the server
and 4 GB per client.

Before every rig session:

- Stop the rig server after any Lua change; clients must match its files.
- Unsubscribe from (or delete the local `~/Zomboid/Workshop/<Item>` copy of) the mod under test in the
  real profile if you also test outside the rig: a stale Workshop copy with the same mod id can win
  over `~/Zomboid/mods`.
- Keep the rig folders gitignored; they fill with logs that contain names and IPs.

### In-game self-test (optional, strong)

For server logic that needs real engine objects, ship a test file only into the rig copy:

```bash
SELFTEST=tests/selftest.lua MOD=MyMod bash scripts/test-server.sh > .testself.out 2>&1
grep "\[MyMod-TEST\]" .testself.out
```

`selftest.lua` runs at server start inside real PZ Lua (`if isClient() then return end`, then call your
functions with a fake player table, `print("[MyMod-TEST] FAIL ...")` on mismatch and a final
`pass/fail` count line). The script copies it into the rig's `lua/server/` folder only; it never
enters the repo's mod folder or the Workshop upload.

## 3. In-game checklist

Write it for the user as numbered steps with the expected result after each. Cover, as they apply:

- [ ] Mod appears in the mod list with its poster; enabling it gives no error popup.
- [ ] Played with `-debug`: no red error counter appears in the corner while using the feature.
- [ ] `console.txt` has no `[MyMod]` errors and no stack trace mentioning the mod's files.
- [ ] Every sandbox option label and tooltip shows real text (not raw keys); every value changes behaviour.
- [ ] Every ModOptions entry (Options > Mods) saves and applies.
- [ ] Feature works in **singleplayer** (if supported).
- [ ] Feature works on the **rig server** with two clients: both see it, the non-admin cannot do admin
      things (send the admin command by hand from client 2 and check the server rejects it).
- [ ] **Restart** the server mid-feature: nothing duplicates, nothing is lost, no orphaned objects.
- [ ] **Relog** mid-feature: state comes back.
- [ ] **Add to an existing save** and **remove from a save** (if the README claims it is safe).
- [ ] Disabled / zero / max values of every option.
- [ ] Sounds: positional (walk around the source), right volume slider, no clicks.
- [ ] Performance: no stutter with many zombies on screen (watch FPS with the feature on and off).
- [ ] With the real mod list the user plays with, if they have one.

Anything not run goes into the README "Known limits" and your reply as **untested**.

## Testing on a real server

Only with the user's go-ahead. Back up the world first. A dedicated server rewrites its
`<name>.ini` on boot and shutdown, so ini edits made while it runs are lost: stop, edit, start, then
check the value again after boot. Mod changes need a server restart and the same files on every client.
