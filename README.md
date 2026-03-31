# autowebsite

Autonomous academic CV website builder, adapted from [karpathy/autoresearch](https://github.com/karpathy/autoresearch).

An AI agent iteratively improves a single `index.html` file, evaluated by a three-layer scoring system:

- **40% Lighthouse** — performance, accessibility, best practices, SEO
- **40% Academic design heuristics** — domain-specific checks for clean academic design
- **20% Brief adherence** — alignment with the human-defined design brief in `program.md`

## Quick start

```bash
# 1. Verify environment (one-time)
bash prepare.sh

# 2. Run one evaluation manually
python3 evaluate.py

# 3. Start autonomous iteration
# Point your AI agent to program.md and let it go
```

## Project structure

```
prepare.sh      — environment validation (do not modify)
evaluate.py     — three-layer evaluation harness (do not modify)
cv-data.json    — academic CV data (do not modify)
program.md      — agent instructions + design brief (human edits)
index.html      — the website (agent modifies this)
results.tsv     — experiment log (untracked)
src/            — photos, logos, assets
```

## Philosophy

Adapted from autoresearch's core principles:

- **Single file to modify.** The agent only touches `index.html`. Diffs are reviewable.
- **Fixed evaluation.** Three-layer composite score makes experiments comparable.
- **Self-contained.** Pure HTML + CSS, no frameworks, no build step.
- **Autonomous loop.** Modify → evaluate → keep/discard → repeat.
- **Human steers taste.** Edit the Design Brief in `program.md` to change aesthetics.

## License

MIT
