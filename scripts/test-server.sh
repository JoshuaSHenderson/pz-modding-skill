#!/usr/bin/env bash
# Boots an isolated Project Zomboid B42 dedicated server with your mod, from the mod repo root.
# The server's user.home is a throwaway folder, so it can never touch your real ~/Zomboid.
# NEVER test with ProjectZomboidServer.bat: it ignores arguments and runs on the real ~/Zomboid.
#
#   MOD=MyMod [ITEM=MyMod] [PZ_GAME=...] [DEPS="<wsid>/mods/<ModId> ..."] [SELFTEST=tests/selftest.lua] \
#     bash test-server.sh > .testserver.out 2>&1
#
# MOD      mod id and folder name under <ITEM>/Contents/mods/ (required)
# ITEM     Workshop item folder in the repo (default: $MOD)
# PZ_GAME  game install (default: Steam's default library)
# DEPS     Workshop dependencies, copied fresh from steamapps/workshop/content/108600 every boot
# SELFTEST a Lua file copied into the rig copy's lua/server/ only, for in-engine checks
# RIG_HOME throwaway home (default: ./.testserver)    RIG_PASS admin password (default: rigtest)
# RIG_MEM  server heap (default: 3072m). (-debug is client-only; the dedicated server rejects it.)
# Windows + Git Bash. Ready when the output contains "SERVER STARTED".
set -e
: "${MOD:?set MOD to your mod id}"
ITEM="${ITEM:-$MOD}"
SRC="$ITEM/Contents/mods/$MOD"
[ -d "$SRC" ] || { echo "no $SRC - run from the repo root" >&2; exit 1; }
GAME="${PZ_GAME:-/c/Program Files (x86)/Steam/steamapps/common/ProjectZomboid}"
[ -f "$GAME/projectzomboid.jar" ] || { echo "game not found at $GAME - set PZ_GAME" >&2; exit 1; }
WS="${PZ_WORKSHOP:-$GAME/../../workshop/content/108600}"
HOME_DIR="${RIG_HOME:-$PWD/.testserver}"
CACHE="$HOME_DIR/Zomboid"
NAME=RigTest
mkdir -p "$CACHE/mods" "$CACHE/Server"

rm -rf "${CACHE:?}/mods/$MOD"
cp -r "$SRC" "$CACHE/mods/"
if [ -n "$SELFTEST" ]; then
  mkdir -p "$CACHE/mods/$MOD/42/media/lua/server/$MOD"
  cp "$SELFTEST" "$CACHE/mods/$MOD/42/media/lua/server/$MOD/ZZSelfTest.lua"
fi

MODS="$MOD"
for d in $DEPS; do
  [ -d "$WS/$d" ] || { echo "missing $WS/$d - subscribe in Steam first" >&2; exit 1; }
  b="$(basename "$d")"
  rm -rf "${CACHE:?}/mods/$b"
  cp -r "$WS/$d" "$CACHE/mods/"
  MODS="$b;$MODS"   # dependencies load first
done
echo "Mods=$MODS"

INI="$CACHE/Server/$NAME.ini"
if [ -f "$INI" ]; then
  sed -i "s/^Mods=.*/Mods=$MODS/" "$INI"
else
  printf 'Mods=%s\nOpen=true\nPublic=false\nPauseEmpty=true\n' "$MODS" > "$INI"
fi

W_HOME="$(cygpath -w "$HOME_DIR")"
cd "$GAME"
# Flags mirror the game's own server launcher JSON. If a game update changes them, copy the new ones from
# ProjectZomboid64.json / the server .bat (jvm args and classpath), keeping user.home and -cachedir.
exec ./jre64/bin/java.exe --enable-native-access=ALL-UNNAMED \
  --add-exports=java.base/jdk.internal.misc=ALL-UNNAMED \
  -XX:+UseZGC -XX:-CreateCoredumpOnCrash -XX:-OmitStackTraceInFastThrow "-Xmx${RIG_MEM:-3072m}" \
  "-Duser.home=$W_HOME" "-Ddeployment.user.cachedir=$W_HOME\\Zomboid" \
  "-Djava.library.path=./natives/;./natives/win64/;./" \
  -cp "./;projectzomboid.jar" zombie.network.GameServer \
  -nosteam "-cachedir=$W_HOME\\Zomboid" -servername "$NAME" -adminpassword "${RIG_PASS:-rigtest}" </dev/null
