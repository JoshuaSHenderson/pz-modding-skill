# Release

## Checklist

1. `python scripts/check_mod.py <Item>` passes with no errors.
2. Specs pass; rig boot is clean (`[MyMod]` lines only, no new `ERROR`/`Exception` mentioning your files).
3. In-game checklist done, or the untested items are in README "Known limits".
4. Version bumped in **every** place: both `mod.info` `modversion`, CHANGELOG heading, workshop.txt
   "New in" section, any in-mod "what's new" text, README if it names the version. `grep -rn "0.4.0"`
   for the old one.
5. CHANGELOG entry: date, one-line theme, then Added / Changed / Fixed in player language (what they
   will notice), not commit language.
6. Credits and licences recorded for every third-party asset.
7. No private data: `git grep -n -i -E "192\.168|10\.0\.|password|@gmail|@hotmail|C:/Users|/home/"`
   and look at every new image.
8. Commit, then push **only with the user's go-ahead**.
9. Copy the item folder to the upload folder and let the user upload.

## Uploading

The Workshop uploader is in the game: Main Menu > Workshop > pick the item > Upload. It reads
`%USERPROFILE%\Zomboid\Workshop\<Item>\` (on Linux `~/Zomboid/Workshop/<Item>/`). Make it an exact copy
of the repo's item folder:

```bash
rm -rf "$HOME/Zomboid/Workshop/MyMod" && cp -r MyMod "$HOME/Zomboid/Workshop/MyMod"
```

- First upload: `id=` blank; afterwards copy the assigned id into `workshop.txt` and commit.
- The upload is the user's action (it publishes under their Steam account). Prepare everything and
  tell them it is ready.
- After upload: delete the Workshop folder copy or keep it in sync; a stale copy there shadows
  `~/Zomboid/mods` in the user's own game when ids match.
- Updating: same item, same id, bump version, upload again, add a change note in the uploader.

## Updating a published mod

- **Deleted files are not deleted on players' machines.** Steam leaves files from the old version in
  place, which can cause mismatches or stale code running. Instead of deleting a Lua file, leave it in
  the mod with its content emptied (a comment saying why), then remove it a few versions later.
- Batch changes: every update forces servers using the mod to restart before players can join. Ship
  larger tested updates; keep quick releases for critical fixes, and prefer weekdays over weekends.
- Test before uploading (rig + checklist). A broken update that needs three hotfixes costs every server
  three restarts.
- Write a change note in the uploader; it appears on the Workshop change log.
- The uploader replaces the whole Steam description with `workshop.txt`'s (see layout-and-metadata.md).

## Local install for play testing

```bash
rm -rf "$HOME/Zomboid/mods/MyMod" && cp -r MyMod/Contents/mods/MyMod "$HOME/Zomboid/mods/"
```

The game scans mods at startup; restart it after copying. While developing, keep **one** visible copy of
the mod: not subscribed to your own Workshop item, and not in both `~/Zomboid/mods` and
`~/Zomboid/Workshop` (same id = they clash and changes silently do not show up). The PZ wiki recommends
developing straight from `~/Zomboid/Workshop/<Item>` for that reason.

## Servers

- Workshop mods go on a server through `WorkshopItems=<id>` **and** `Mods=<modid>`; both lines.
- Every client downloads the server's version. A mismatch blocks joining; restart the server after
  updating.
- Removing a mod id from `Mods=` while its items exist in the save deletes them permanently.
- Never edit a running server's ini; it is rewritten on boot and shutdown.
