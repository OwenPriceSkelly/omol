# Spyhop Frontend Implementation Plan

**Goal:** Build a single-file static web frontend for the OMol25 filter interface.

**Architecture:** A single `spyhop/index.html` with no build toolchain. Alpine.js manages reactive filter state; Tailwind CSS (CDN play build) handles layout and element state colors. The page POSTs JSON to the live Modal API and renders results directly.

**Tech Stack:** HTML, Tailwind CSS (CDN), Alpine.js (CDN), vanilla JS

**Documentation:** See design doc at `docs/plans/2026-03-16-spyhop-frontend-design.md`. API schema is at `https://garden-ai--spyhop-spyhopserver-serve-dev.modal.run/docs`.

---

### Task 1: Element data and periodic table grid

**Files:**
- Create: `spyhop/index.html`

**Behavior:**

Create the HTML skeleton with CDN imports and the periodic table grid. The element data is a hardcoded JS array of 118 objects at the top of the `<script>` block:

```js
{ symbol: "H", number: 1, row: 1, col: 1 },
{ symbol: "He", number: 2, row: 1, col: 18 },
// ...
```

Row/col follow standard periodic table layout (1-indexed). Lanthanides (La–Lu, Z=57–71) go on row 8, cols 3–17. Actinides (Ac–Lr, Z=89–103) go on row 9, cols 3–17. The gap between the main grid and the f-block rows is achieved with `mt-4` on the lanthanide row.

The grid is an 18-column CSS grid (`grid-cols-18` via Tailwind arbitrary value or inline style). Each element renders as a ~40×40px button showing symbol (bold) and atomic number (small, muted).

Element state is tracked in the Alpine root component:

```js
x-data="{
  must_have: [],
  must_not_have: [],
  ...
  elementState(sym) { ... },  // returns 'neutral' | 'must_have' | 'must_not_have'
  toggleElement(sym) { ... }, // cycles state forward
}"
```

`toggleElement` cycles: neutral → must_have → must_not_have → neutral by adding/removing from the two arrays.

Button color is driven by `elementState`: gray for neutral, green for must_have, red for must_not_have (Tailwind bg- classes bound with `:class`).

**Test cases:**

- **Element grid renders all 118 elements**
  - Given: page is loaded
  - When: user inspects the grid
  - Then: all 118 element symbols are present, H at top-left, Og at bottom-right of main grid

- **Lanthanide/actinide rows are visually separated**
  - Given: page is loaded
  - When: user views the bottom of the table
  - Then: La–Lu and Ac–Lr appear below the main grid with a visible gap

- **Element cycles through three states on click**
  - Given: all elements start neutral (gray)
  - When: user clicks Fe once
  - Then: Fe turns green (must_have)
  - When: user clicks Fe again
  - Then: Fe turns red (must_not_have)
  - When: user clicks Fe again
  - Then: Fe returns to gray (neutral)

- **must_have and must_not_have arrays update correctly**
  - Given: Fe is neutral
  - When: clicked to must_have
  - Then: `must_have` contains "Fe", `must_not_have` does not
  - When: clicked to must_not_have
  - Then: `must_not_have` contains "Fe", `must_have` does not
  - When: clicked to neutral
  - Then: neither array contains "Fe"

**Verify:** Open `spyhop/index.html` in a browser. Periodic table renders correctly, element clicking cycles colors, browser console shows no errors.

---

### Task 2: Live count with debounced API call

**Files:**
- Modify: `spyhop/index.html`

**Behavior:**

Add the results panel below the periodic table and wire up the live count.

The API base URL is a `const` at the top of the script:
```js
const API_URL = "https://garden-ai--spyhop-spyhopserver-serve-dev.modal.run";
```

The Alpine component gains:
- `count: null` — current count (null = not yet loaded)
- `estimatedGb: null`
- `countLoading: false`
- `countError: null`
- `_debounceTimer: null`

`updateCount()` clears any pending timer, sets a 300ms timeout, then POSTs the current filter state (serialized via a `buildSpec()` helper) to `/query/count`. On success, updates `count` and `estimatedGb`. On failure, sets `countError`.

`buildSpec()` constructs the JSON body from current state, omitting null/empty fields so the API receives a clean spec.

`toggleElement` calls `updateCount()` after modifying state. The advanced filter inputs (Task 3) will also call it.

The results panel shows:
- While loading: dimmed "— structures (~— GB)"
- On success: "14,200 structures (~56.3 GB)"
- On error: "— structures" + small red error text

**Test cases:**

- **Count updates after element toggle**
  - Given: page freshly loaded (count shows full dataset)
  - When: user clicks Fe (must_have)
  - Then: after ~300ms, count updates to a smaller number

- **Count reflects correct filter**
  - Given: Fe is must_have, no other filters
  - When: count displays
  - Then: value matches `POST /query/count {"must_have": ["Fe"]}` from the API directly (verify in devtools Network tab)

- **Loading state is shown during request**
  - Given: network is slow (throttle in devtools)
  - When: user toggles an element
  - Then: count text dims while request is in flight

- **Error state shown on API failure**
  - Given: API_URL is set to an invalid URL
  - When: page loads and fires initial count
  - Then: count shows "—" and a red error message appears

- **Debounce: rapid clicks fire only one request**
  - Given: user clicks 5 elements quickly in succession
  - When: watching the Network tab
  - Then: only one `/query/count` request is sent (after the last click's 300ms window)

**Verify:** Toggle elements and confirm Network tab shows debounced `/query/count` calls with correct request body and sensible response counts.

---

### Task 3: Advanced filters (collapsible)

**Files:**
- Modify: `spyhop/index.html`

**Behavior:**

Add a collapsible "Advanced filters" section between the periodic table and results panel.

Alpine component gains: `advancedOpen: false` (toggle with a chevron button using `x-show`).

Inside the collapsible:
- **Domain**: `<select>` with options `["any", "biomolecules", "elytes", "metal_complexes", "reactivity", "ani2x", "trans1x", "geom_orca6", "rgd", "orbnet_denali", "spice"]`. Bound to `domain` (null when "any" selected).
- **Min/max atoms**: two `<input type="number">` bound to `num_atoms.min` and `num_atoms.max`.
- **Charge**: `<input type="number">` bound to `charge`.
- **Spin**: `<input type="number">` bound to `spin`.

All inputs call `updateCount()` on change (`x-on:change` or `x-on:input` with debounce already handled inside `updateCount`).

`buildSpec()` must include these fields when non-null/non-empty, matching the API's `FilterSpecModel` shape exactly.

**Test cases:**

- **Advanced filters section is hidden by default**
  - Given: page loads
  - When: user has not interacted with the chevron
  - Then: domain/atoms/charge/spin inputs are not visible

- **Chevron toggles section open and closed**
  - Given: section is closed
  - When: user clicks the chevron
  - Then: inputs become visible; clicking again hides them

- **Domain filter narrows count**
  - Given: no element filters active
  - When: user selects "elytes" in the domain dropdown
  - Then: count updates to ~800k (the elytes slice of the 4M)

- **num_atoms range filter included in request**
  - Given: user enters min=5, max=20
  - When: watching Network tab
  - Then: request body contains `{"num_atoms": {"min": 5, "max": 20}}`

- **"any" domain sends no domain field**
  - Given: user selects a domain then switches back to "any"
  - When: watching Network tab
  - Then: request body does not contain a `domain` key

**Verify:** Open advanced filters, set domain to "metal_complexes", observe count change. Inspect Network tab to confirm request body matches expected spec.

---

### Task 4: Manifest preview and download

**Files:**
- Modify: `spyhop/index.html`

**Behavior:**

Add "Generate manifest" button to the results panel. On click, POSTs current filter state to `/query/manifest`.

Alpine component gains:
- `manifestLoading: false`
- `manifestError: null`
- `manifestPreview: null` — first 20 lines as a string
- `manifestBlob: null` — full manifest as a Blob URL for download
- `manifestCount: null`

On success, the response JSON is formatted into the Globus batch format (same as the CLI: one `src dest` line per path, with comment header), stored in full as a Blob, and the first 20 lines are extracted for preview.

The download link is created with `URL.createObjectURL(blob)` and uses the `download="omol_manifest.txt"` attribute. Previous Blob URLs should be revoked with `URL.revokeObjectURL` before creating a new one to avoid memory leaks.

The manifest section shows:
- "Generate manifest" button (always visible in results panel)
- While loading: button dims / spinner
- On success: `<pre>` block with first 20 lines + "... and N more" if truncated, plus "Download full manifest (N paths)" link
- On error: red error message

**Test cases:**

- **Manifest button triggers POST to /query/manifest**
  - Given: Fe is must_have, domain is metal_complexes
  - When: user clicks "Generate manifest"
  - Then: Network tab shows POST to `/query/manifest` with correct body

- **Preview shows first 20 paths**
  - Given: filter matches >20 structures
  - When: manifest loads
  - Then: `<pre>` shows exactly 20 path lines plus a "... and N more" message

- **Preview shows all paths when ≤20 results**
  - Given: tight filter (e.g. Fe + N + P + max_atoms=20 + metal_complexes = 2 results)
  - When: manifest loads
  - Then: all 2 paths visible, no truncation message

- **Download link produces valid Globus batch file**
  - Given: manifest has loaded
  - When: user clicks "Download full manifest"
  - Then: file downloads as `omol_manifest.txt`, contains comment header and one `path/ path/` line per result

- **Manifest regenerates when filters change after initial generation**
  - Given: manifest was generated for filter A
  - When: user changes a filter and clicks "Generate manifest" again
  - Then: new manifest reflects updated filter; old Blob URL is revoked

- **Error state on manifest failure**
  - Given: API_URL is broken
  - When: user clicks "Generate manifest"
  - Then: red error message appears, no download link shown

**Verify:** With tight filter (Fe + N + P + metal_complexes + max-atoms 20), click "Generate manifest". Confirm 2 paths appear in preview. Download file and confirm it matches CLI output for the same filter.

---

### Task 5: Polish and GitHub Pages prep

**Files:**
- Modify: `spyhop/index.html`
- Modify: `TODO.md`

**Behavior:**

Final polish before the prototype is declared done:

- Page title: "OMol25 Filter Interface"
- Add a one-line description at the top: "Filter the OMol25 DFT dataset by element composition and molecular properties. Generate a Globus transfer manifest for your selection."
- Add a small footer with a link to the Globus collection URL
- Add a "Reset all filters" button that clears all state and re-fires `updateCount()`
- Confirm the page works when opened as a local file (`file://`) — no CORS issues since all requests go to the Modal API (which has `allow_origins=["*"]`)
- Update `TODO.md`: mark frontend done, add "Deploy index.html to GitHub Pages" as the final prototype sign-off task

**Test cases:**

- **Reset button clears all state**
  - Given: several elements selected, domain set, num_atoms range set
  - When: user clicks "Reset all filters"
  - Then: all elements return to neutral, all inputs clear, count returns to full dataset count

- **Page works as a local file**
  - Given: `spyhop/index.html` opened via `file://` in Chrome/Firefox
  - When: page loads and user interacts
  - Then: count updates correctly, no CORS errors in console

**Verify:** Full end-to-end walkthrough: load page locally, select Fe + N, open advanced filters, set domain to metal_complexes, observe count, generate manifest, download file, confirm it matches CLI output.
