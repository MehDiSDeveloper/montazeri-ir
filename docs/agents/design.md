<!-- Moved out of CLAUDE.md so it loads only when needed. Keep it current. -->

## The design system

**Colour lives in the three token blocks at the top of `static/css/site.css`
and nowhere else.** `:root` is the light theme; the two blocks after it restate
the same names for dark, once for `prefers-color-scheme` and once for an
explicit `[data-theme="dark"]`, so an explicit choice beats the device in both
directions. A rule that needs a tint writes `rgba(var(--mint-rgb), .12)`, never
a second hex. Re-theming the site is editing values in those blocks. The two
`--bg` values are also written in `base.html`'s `theme-color` meta tags and in
`THEME_COLOR` in `app.js`.

The palette is **four pastels, each with one meaning**:

| hue | means | where |
|---|---|---|
| mint (`--mint`) | the work, and anything actionable | projects, nav, primary buttons |
| sky (`--sky`) | the career | timeline, résumé, facts |
| peach (`--peach`) | the person | availability, «این روزها», contact |
| lilac (`--lilac`) | writing, and nothing else | posts, so a post tag never reads as a project |

A fifth hue would need a fifth meaning, which is the reason not to add one.

**Each hue is a five-step ramp, not one value**: `--x-tint`, `--x-soft`,
`--x`, `--x-strong`, `--x-deep`, plus `--x-rgb` for tints. A card, its border,
its icon and its label can be one colour at four intensities. What each step
is *for* is the rule to keep:

- `-tint` is a ground you can barely see, `-soft` is a fill, `--x` is the
  pastel itself (a button, a dot, a hover border).
- **Only `-strong` and `-deep` may colour a letterform**: `-strong` on
  `--surface` or `-tint` (≥ 4.5:1), and **on a `-soft` fill only `-deep`**
  (mint and peach `-strong` fall to 4.3–4.5:1 there).
- Text **on the pastel `--x` itself is `--on-accent`**, which is ink. That is
  why a primary button is a pastel with dark lettering rather than a saturated
  fill with white: it keeps the page pastel and still AA (8:1 or better).

In dark the ramp inverts — `-deep` is the *lightest* step — so a rule that
asked for `-deep` because it was drawing text keeps getting the readable step
without knowing about the theme.

**`--accent-*` is an indirection, not a fifth colour.** An element carrying
`data-accent="peach"` (or `"sky"`, `"lilac"`, `"mint"`) re-points the whole
ramp for itself and everything inside it, so every eyebrow, pill, chip, tag,
button and link in that subtree follows. Re-colouring a section is one
attribute in the template and no new CSS. Prefer `var(--accent-…)` over
`var(--mint-…)` in any component that could appear in more than one context.

**Where a hue *carries* something it means something; where it is only a
field it is rhythm.** Tags, links, buttons and post rows are the first kind and
keep the meanings above. Rows of near-identical boxes — case covers, project
cards, skill groups, fact tiles, contact channels, footer columns, the tech
ribbon — are the second: their container carries **`.rhythm`**, whose children
take turns through all four hues, so four boxes read as four boxes. Removing
the class is how a row goes back to one hue.

**A section can be a band.** `.sec.sec-band` paints the section edge to edge in
its own accent's `--wash-*` with a hairline dot texture. Bands alternate with
plain sections down the home page (work → *career band* → toolbox → *writing
band* → contact), which is what gives a long page a horizontal rhythm.

**Nothing may bleed sideways.** The hero aurora is an element with
`overflow: hidden`, and `.page-head::before` bleeds *up* behind the
transparent header but has `inset-inline: 0`. A negative inline inset or a
`left: -9999px` is scrollable overflow in RTL: the Persian page opens shifted
by exactly that much, while English looks fine. `html` carries
`overflow-x: clip` as the last line of defence, and **`<body>` must not carry
any `overflow-x`** — next to `clip` on `html` it turns `<body>` into its own
scroll container and the sticky header stops sticking.

**`[hidden]` always wins** (`display: none !important` in the base). Without
it a component's own `display: grid` beats the attribute, and a closed
popover, a filtered-out card and the pre-JS back-to-top button all show.

**Motion has one vocabulary.** Two easings, `--ease` (settle) and `--spring`
(a small overshoot, for things that pop); hover lifts use `transform`, arrivals
use the individual `translate`/`scale` properties, so the two never overwrite
each other. **The whole site sits on `.ambient`** (first child of `<body>`): a
fixed, self-clipped layer of four pastel lights drifting on 22–32 s cycles,
turned by scroll through a scroll-driven `rotate` (no JS), plus grain; over
them `initAmbient()` draws a canvas network (linked nodes, events travelling
the links, rising code tokens) in the `--x-rgb` colours. Strength is the
`--ambient` and `--net` tokens, set per theme. Every decorative loop —
the ambient field, the aurora drift, the portrait halo, the
floating skill chips, the tech ribbon — sits behind
`prefers-reduced-motion`, which also stops the ribbon and wraps it.

**Logical properties only.** The site runs RTL in Persian and LTR in English
and German from the same rules: `padding-inline-start`, never `padding-left`.
A rule with a physical side in it is a bug in one of the three languages.

**Three typefaces, all self-hosted.** Vazirmatn for everything Persian and all
UI, Fraunces for Latin display (the name, the card index, the error code) and
IBM Plex Mono for labels, dates and technology names. Nothing this page draws
with comes off a CDN — inside Iran `fonts.googleapis.com` is slow at best.
Latin runs inside Persian text carry `.lat` or `.mono`, which set
`direction: ltr; unicode-bidi: isolate`, or a Latin word flips inside a Persian
sentence.

**The theme has three states**, not two: `system` / `light` / `dark`, stored
under `localStorage["montazeri-theme"]`. That key is read **twice**: by
`app.js`, and by a small blocking script in `base.html`'s `<head>`. The second
one is pre-paint on purpose — deferring it to `app.js` repaints one frame in,
which is exactly the flash it prevents. **If you rename the key, rename it in
both places.**
