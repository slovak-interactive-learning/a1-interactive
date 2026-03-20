# Slovenčina — Daily Practice Hub

A standalone webapp for practising Slovak at the A1 level (Krížom Krážom curriculum).

## Quick Start

1. Open `index.html` in your browser (works as a local file, no server needed)
2. Start practising — the `bank/` folder contains the exercise bank

## Exercise Types

- **Micro-Story**: Read 6-sentence stories, tap to reveal translations
- **Translate**: Type Slovak translations, get scored
- **Gap Fill**: Multiple-choice gap-fill passages
- **Grammar Drill**: Speed-round with 15-second timer across grammar categories

## Topic Filtering

Click topic tags (grammar or thematic) on the home screen to filter exercises. Pool size updates live for each activity.

## File Structure

```
slovak-a1-interactive/
├── index.html              # The webapp (single file, no build step)
├── CURRICULUM.md           # Krížom Krážom A1 topic taxonomy
├── bank/
│   ├── stories.json        # Short dialogue/story exercises
│   ├── translates.json     # English → Slovak sentence exercises
│   ├── gapfills.json       # Gap-fill multiple choice exercises
│   ├── drills.json         # Grammar drill questions
│   ├── topic_stats.json    # Tag index used by the frontend filter
│   └── meta.json           # Bank metadata
└── scripts/
    ├── generate_bank.py    # Main exercise generator (Anthropic API)
    ├── generate_for_tag.py # Generate exercises for a specific topic tag
    ├── fill_gaps.py        # Fill specific thematic/grammar gaps
    ├── tag_exercises.py    # Post-process: add tags + rebuild topic_stats.json
    └── flatten_banks.py    # One-off migration (do not re-run)
```

## Generating Exercises

All scripts live in `scripts/` and write to `bank/`. Run them from the repo root.

### Prerequisites

```bash
pip install anthropic python-dotenv
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Add exercises in bulk

```bash
# Generate exercises (saves incrementally, safe to interrupt and resume)
python scripts/generate_bank.py --stories=50 --translates=50 --gapfills=50 --drills=50

# Then re-tag and rebuild topic_stats.json
python scripts/tag_exercises.py
```

### Add exercises for a specific tag

```bash
python scripts/generate_for_tag.py --list
python scripts/generate_for_tag.py --tag dative --count 10
# (calls tag_exercises.py automatically)
```

### Fill known curriculum gaps

```bash
python scripts/fill_gaps.py --list
python scripts/fill_gaps.py --topic colours
python scripts/fill_gaps.py          # all gaps
# (calls tag_exercises.py automatically)
```

### Re-tag / rebuild stats only

```bash
python scripts/tag_exercises.py           # update tags + topic_stats.json
python scripts/tag_exercises.py --dry-run # stats only, no writes
```

## How It Works

- Exercises are randomly picked from the bank; the app avoids repeats until you've cycled through all
- Topic filters narrow the pool client-side using `bank/topic_stats.json`
- Streak counter persists across sessions (localStorage)
- No API calls at runtime — fully offline after the bank is built

## Hosting

Upload `index.html` and the `bank/` folder to any static host (GitHub Pages, Netlify, Vercel, Cloudflare Pages) or just open `index.html` locally.
