# autowebsite

Autonomous iteration on an academic CV website, adapted from [autoresearch](https://github.com/karpathy/autoresearch).

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar31`). The branch `autowebsite/<tag>` must not already exist — this is a fresh run.
2. **Create the branch**: `git checkout -b autowebsite/<tag>` from current main.
3. **Read the in-scope files**: The repo is small. Read these files for full context:
   - `README.md` — project context.
   - `evaluate.py` — fixed three-layer evaluation harness. DO NOT MODIFY.
   - `cv-data.json` — fixed academic CV data. DO NOT MODIFY.
   - `program.md` — this file. Your instructions. DO NOT MODIFY.
   - `index.html` — the file you modify.
4. **Verify setup**: Run `python3 evaluate.py > run.log 2>&1` and confirm scores come back via `grep "^composite_score:" run.log`.
5. **Initialize results.tsv**: Create `results.tsv` with just the header row. The baseline will be recorded after the first run.
6. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Design Brief

This section defines the aesthetic target. The evaluation harness checks adherence to these directives. The human edits this section to steer taste.

- palette: navy (#1B2A4A) and white (#FFFFFF), one warm accent (#C4A35A)
- headings: serif (Georgia or similar)
- body: system sans-serif stack (-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif)
- layout: single column, max-width 750px
- publications: hanging indent, bold author name, italic venue
- above the fold: name, title, affiliation, photo, email, links
- aesthetic: minimalist faculty page, not a startup landing page
- print: clean black-and-white, no background colors

## Experimentation

Each experiment runs `python3 evaluate.py` which takes ~30–60 seconds (3 Lighthouse runs + heuristic scoring).

**What you CAN do:**
- Modify `index.html` — this is the ONLY file you edit. Everything is fair game: layout, typography, colors, CSS animations, semantic HTML structure, meta tags, Open Graph tags, structured data, image optimization, responsive design, etc.
- All CSS must be inline (inside `<style>` tags). Google Fonts via `<link>` are acceptable.

**What you CANNOT do:**
- Modify `evaluate.py`. It is read-only.
- Modify `cv-data.json`. It is read-only. (But you should read it for authoritative data.)
- Modify `program.md`. It is read-only.
- Add external JavaScript frameworks (React, Vue, etc.).
- Add external CSS frameworks (Bootstrap, Tailwind, etc.).
- The page must work as a static HTML file served by any HTTP server.

**The goal: maximize composite_score.**

The composite score is:
```
composite = 0.40 * lighthouse + 0.40 * heuristic + 0.20 * brief
```

Where:
- **lighthouse** (40%): average of Lighthouse Performance, Accessibility, Best Practices, SEO
- **heuristic** (40%): domain-specific academic design quality checks
- **brief** (20%): adherence to the Design Brief section above

Higher is better.

**Content accuracy**: All text content MUST match `cv-data.json`. Do not invent publications, degrees, or experiences. Read `cv-data.json` for the authoritative data source.

**Simplicity criterion**: All else being equal, simpler HTML/CSS is better. A 0.5-point improvement that adds 50 lines of hacky CSS? Probably not worth it. Removing markup and getting equal or better scores? Definitely keep. Clean, readable code is part of the aesthetic.

**The first run**: Your very first run should always be to establish the baseline, so run the evaluation on the initial `index.html` as is.

## Output format

The evaluation prints:

```
---
composite_score:  85.50
lighthouse:       92.00
heuristic:        82.00
brief:            75.00
perf:             95.00
a11y:             90.00
bp:               88.00
seo:              82.00
html_size_kb:     12.3
```

Extract the key metric: `grep "^composite_score:" run.log`

## Logging results

When an experiment is done, log it to `results.tsv` (tab-separated, NOT comma-separated).

The TSV has a header row and 8 columns:

```
commit	composite	lighthouse	heuristic	brief	status	description
```

1. git commit hash (short, 7 chars)
2. composite_score (e.g. 85.50)
3. lighthouse score
4. heuristic score
5. brief score
6. status: `keep`, `discard`, or `crash`
7. short text description of what this experiment tried

Example:

```
commit	composite	lighthouse	heuristic	brief	status	description
a1b2c3d	65.40	72.00	60.00	55.00	keep	baseline
b2c3d4e	71.20	78.00	70.00	60.00	keep	add lang attr, viewport meta, semantic HTML
c3d4e5f	70.80	80.00	68.00	58.00	discard	tried grid layout (broke single-column)
```

## The experiment loop

The experiment runs on a dedicated branch (e.g. `autowebsite/mar31`).

LOOP FOREVER:

1. Look at the git state: the current branch/commit we're on and recent results.tsv entries
2. Choose an improvement strategy (see Ideas section below)
3. Modify `index.html`
4. git commit
5. Run the experiment: `python3 evaluate.py > run.log 2>&1` (redirect everything)
6. Read out the results: `grep "^composite_score:\|^lighthouse:\|^heuristic:\|^brief:" run.log`
7. If the grep output is empty, the run crashed. Run `tail -n 50 run.log` to read the error and attempt a fix.
8. Record the results in the tsv (NOTE: do not commit the results.tsv file, leave it untracked by git)
9. If composite_score improved (higher), you "advance" the branch, keeping the git commit
10. If composite_score is equal or worse, you git reset back to where you started

**Timeout**: Each evaluation should take ~30–60 seconds. If a run exceeds 3 minutes, kill it and treat it as a failure.

**Crashes**: If evaluation crashes, use your judgment. If it's a dumb bug (typo, malformed HTML), fix it and re-run. If the idea is fundamentally broken, skip it, log "crash", and move on.

**NEVER STOP**: Once the experiment loop has begun, do NOT pause to ask the human if you should continue. The human might be asleep. You are autonomous. If you run out of ideas, re-read the heuristic details and Lighthouse audit failures in run.log for specific things to fix. The loop runs until the human interrupts you, period.

## Ideas to try (in rough priority order)

### Quick wins (Lighthouse Accessibility + SEO)
- Add `lang="en"` attribute to `<html>`
- Add `<meta name="viewport" content="width=device-width, initial-scale=1">`
- Add `<meta name="description" content="...">`
- Use semantic HTML5: `<header>`, `<main>`, `<section>`, `<footer>`
- Add proper heading hierarchy (single `<h1>`, then `<h2>`, `<h3>`)
- Ensure sufficient color contrast (4.5:1 minimum)
- Add skip-to-content link
- All images must have `alt` text
- Add ARIA landmarks where appropriate

### Heuristic targets
- Set `max-width` to ≤ 750px on the main container
- Use ≤ 5 distinct colors in CSS
- Add `@media print` stylesheet (clean black-and-white)
- Style publications with hanging indent (`text-indent` + `padding-left`)
- Put contact info (email, links) in the `<header>` section
- Use semantic `<section>` tags for each CV section
- Keep animations/transitions to ≤ 2

### Brief adherence
- Use navy (#1B2A4A) as primary color
- Use Georgia (or similar serif) for headings
- Use system sans-serif stack for body text
- Single-column layout, max-width 750px
- Place name, title, affiliation, photo, email, links above the fold
- Minimalist aesthetic — no cards, no hero sections, no startup vibes

### Performance
- Inline critical CSS (already inline by design)
- Optimize/remove unused CSS rules
- Minimize DOM depth
- Set explicit `width` and `height` on images (prevents CLS)
- Lazy-load images below the fold
- Preconnect to Google Fonts if used: `<link rel="preconnect" href="https://fonts.googleapis.com">`

### Advanced
- Add JSON-LD structured data (`Person` schema with `sameAs` links)
- Add Open Graph meta tags (`og:title`, `og:description`, `og:image`)
- Add `<link rel="canonical">`
- Optimize for Cumulative Layout Shift (explicit image dimensions, font-display: swap)
- Add `<meta name="theme-color">`
