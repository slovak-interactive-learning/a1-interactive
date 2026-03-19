# Slovenčina — Daily Practice Hub

A standalone webapp for practising Slovak at the A1 level (Krížom Krážom curriculum).

## Quick Start (with the included seed bank)

The repo comes with a seed `bank.js` containing ~10 stories, ~8 translate sets, ~5 builder sets, and ~5 drill sets. To use immediately:

1. Open `index.html` in your browser (works as a local file, no server needed)
2. Start practising!

## Generating a Bigger Bank (100+ sets)

The generator script uses the Anthropic API to create varied exercises.

### Prerequisites

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

### Generate

```bash
# Generate 100 of each exercise type (takes ~30-45 minutes, ~$2-3 in API costs)
python generate_bank.py --stories=100 --translates=100 --gapfills=100 --drills=100

# Or start smaller
python generate_bank.py --stories=20 --translates=20 --gapfills=20 --drills=20

# Custom batch size (saves after each batch, so you can interrupt & resume)
python generate_bank.py --stories=100 --batch-size=10
```

The script:
- **Saves progress** after each batch — safe to interrupt with Ctrl+C
- **Resumes** from where it left off (reads existing `bank.json`)
- **Deduplicates** by tracking used scenarios/themes
- Outputs both `bank.json` (readable) and `bank.js` (for the webapp)

### Use the generated bank

After generation, copy `bank.js` into the same folder as `index.html`:

```bash
cp bank.js /path/to/your/slovak-practice/bank.js
```

Refresh the page — the app will automatically use the new bank. The exercise count shows at the bottom of the home screen.

## Hosting

### Option A: Local file
Just double-click `index.html`. Works in any modern browser.

### Option B: GitHub Pages
1. Create a repo, push `index.html` and `bank.js`
2. Enable GitHub Pages in repo settings
3. Access at `https://yourusername.github.io/repo-name/`

### Option C: Any static host
Upload `index.html` + `bank.js` to Netlify, Vercel, Cloudflare Pages, or any web server.

## Features

- **📖 Micro-Story**: Read 6-sentence stories, tap to reveal translations
- **✍️ Translate**: Type Slovak translations, get scored
- **🧩 Word Order**: Arrange jumbled words into correct Slovak sentences
- **⚡ Grammar Drill**: Speed-round with 15-second timer across 7 grammar categories

All exercises cover the full KK A1 curriculum + early A2:
- 4 cases (nominative, accusative, instrumental, locative)
- Present, past, and future tense
- Pronouns in all cases
- Modal verbs, reflexive verbs, verb aspect
- Time expressions, ordinal numbers, dates
- Double negation, word order, possessives

## How It Works

- Exercises are randomly picked from the bank
- The app tracks which exercises you've seen and avoids repeats until you've cycled through all of them
- Streak counter persists across sessions (localStorage)
- No API calls at runtime — everything is instant and offline

## File Structure

```
slovak-practice/
├── index.html          # The webapp (single file, ~20KB)
├── bank.js             # Exercise bank (loaded by index.html)
├── bank.json           # Same data, readable format (generated)
├── generate_bank.py    # Bank generator script
└── README.md           # This file
```
