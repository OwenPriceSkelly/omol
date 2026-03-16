# Spyhop Frontend — Design Document

*Date: 2026-03-16*

## Problem

The spyhop API has working `/query/count` and `/query/manifest` endpoints, but there is no user-facing interface. Researchers need a way to explore the OMol25 dataset interactively — filtering by element composition, domain, and scalar properties — without writing code.

## Design Principles

- **No build toolchain** — single `index.html` file, deployable to GitHub Pages with no CI setup
- **YAGNI** — prototype first, host locally, deploy to GitHub Pages before declaring victory
- **Accessible to non-FE developers** — Alpine.js + Tailwind via CDN keep the code readable without requiring framework expertise

## Architecture

A single `spyhop/index.html` file. No npm, no bundler, no build step. Two CDN dependencies loaded via `<script>` tags:

- **Tailwind CSS (CDN play build)** — utility classes for layout and element state colors
- **Alpine.js** — lightweight reactive library (~15kb); state lives in HTML attributes (`x-data`, `x-on:click`, `x-show`) rather than scattered DOM manipulation

The API base URL is a single `const API_URL = "..."` at the top of the script — easy to override for local dev or point at a different environment.

Filter state is a plain JS object owned by the root Alpine component:

```js
{
  must_have: [],
  must_not_have: [],
  domain: null,
  num_atoms: { min: null, max: null },
  charge: null,
  spin: null,
}
```

## Components

### Periodic Table Grid

CSS grid with 18 columns matching real periodic table layout. Each element is a small square button showing symbol and atomic number. Lanthanide/actinide rows sit below the main grid with a small visual gap (rows 8–9, col offset 3), matching standard conventions.

**Three-state toggle** (left-click cycles forward):
- Neutral (gray) — no constraint
- Must-have (green) — element required
- Must-not-have (red) — element excluded

The Alpine component owns `must_have` and `must_not_have` arrays. Each click rotates the element through the three states and updates both arrays.

Element grid data is a hardcoded JS array at the top of the script — 118 entries with `{ symbol, number, row, col }`.

### Advanced Filters

Collapsible section (closed by default), toggled with `x-show` and a chevron indicator. Contains:

- **Domain** — dropdown with the 10 known values (`biomolecules`, `elytes`, `metal_complexes`, `reactivity`, `ani2x`, `trans1x`, `geom_orca6`, `rgd`, `orbnet_denali`, `spice`) plus "any"
- **Num atoms** — two number inputs (min / max)
- **Charge** — single number input
- **Spin** — single number input (multiplicity, 2S+1)

### Results Panel

Always visible below the periodic table.

**Live count** — updated on every filter change, debounced 300ms via a `setTimeout` wrapper. Shows `N structures (~X GB)`. While a request is in flight, the text dims. On error, shows "—" with a small red message.

**Manifest** — "Generate manifest" button POSTs to `/query/manifest`. On success:
- First 20 paths rendered in a `<pre>` block for preview
- "Download full manifest" link generated via `URL.createObjectURL(new Blob([fullText]))`, filename `omol_manifest.txt`

## Data Flow

1. User toggles an element or changes an advanced filter
2. `updateCount()` fires, debounced 300ms
3. POST `/query/count` with current filter state → update count display
4. User clicks "Generate manifest"
5. POST `/query/manifest` → render preview + download link

## Error Handling

Minimal for prototype: failed requests show "—" in the count display and a small red error message. No retries.

## Hosting

- **Now**: local `index.html`, opened directly in the browser
- **Before prototype sign-off**: deploy to GitHub Pages (zero config for a single static file)
