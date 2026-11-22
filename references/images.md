# Images: preview, poster, icons, screenshots

| Asset | Where | Size | Notes |
|---|---|---|---|
| Workshop preview | `<Item>/preview.png` | square, **max 512x512**, 8-bit colour, < 1 MB | The card players see in search. 256x256 is plenty; 512x512 is the in-game uploader's maximum (PZ wiki). Scale it yourself (LANCZOS) so pixel art stays crisp. Non-square or animated previews need an external tool (SteamChangePreview). |
| In-game poster | `42/poster.png` (and root, beside each `mod.info`), `poster=poster.png` | 256x256 is fine | Shown in the mod list. Usually the same art. |
| Mod list icon | `42/icon.png`, `icon=icon.png` | small square (32-64 px) | Optional; 109 of 273 installed mods ship one. |
| Trait icon | `42/media/ui/Traits/trait_<name>.png` | 18x18 | Match vanilla trait icons: simple silhouette, readable at 18 px. |
| UI icons / marks | `42/media/ui/<Mod>/...png` | the size you draw at (16-32 px typical) | Transparent PNG. Generate from a script so they can be rebuilt. |
| Screenshots | `docs/screenshots/<what-it-shows>.png` | full resolution, PNG | Linked from README and workshop.txt via raw GitHub URLs. |

## Principle: images are built by scripts

Keep a `tools/make_preview.py` (and `make_icons.py`) in the repo so art is reproducible and editable.
Pillow is enough (`pip install pillow`). `scripts/make_preview.py` in this skill is a template with two
modes:

```bash
# text card in the mod's own colours (UI and admin mods)
python scripts/make_preview.py --title "Server Event Manager" --subtitle BETA --out MyMod/preview.png
# from an in-game screenshot: crop, darken bands, big outlined title (gameplay mods)
python scripts/make_preview.py --shot raw.png --crop 40,20,560,540 --title "SEE IT" --bottom "BEFORE YOU HIT IT" --out MyMod/preview.png
```

Technique notes:

- Draw at 4x then downscale with `Image.LANCZOS` for smooth text and lines.
- Title text: heavy font (Impact, Arial Black, Bahnschrift Bold on Windows: `C:/Windows/Fonts/`),
  yellow/white fill, black stroke (`stroke_width=4`), on a darkened band (`(0,0,0,170)` overlay).
  It must read at 128 px, the size the card often shows.
- One idea per preview: the effect of the mod, not a collage.
- If the user supplies artwork, use theirs; resize to 256x256 and keep a large copy out of the item folder
  (or under 1 MB).
- Using another mod's logo (add-ons): only to show what it extends, marked `[UNOFFICIAL]`, credited.

## Generated art (AI images)

The PZ wiki warns that Workshop users skip mods with AI-generated previews: low-effort mods made the
look a signal of low quality, and AI previews rarely match the game's style or show what the mod does.
Default to **an in-game screenshot of the mod working, with the mod name on it** (`make_preview.py
--shot`). If the user still wants generated art, they make it (or approve it) and the licence question
is theirs; note it in the README. Check it for the usual generator defects at 256 px: garbled text (put text on with
Pillow instead), extra fingers, melted UI. Never pass off a generated image as an in-game screenshot.

## Screenshots that sell the mod

Take them on the rig client or the user's game; they must show the real mod.

- Capture: Windows `Win+Shift+S` or the game's own screenshot key (Steam overlay F12 is not available on
  `-nosteam` rig clients). Save raw captures to a gitignored `docs/screenshots/raw/`, then copy the
  keepers to `docs/screenshots/` with names that say what they show (`map-world.png`,
  `crash-helicopter.png`), not `2026-09-25 11_00_46-Project Zomboid.png`.
- Show the feature doing its job, close enough to read: zoom in, hide unrelated UI, daytime unless the
  mod is about night.
- One shot per feature, each with a one-line caption in the README (alt text describes the moment).
- Before committing, look at every image for private data: usernames in chat or nameplates, server
  names, IPs in the server browser, desktop overlays, notification popups. Crop or retake.
- Keep each under a few MB (PNG is fine; downscale 4K captures to 1920 wide).

## Icons from code

For status icons, marks and arrows, draw them in Pillow from shapes (circles, polygons, outlines) at 4x
and downscale; keep one script that writes every variant so colour changes are one edit. Give every
icon a dark outline so it reads on both grass and snow. Colour meaning must be consistent across the
mod (red = hostile only, and so on) and survive colour blindness: vary shape as well as colour.
