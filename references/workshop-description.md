# Writing the Workshop description (and README)

The Workshop page is read by a player deciding in ten seconds whether to subscribe, and by a server
admin checking whether it breaks their server. Write for both. Plain, specific, honest.

## Structure that works

```
[h1]Mod Title[/h1]
One or two sentences: the problem or fantasy, then what the mod does about it.

[h2]Features[/h2]   (or "What it does")
[list]
[*][b]Short bold claim.[/b] One sentence of how it actually behaves, with the default number.
[/list]

[h2]Options[/h2]
[list]
[*][b]Option name[/b]: range, default N
[/list]

[h2]Notes[/h2]
[list]
[*]Client-side only / needs to be on the server. Safe to add to or remove from an existing save (only if true).
[*]Singleplayer and/or multiplayer.
[*]Compatibility and known limits.
[/list]

[b]Build 42 only.[/b] Requires X (linked).
Credits (third-party assets with licence links).
Source: https://github.com/<you>/<repo>
```

For a big mod, add: a status line for beta ("This mod is in beta. Expect bugs. Report on GitHub with
what you did and your console.txt"), a "New in x.y.z" section at the top with only the latest one or
two versions, and a link to the full changelog on GitHub instead of pasting it.

## BBCode cheat sheet

`[h1] [h2] [h3]`, `[b] [i] [u] [strike]`, `[list][*]...[/list]`, `[olist]`, `[url=https://...]text[/url]`,
`[img]https://...[/img]`, `[code]`, `[quote]`, `[hr][/hr]`, `[spoiler]`. Markdown does not render.
Each line of the page is its own `description=` line in `workshop.txt`; a blank line is `description=`.

Images: Workshop text cannot host images. Link raw files from the public repo:
`[img]https://raw.githubusercontent.com/<you>/<repo>/main/docs/screenshots/name.png[/img]`.
They only show once pushed.

Limit: **8000 characters** for the whole description. `scripts/check_mod.py` counts it. Trim by moving
detail to the README and linking it.

## The two other descriptions

- `mod.info` `description=`: one or two sentences, shown in the in-game mod list. Lead with what it is.
- README: the full reference. Everything on the Workshop page plus how it works, every option with
  type/range/default, file layout, how to test, how to build assets, known limits, licence.

All three must agree on numbers (defaults, ranges, versions). When a default changes, grep all three.

## Voice: avoid the AI tells

Players and modders spot machine-written pages instantly and trust the mod less. Cut:

| Tell | Instead |
|---|---|
| "Elevate your gameplay", "immersive experience", "seamlessly", "robust", "comprehensive", "dive into", "unleash" | Say the concrete thing: "Outlines trees in a lane ahead of the car." |
| Em dashes everywhere, especially as decoration | Commas, colons, full stops. Keep translation JSON ASCII where vanilla is ASCII. |
| Emoji bullets, ✨🔥 | `[list]` with bold leads. |
| Rule-of-three adjectives ("fast, flexible and powerful") | One fact with a number. |
| Restating the title as the first sentence | Open with the problem or the effect. |
| Claims nobody tested ("fully compatible with all mods", "no performance impact") | What you tested, and "untested with X". |
| Long dramatic paragraphs in trait/item text | Vanilla's clipped mechanical lines with `<br>`. |
| Feature lists padded with things every mod does | Only what this mod does. |
| "Note:" / "Important:" stacked callouts | One Notes list. |

Read it aloud. If a sentence would sound odd from a person explaining their mod to a friend, rewrite it.
Humour and personality are fine when they are specific to the mod ("Sprinters do not groan. They scream.").

## Honesty rules

- Beta is labelled beta, everywhere (title tag, `modversion`, first lines).
- "Untested in game" is written down when true.
- Every third-party asset is credited with author, source link and licence. Unofficial add-ons for
  another mod say so and credit that mod's team, especially when the preview uses their logo
  (mark it `[UNOFFICIAL]`).
- State the licence (LICENSE file in the repo, or one of TIS's BBCode licence templates on the page).
- No private information: no server IPs, usernames, Discord invites the user did not ask for, local paths.
- Follow the user's preference on AI attribution. Do not add "made with AI" lines or tool footers they
  did not ask for; do not hide it if they want it stated.
