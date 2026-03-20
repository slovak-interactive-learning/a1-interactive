#!/usr/bin/env python3
"""
Generate Slovak exercises focused on a specific topic tag.

Usage:
    python generate_for_tag.py --list
    python generate_for_tag.py --tag dative
    python generate_for_tag.py --tag food_drink --count 10
    python generate_for_tag.py --tag instrumental --count 5 --workers 3
"""

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

BANK_DIR = Path(__file__).parent.parent / "bank"

# Grammar tags that map directly to drill categories
TAG_TO_DRILL_CATS = {
    "accusative":    ["accusative"],
    "instrumental":  ["instrumental"],
    "locative":      ["locative"],
    "nom_plural":    ["nom_plural"],
    "pronouns":      ["pronoun"],
    "present_tense": ["present"],
    "past_tense":    ["past"],
    "numerals":      ["numeral"],
    "time_date":     ["time"],
    "possessive":    ["possessive"],
    "adjectives":    ["adjective"],
    "uz_este":       ["uz_este"],
    "negation":      ["uz_este"],  # closest drill category
}

# Keywords for filtering grammar combos / scenario strings
TAG_KEYWORDS = {
    # Grammar
    "accusative":    ["accusative"],
    "locative":      ["locative"],
    "instrumental":  ["instrumental"],
    "nom_plural":    ["nominative plural", "nom_pl", "nominatív pl"],
    "nominative":    ["nominative"],
    "adjectives":    ["adjective", "colour", "color"],
    "pronouns":      ["pronoun", "demonstrative"],
    "present_tense": ["present tense", "present (", "present irregular", "byť conjugation"],
    "past_tense":    ["past tense", "past (", "past regular", "past irregular"],
    "future_tense":  ["future"],
    "modals":        ["modal", "chcieť", "musieť", "môcť"],
    "reflexive":     ["reflexive", "sa/si"],
    "numerals":      ["numeral", "ordinal", "cardinal"],
    "time_date":     ["time", "o koľkej", "date"],
    "negation":      ["negation", "nikto", "nikdy", "double neg"],
    "possessive":    ["possessive"],
    "uz_este":       ["už/ešte", "uz/este", "already"],
    # Thematic
    "food_drink":       ["food", "drink", "restaurant", "café", "canteen", "lunch",
                         "dinner", "breakfast", "cooking", "cook", "menu", "order"],
    "transport_travel": ["train", "transport", "tram", "bus", "travel", "trip",
                         "airport", "station", "drive", "car"],
    "home_apartment":   ["apartment", "flat", "dormitory", "room", "furniture",
                         "moving", "home"],
    "university_work":  ["university", "seminar", "exam", "library", "lecture",
                         "job", "work", "company", "office", "interview"],
    "family_people":    ["family", "grandparent", "sister", "brother", "friend",
                         "nationality"],
    "shopping":         ["shopping", "market", "shop", "clothes", "buy", "price",
                         "colour"],
    "weather":          ["weather", "rain", "storm", "forecast", "temperature"],
    "health":           ["doctor", "pharmacy", "illness", "health", "symptom", "sick"],
    "daily_routine":    ["morning", "routine", "daily", "schedule", "alarm", "wake"],
    "directions":       ["directions", "lost", "tourist", "map", "hotel", "building"],
    "social":           ["party", "friend", "meeting", "birthday", "celebration",
                         "wedding", "concert"],
    "free_time":        ["cinema", "film", "hobby", "sport", "gym", "hiking",
                         "music", "concert"],
    "colours":          ["colour", "color", "farba", "farby", "red", "blue", "green",
                         "yellow", "white", "black", "colour adjective", "svetly", "tmavy"],
    "clothing":         ["clothes", "clothing", "oblecenie", "sveter", "sukna",
                         "tricko", "nohavice", "topanky", "kabat", "kosela",
                         "outfit", "wearing", "dressed", "fashion"],
    "professions":      ["profession", "job title", "lekar", "ucitel", "inzinier",
                         "what do you do", "co robite", "works as", "career"],
    "countries":        ["country", "nationality", "odkial", "z ktorej krajiny",
                         "slovensko", "nemecko", "taliansko", "international",
                         "erasmus", "foreign student"],
}

GRAMMAR_TAGS = [
    "nominative", "accusative", "locative", "instrumental",
    "nom_plural", "adjectives", "pronouns", "present_tense", "past_tense",
    "future_tense", "modals", "reflexive", "numerals", "time_date", "negation",
    "possessive", "uz_este",
]
THEMATIC_TAGS = [
    "daily_routine", "food_drink", "transport_travel", "home_apartment",
    "university_work", "family_people", "shopping", "weather", "health",
    "free_time", "social", "directions",
    "colours", "clothing", "professions", "countries",
]
ALL_TAGS = GRAMMAR_TAGS + THEMATIC_TAGS


def filter_by_keywords(items, keywords, text_fn, min_results):
    """Return items whose text contains any keyword; fall back to all if too few match."""
    kw = [k.lower() for k in keywords]
    filtered = [x for x in items if any(k in text_fn(x).lower() for k in kw)]
    return filtered if len(filtered) >= min_results else items


def build_drill_prompts(tag, count, stems_by_cat, make_prompt):
    drill_cats = TAG_TO_DRILL_CATS.get(tag)
    all_cats = list(stems_by_cat.keys())
    prompts = []
    for _ in range(count):
        if drill_cats:
            # 6 slots from the target category, 2 from random others for variety
            target = [random.choice(drill_cats) for _ in range(6)]
            others = [c for c in all_cats if c not in drill_cats]
            filler = random.sample(others, min(2, len(others)))
            cats = target + filler
            random.shuffle(cats)
        else:
            cats = random.sample(all_cats, 8)
        selected = [(cat, *random.choice(stems_by_cat[cat])) for cat in cats]
        prompts.append(make_prompt(selected))
    return prompts


def build_translate_prompts(tag, count, themes, grammar_sets, make_prompt):
    kw = TAG_KEYWORDS.get(tag, [tag])
    grammar_pool = filter_by_keywords(grammar_sets, kw,
                                      lambda g: " ".join(g), min_results=2)
    theme_pool = filter_by_keywords(themes, kw, lambda t: t, min_results=3)
    return [make_prompt(random.choice(theme_pool), random.choice(grammar_pool))
            for _ in range(count)]


def build_gapfill_prompts(tag, count, scenarios, focuses, make_prompt):
    kw = TAG_KEYWORDS.get(tag, [tag])
    focus_pool = filter_by_keywords(focuses, kw, lambda f: f, min_results=2)
    scenario_pool = filter_by_keywords(scenarios, kw, lambda s: s, min_results=3)
    return [make_prompt(random.choice(scenario_pool), random.choice(focus_pool))
            for _ in range(count)]


def build_story_prompts(tag, count, scenarios, grammar_combos, char_pairs, make_prompt):
    kw = TAG_KEYWORDS.get(tag, [tag])
    grammar_pool = filter_by_keywords(grammar_combos, kw,
                                      lambda g: " ".join(g), min_results=3)
    scenario_pool = filter_by_keywords(scenarios, kw, lambda s: s, min_results=5)
    return [make_prompt(random.choice(scenario_pool),
                        random.choice(grammar_pool),
                        random.choice(char_pairs))
            for _ in range(count)]


def main():
    parser = argparse.ArgumentParser(
        description="Generate Slovak exercises focused on a specific topic tag"
    )
    parser.add_argument("--tag", help="Tag to focus on (use --list to see all)")
    parser.add_argument("--count", type=int, default=5,
                        help="Exercises to generate per type (default: 5)")
    parser.add_argument("--workers", type=int, default=3,
                        help="Parallel API workers (default: 3)")
    parser.add_argument("--output", type=str, default="bank",
                        help="Output directory (default: bank)")
    parser.add_argument("--list", action="store_true",
                        help="List available tags and exit")
    args = parser.parse_args()

    if args.list:
        print("Grammar tags:")
        for t in GRAMMAR_TAGS:
            has_drill = "  [drill+]" if t in TAG_TO_DRILL_CATS else ""
            print(f"  {t}{has_drill}")
        print("\nThematic tags:")
        for t in THEMATIC_TAGS:
            print(f"  {t}")
        return

    if not args.tag:
        parser.error("--tag is required  (use --list to see available tags)")
    if args.tag not in ALL_TAGS:
        print(f"Unknown tag: {args.tag!r}  — run with --list to see available tags")
        sys.exit(1)

    # Lazy imports — only needed for generation, not for --list
    try:
        from dotenv import load_dotenv
        load_dotenv()
        import anthropic
        from generate_bank import (
            generate_parallel, save_bank, load_progress,
            SCENARIOS, GRAMMAR_COMBOS, CHARACTER_PAIRS,
            TRANSLATE_THEMES, TRANSLATE_GRAMMAR_SETS,
            GAPFILL_SCENARIOS, GAPFILL_GRAMMAR_FOCUSES,
            DRILL_STEMS_BY_CATEGORY,
            make_story_prompt, make_translate_prompt,
            make_gapfill_prompt, make_drill_prompt,
        )
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with:  pip install anthropic python-dotenv")
        sys.exit(1)

    tag = args.tag
    count = args.count
    base_dir = Path(args.output)
    client = anthropic.Anthropic()
    bank = load_progress(base_dir)

    print(f"Generating up to {count} exercises per type focused on: '{tag}'")
    print(f"Current bank: {len(bank['stories'])}s / {len(bank['translates'])}t / "
          f"{len(bank['gapfills'])}g / {len(bank['drills'])}d\n")

    # Drills (only when a relevant drill category exists)
    if tag in TAG_TO_DRILL_CATS:
        print(f"Drills ({count})...")
        prompts = build_drill_prompts(tag, count, DRILL_STEMS_BY_CATEGORY, make_drill_prompt)
        new = generate_parallel(client, prompts, "drill", args.workers)
        bank["drills"].extend(new)
        print(f"  +{len(new)} drill sets")
    else:
        print(f"Drills: skipped (no drill category for '{tag}')")

    # Translates
    print(f"Translates ({count})...")
    prompts = build_translate_prompts(tag, count, TRANSLATE_THEMES,
                                      TRANSLATE_GRAMMAR_SETS, make_translate_prompt)
    new = generate_parallel(client, prompts, "translate", args.workers)
    bank["translates"].extend(new)
    print(f"  +{len(new)} translate sets")

    # Gap-fills
    print(f"Gap-fills ({count})...")
    prompts = build_gapfill_prompts(tag, count, GAPFILL_SCENARIOS,
                                    GAPFILL_GRAMMAR_FOCUSES, make_gapfill_prompt)
    new = generate_parallel(client, prompts, "gapfill", args.workers)
    bank["gapfills"].extend(new)
    print(f"  +{len(new)} gap-fill sets")

    # Stories
    print(f"Stories ({count})...")
    prompts = build_story_prompts(tag, count, SCENARIOS, GRAMMAR_COMBOS,
                                  CHARACTER_PAIRS, make_story_prompt)
    new = generate_parallel(client, prompts, "story", args.workers)
    bank["stories"].extend(new)
    print(f"  +{len(new)} stories")

    save_bank(bank, base_dir)
    print(f"\nSaved to {base_dir}/")

    # Re-tag and update topic_stats.json
    print("Re-running tagger...")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "tag_exercises.py")],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  ✓ Tags and stats updated")
    else:
        print(f"  Warning: tagger exited {result.returncode}:\n{result.stderr}")

    # Show resulting counts for the tag
    stats_path = base_dir / "topic_stats.json"
    if stats_path.exists():
        with open(stats_path) as f:
            stats = json.load(f)
        counts = {b: d["tag_counts"].get(tag, 0) for b, d in stats["by_bank"].items()}
        total = sum(counts.values())
        print(f"\nExercises tagged '{tag}': {total} total")
        for b, n in counts.items():
            if n:
                print(f"  {b}: {n}")


if __name__ == "__main__":
    main()
