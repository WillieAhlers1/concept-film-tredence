# Look: graphics, images, captions

The film has two looks, as the prototype does.  **Product scenes look like Microsoft**: they are the prototype,
filmed as it is.  **Everything Tredence says looks like Tredence**: the prototype's frame scenes (cover, close,
#beyondpossible) and the film's own graphics, which follow the Tredence 2026 template (pptx-tredence
`references/design-system.md`, prototype-tredence `references/tredence-frame.md`).

## Graphics (`graphics.html`)

`templates/graphics.html` is fixed: all words, numbers and images come from `film.json` `graphics` through
`gfx_data.py`.  Don't edit it per film; if a film needs something it can't do, change the template for every film
and check the stills of the example.

| Segment | What it shows | Brand treatment |
|---|---|---|
| `night` | Establishing photo, slow push-in, kicker + title; then the simulation if there's engine data | Charcoal shade on the photo (the one allowed gradient), orange accent bar, Bright Orange kicker, white Poppins Bold title with the key phrase in Bright Orange |
| `night` (simulation) | Each row a case with its deadline flag; dots = simulated outcomes; arrival order → search → the plan's order | Flat Charcoal over the blurred photo; Teal = in time, Bright Orange = too late; badges black on Teal or Bright Orange; stat values Highlight Orange before, Teal after |
| `morning` | Two photos crossfading, clock chip, name card, work-list card | White cards with the orange accent bar (the template's panel motif), Deep Orange label, black name, Charcoal role |
| `endcard` | Solid Bright Orange, the white T, kicker, one sentence, the wordmark with Beyond Possible | The template's orange divider; title all white |

Rules:
- **Poppins only** (Regular, Medium, SemiBold, Bold, in `fonts/`).  No Segoe, no system fonts in graphics.
- **The closed palette**: Bright Orange `#FE5000`, Teal `#6DCDB8`, Deep Green `#004E42`, Deep Orange `#8A1F04`,
  Highlight Orange `#F48120`, Charcoal `#404041`, Grey `#929497`, Off White `#E6E7E8`, white, black; Orange Tint
  `#FFEDE5` and Teal Tint `#E2F5F1` as backgrounds only.  `check_film.py` flags any other colour in `film.json`.
- **Flat colour**: no glows, glass, drop shadows or decorative gradients.  The Charcoal photo shade is the only
  gradient.
- **Titles are sentences you'd say**, sentence case, never opening with a number or a count.  Put the key phrase in
  `*asterisks*` to turn it Bright Orange.
- **Contrast**: white text on a photo only over the shade; orange text at 24 px and up; black (never white) on
  Teal; white on Bright Orange only at 24 px and up.
- **Official logos** from `brand/`, unrecoloured: `wordmark-tagline-white.svg` and `t-white.png` on the end card.
  Don't add logos to other graphics; the prototype's frame scenes already carry them.
- **The concept label** sits bottom left on every graphic (as in the prototype), from `graphics.concept_label`.
- **Keep the bottom ~190 px clear**: the captions sit there.
- **Simulation rows**: up to about 15 cases fit; keep product names short (`product_short`) so the detail line
  stays clear of the badges at x 470.

## Images

Three 16:9 photographs: the workplace at night (establishing), the person arriving, the person at work.  Repeat
one style descriptor in every prompt so they read as one set, in the spirit of the Tredence photo style (friendly,
human, warm):

> photorealistic editorial photography, warm natural light, candid and friendly, modern workplace, warm neutral
> palette with a touch of orange, soft depth of field, open space on the left for a title, no logos, no text,
> no readable screens

- Fictional people only, never a real person or a recognisable brand.  For the same person across shots, give
  the first image as the reference image if the generator supports it.
- `quality` medium, landscape 16:9, JPEG, at least 1920 px wide.  Save as `images/night.jpg`,
  `images/arrival.jpg`, `images/desk.jpg`.
- The brand photo set (prototype-tredence `kit/photos/`: mountains, lakes, hikers) is for cover and closing
  frames, not for the persona's workplace.  Don't substitute it for the three images.
- **No image generator**: the graphics fall back to flat colour (Charcoal at night, Teal Tint and Orange Tint in
  the morning).  It's clean and on-brand but less cinematic: say so in your reply and offer to drop in images later
  (re-run gfx_data, re-film the G segments, assemble).

## Captions

`subs.py` writes ASS captions: Poppins Medium 34, white on a Charcoal box at about 80 % opacity, bottom centre,
chunks of up to 72 characters split at sentences, then commas, with no fragment shorter than 24 characters.
`margin_v` 80 keeps the Tredence frame footer visible.  Captions are on by default: many viewers watch a shared
film muted.

## The end of the film

End on the prototype's close (the ask, held ~2 s) and its #beyondpossible closing scene with music only for 3-4 s.
If the prototype has no closing scene, end on the `endcard` graphic instead.  Never both.
