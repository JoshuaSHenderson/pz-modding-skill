# Verify against the game, not memory

Model knowledge of PZ is mostly Build 41 and forum lore. Build 42 renamed, removed and re-signatured a
lot. Every engine call you write has to be checked against the installed game.

## Sources, in order of trust

1. **The jar** - `<game>/projectzomboid.jar` (B42 ships classes in the jar; older installs had a
   `zombie/` class tree). This is the truth for Java methods exposed to Lua.
2. **Vanilla Lua** - `<game>/media/lua/{client,server,shared}`. The best examples of idioms, event
   names, UI classes, timed actions and context menus. If vanilla does the thing you want, copy the
   *pattern* (write your own code).
3. **Vanilla scripts and data** - `<game>/media/scripts/` (items, sounds, vehicles, traits),
   `<game>/media/lua/shared/Translate/EN/*.json` (translation format).
4. **Installed Workshop mods** - `<steam>/steamapps/workshop/content/108600/<id>/mods/`. Good for
   "does any B42 mod do X this way" (e.g. how many ship a root `mod.info`, what sandbox syntax works).
   Never copy their code; credit if you borrow an idea that is distinctive.
5. Wikis, forum posts, AI memory: leads only. Verify before use.

`<game>` is usually `C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid` (or another
Steam library). Ask the user if it is not there.

## Decompiling the jar (no JDK needed)

The game ships its own Java runtime. Use it to run CFR:

```bash
GAME="/c/Program Files (x86)/Steam/steamapps/common/ProjectZomboid"
mkdir -p work/cfr && cd work/cfr
curl -LO https://github.com/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar
# one class
"$GAME/jre64/bin/java.exe" -jar cfr-0.152.jar "$GAME/projectzomboid.jar" \
    --jarfilter 'zombie\.characters\.IsoZombie$' --outputdir out
# grep a method's exact signature
grep -n "public .* getSpeedType\|public .* isTargetVisible" out/zombie/characters/IsoZombie.java
```

Put the decompiled output in a scratch folder outside the repo. **Never commit decompiled game code.**

Quick checks without a full decompile:

```bash
unzip -l "$GAME/projectzomboid.jar" | grep -i 'IsoTree'          # does the class exist, where
grep -rn "setOutlineHighlight" "$GAME/media/lua" | head          # how vanilla calls it
grep -rn "Events\.OnPlayerUpdate" "$GAME/media/lua" | head       # is the event real
```

## What "verified" means

For every Java call in the mod:

- the **class** has the method,
- the **argument count and types** match an overload (passing `0.6` to a no-arg method fails exactly
  like a missing method),
- it is an **instance** method if you call it with `:` on an object, or **static** if you call it on
  the class (`Core.getTileScale()`),
- it exists in the **oldest build** in `versionMin`.

For every event (`Events.X.Add`): vanilla Lua uses it, or `LuaEventManager` in the jar registers it.
A misspelled event name is `nil` and errors at file load.

Write the check down when it is not obvious:

```lua
-- verified against 42.21 IsoZombie: getSpeedType()I, getTarget(), isTargetVisible()Z
```

## Unverifiable values

Some things can only be confirmed in a running game (an enum's numeric value, which object a sprite
belongs to). Do not guess silently. Make it one constant at the top of the file, add a `DEBUG` flag
that prints what the game reports, and tell the user the exact step to check it:

```lua
local DEBUG = false
local SPRINTER_SPEED_TYPE = 1 -- sandbox enum order; if sprinters stay silent set DEBUG and read the log
```
