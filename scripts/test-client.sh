#!/usr/bin/env bash
# Launches one isolated B42 game client for the rig server (scripts/test-server.sh). From the mod repo root.
#   bash test-client.sh 1     # join as admin / $RIG_PASS (default rigtest)
#   bash test-client.sh 2     # second player, any other username and password
# Each client has its own throwaway home (.testclientN) with a copy of the server's mods; never the real ~/Zomboid.
# Join: IP 127.0.0.1, port 16261. Restart the server after any Lua change so files match.
# RIG_DEBUG=1 adds -debug (F11 Lua debugger, Reset Lua on the main menu).
# Java-mod loaders (e.g. ZombieBuddy) need their agent flag: AGENT="-agentlib:zbNative".
set -e
case "$1" in [1-9]) N="$1" ;; *) echo "usage: $0 N   (N = 1..9)" >&2; exit 1 ;; esac
GAME="${PZ_GAME:-/c/Program Files (x86)/Steam/steamapps/common/ProjectZomboid}"
SERVER_HOME="${RIG_HOME:-$PWD/.testserver}"
HOME_DIR="$PWD/.testclient$N"
[ -d "$SERVER_HOME/Zomboid/mods" ] || { echo "start scripts/test-server.sh first" >&2; exit 1; }
mkdir -p "$HOME_DIR/Zomboid/mods"
rm -rf "${HOME_DIR:?}/Zomboid/mods/"*
cp -r "$SERVER_HOME/Zomboid/mods/"* "$HOME_DIR/Zomboid/mods/"
W_HOME="$(cygpath -w "$HOME_DIR")"
echo "Join 127.0.0.1:16261 as $([ "$N" = 1 ] && echo "admin / ${RIG_PASS:-rigtest}" || echo 'any other username')"
cd "$GAME"
# shellcheck disable=SC2086
exec ./jre64/bin/java.exe $AGENT --enable-native-access=ALL-UNNAMED \
  --add-exports=java.base/jdk.internal.misc=ALL-UNNAMED \
  -XX:+UseG1GC -XX:-CreateCoredumpOnCrash -XX:-OmitStackTraceInFastThrow "-Xmx${CLIENT_MEM:-4096m}" \
  "-Duser.home=$W_HOME" "-Ddeployment.user.cachedir=$W_HOME\\Zomboid" \
  "-Djava.library.path=win64/;." \
  -cp ".;projectzomboid.jar" zombie.gameStates.MainScreenState \
  -nosteam ${RIG_DEBUG:+-debug} "-cachedir=$W_HOME\\Zomboid" </dev/null
