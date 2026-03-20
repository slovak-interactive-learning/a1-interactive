#!/usr/bin/env python3
"""
Tag exercises with topic taxonomy for Krizom Krazom A1 Slovak learning app.

Adds a `tags` array to every exercise in the JSON bank files.
Tags are drawn from a two-tier taxonomy: grammar topics + thematic topics.

Usage:
    python3 tag_exercises.py
    python3 tag_exercises.py --dry-run   # print stats only, don't write
"""

import json
import re
import argparse
from pathlib import Path

BANK_DIR = Path(__file__).parent / "bank"

# ─────────────────────────────────────────────────────────────────
# TAXONOMY
# ─────────────────────────────────────────────────────────────────

GRAMMAR_TAGS = [
    "nominative",
    "accusative",
    "genitive",
    "dative",
    "locative",
    "instrumental",
    "nom_plural",
    "adjectives",
    "pronouns",
    "present_tense",
    "past_tense",
    "future_tense",
    "modals",
    "reflexive",
    "numerals",
    "time_date",
    "negation",
    "possessive",
    "uz_este",
]

THEMATIC_TAGS = [
    "daily_routine",
    "food_drink",
    "transport_travel",
    "home_apartment",
    "university_work",
    "family_people",
    "shopping",
    "weather",
    "health",
    "free_time",
    "social",
    "directions",
]

ALL_TAGS = GRAMMAR_TAGS + THEMATIC_TAGS

# ─────────────────────────────────────────────────────────────────
# GRAMMAR KEYWORD → TAG RULES
# Applied to free text (grammarFocus, hints, focus fields)
# ─────────────────────────────────────────────────────────────────

GRAMMAR_KEYWORD_RULES = [
    # Each rule: (tag, [keywords/phrases that signal this tag])
    ("accusative",    ["accusative", "akuzatív", "akuzativ"]),
    ("genitive",      ["genitive", "genitív", "genitiv", "genitive plural", "numeral + gen"]),
    ("dative",        ["dative", "datív", "dativ"]),
    ("locative",      ["locative", "lokál", "lokal", "lokativ", "locatív"]),
    ("instrumental",  ["instrumental", "inštrumentál", "inštrumental"]),
    ("nom_plural",    ["nominative plural", "nom_plural", "nom. pl", "nominatív pl",
                       "plurál", "plural nominative"]),
    ("nominative",    ["nominative", "nominatív"]),
    ("adjectives",    ["adjective", "adjektív", "adjektiv", "adj.", "colour", "color",
                       "colors", "colours", "prídavné"]),
    ("pronouns",      ["pronoun", "pronomin", "zámeno", "zámená", "demonstrative",
                       "personal pronoun"]),
    ("present_tense", ["present tense", "present irregular", "present regular",
                       "prítomný čas", "present (", "byť conjugation"]),
    ("past_tense",    ["past tense", "minulý čas", "past regular", "past irregular"]),
    ("future_tense",  ["future", "budúci čas", "budem +", "budem+"]),
    ("modals",        ["modal", "chcieť", "musieť", "môcť", "vedieť +", "vedieť+"]),
    ("reflexive",     ["reflexive", "zvratné", "sa/si", "reflexív"]),
    ("numerals",      ["numeral", "číslovk", "numeral +", "cardinal", "ordinal"]),
    ("time_date",     ["time expression", "čas", "date expression", "dátum",
                       "o koľkej", "telling the time", "weekday", "ordinal date"]),
    ("negation",      ["double negation", "negation", "zápor", "nikto", "nič",
                       "nikdy", "nem-"]),
    ("possessive",    ["possessive", "privlastňov", "môj", "tvoj", "jeho", "jej",
                       "náš", "váš", "ich", "possessive adjective", "possessive from"]),
    ("uz_este",       ["už", "ešte", "already", "still", "already/still", "uz_este",
                       "uz/este"]),
]

# ─────────────────────────────────────────────────────────────────
# THEMATIC KEYWORD → TAG RULES
# Applied to theme, scenario, title fields
# ─────────────────────────────────────────────────────────────────

THEMATIC_KEYWORD_RULES = [
    ("daily_routine",      ["morning routine", "daily routine", "denná rutina",
                            "morning", "alarm", "waking up", "getting up",
                            "evening routine", "daily schedule"]),
    ("food_drink",         ["restaurant", "food", "drink", "café", "coffee",
                            "breakfast", "lunch", "dinner", "cooking", "eating",
                            "ordering food", "jedál", "jedlo", "reštaurácia",
                            "kaviareň", "kaviarni", "jedáleň", "canteen",
                            "meal", "menu", "obed", "večera", "raňajky",
                            "varí", "recipe", "groceries", "grocery"]),
    ("transport_travel",   ["transport", "travel", "train", "bus", "taxi", "car",
                            "driving", "station", "airport", "journey", "trip",
                            "vlak", "autobus", "cestovanie", "getting lost",
                            "directions to", "tourist", "city tour", "sightseeing",
                            "delayed", "delay", "route", "metro", "tram"]),
    ("home_apartment",     ["apartment", "flat", "room", "furniture", "moving",
                            "home", "house", "byt", "izba", "nábytok", "sťahuje",
                            "dormitory", "internát", "housework", "cleaning",
                            "living room", "bedroom", "kitchen", "bathroom"]),
    ("university_work",    ["university", "exam", "lecture", "seminar", "study",
                            "studying", "class", "school", "homework", "library",
                            "skúška", "škola", "profesor", "workplace",
                            "job", "work", "office", "colleague", "career",
                            "part-time", "brigáda", "schedule", "timetable"]),
    ("family_people",      ["family", "parents", "mother", "father", "sister",
                            "brother", "grandparent", "rodina", "mama", "otec",
                            "sestra", "brat", "relatives", "children", "kids",
                            "describing people", "appearance", "character"]),
    ("shopping",           ["shopping", "shop", "buy", "store", "market",
                            "nakupovanie", "obchod", "clothes", "clothes shop",
                            "price", "pay", "birthday present", "darček",
                            "what colour", "gift"]),
    ("weather",            ["weather", "forecast", "rain", "sun", "wind",
                            "snow", "počasie", "predpoveď", "cold", "hot",
                            "temperature", "seasons", "summer", "winter"]),
    ("health",             ["health", "doctor", "hospital", "sick", "ill",
                            "illness", "zdravie", "lekár", "nemocnica",
                            "medicine", "appointment", "feeling", "symptom"]),
    ("free_time",          ["hobby", "hobbies", "sport", "cinema", "film",
                            "music", "reading", "free time", "voľný čas",
                            "weekend", "recreation", "game", "party", "festival",
                            "concert", "theatre", "koníčky"]),
    ("social",             ["birthday", "celebration", "name day", "meeting",
                            "friend", "party", "visit", "invitation",
                            "oslava", "meniny", "kamarát", "stretnutie",
                            "introducing yourself", "introduction",
                            "at a café", "phone conversation", "phone call"]),
    ("directions",         ["directions", "map", "street", "location",
                            "navigate", "smer", "ulica", "kde je",
                            "orientácia", "left", "right", "straight",
                            "town centre", "city centre"]),
]


def grammar_tags_from_text(text: str) -> set[str]:
    """Extract grammar tags from free text using keyword matching."""
    text_lower = text.lower()
    found = set()
    for tag, keywords in GRAMMAR_KEYWORD_RULES:
        for kw in keywords:
            if kw.lower() in text_lower:
                found.add(tag)
                break
    return found


def thematic_tags_from_text(text: str) -> set[str]:
    """Extract thematic tags from free text using keyword matching."""
    text_lower = text.lower()
    found = set()
    for tag, keywords in THEMATIC_KEYWORD_RULES:
        for kw in keywords:
            if kw.lower() in text_lower:
                found.add(tag)
                break
    return found


# ─────────────────────────────────────────────────────────────────
# DRILL CATEGORY → TAG MAPPING (direct 1-to-1)
# ─────────────────────────────────────────────────────────────────

DRILL_CATEGORY_TO_TAG = {
    "instrumental": "instrumental",
    "accusative":   "accusative",
    "locative":     "locative",
    "nom_plural":   "nom_plural",
    "pronoun":      "pronouns",
    "present":      "present_tense",
    "past":         "past_tense",
    "numeral":      "numerals",
    "time":         "time_date",
    "possessive":   "possessive",
    "adjective":    "adjectives",
    "uz_este":      "uz_este",
}

# ─────────────────────────────────────────────────────────────────
# PER-TYPE TAGGING FUNCTIONS
# ─────────────────────────────────────────────────────────────────


def tag_drill(exercise: dict) -> list[str]:
    tags = set()
    for q in exercise.get("questions", []):
        cat = q.get("category", "")
        if cat in DRILL_CATEGORY_TO_TAG:
            tags.add(DRILL_CATEGORY_TO_TAG[cat])
        # Also parse explanation text for extra context
        explanation = q.get("explanation", "")
        if explanation:
            tags |= grammar_tags_from_text(explanation)
    return sorted(tags)


def tag_translate(exercise: dict) -> list[str]:
    tags = set()

    # Thematic tag from theme
    theme = exercise.get("theme", "")
    if theme:
        tags |= thematic_tags_from_text(theme)

    # Grammar tags from per-sentence focus fields and hints
    for sentence in exercise.get("sentences", []):
        focus = sentence.get("focus", "")
        hint = sentence.get("hint", "")
        if focus:
            tags |= grammar_tags_from_text(focus)
        if hint:
            tags |= grammar_tags_from_text(hint)

    return sorted(tags)


def tag_gapfill(exercise: dict) -> list[str]:
    tags = set()

    # Thematic tags from scenario
    scenario_en = exercise.get("scenarioEn", "")
    scenario_sk = exercise.get("scenario", "")
    if scenario_en:
        tags |= thematic_tags_from_text(scenario_en)
    if scenario_sk:
        tags |= thematic_tags_from_text(scenario_sk)

    # Grammar tags from gap hints
    for gap in exercise.get("gaps", []):
        hint = gap.get("hint", "")
        if hint:
            tags |= grammar_tags_from_text(hint)

    return sorted(tags)


def tag_story(exercise: dict) -> list[str]:
    tags = set()

    # Grammar tags from grammarFocus (verbose text)
    grammar_focus = exercise.get("grammarFocus", "")
    if grammar_focus:
        tags |= grammar_tags_from_text(grammar_focus)

    # Thematic tags from title and sentences
    title_en = exercise.get("titleEn", "")
    title_sk = exercise.get("title", "")
    if title_en:
        tags |= thematic_tags_from_text(title_en)
    if title_sk:
        tags |= thematic_tags_from_text(title_sk)

    # Scan sentence English translations for thematic tags
    for sentence in exercise.get("sentences", []):
        en = sentence.get("en", "")
        if en:
            tags |= thematic_tags_from_text(en)

    # Also scan new words for thematic context
    for word in exercise.get("newWords", []):
        en = word.get("en", "")
        if en:
            tags |= thematic_tags_from_text(en)

    return sorted(tags)


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

BANK_FILES = {
    "drills":     ("drills.json",     tag_drill),
    "translates": ("translates.json", tag_translate),
    "gapfills":   ("gapfills.json",   tag_gapfill),
    "stories":    ("stories.json",    tag_story),
}


def print_stats(name: str, exercises: list[dict]) -> None:
    tag_counts: dict[str, int] = {}
    untagged = 0
    for ex in exercises:
        t = ex.get("tags", [])
        if not t:
            untagged += 1
        for tag in t:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    print(f"\n  {name} ({len(exercises)} exercises, {untagged} untagged):")
    for tag in ALL_TAGS:
        count = tag_counts.get(tag, 0)
        if count:
            bar = "█" * (count // 2)
            print(f"    {tag:<20} {count:3d} {bar}")


def build_stats(bank_name: str, exercises: list[dict]) -> dict:
    """Return a stats dict for a bank (tag counts + compact per-exercise tag index)."""
    tag_counts: dict[str, int] = {}
    untagged = 0
    exercise_tags: list[list[str]] = []
    for ex in exercises:
        t = ex.get("tags", [])
        exercise_tags.append(t)
        if not t:
            untagged += 1
        for tag in t:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return {
        "total": len(exercises),
        "untagged": untagged,
        "tag_counts": {tag: tag_counts.get(tag, 0) for tag in ALL_TAGS},
        "exercise_tags": exercise_tags,  # compact index: list of tag lists
    }


def write_stats_file(all_stats: dict) -> None:
    """Write bank/topic_stats.json with per-bank and aggregate tag counts."""
    # Build aggregates across all banks
    aggregate: dict[str, int] = {}
    total_exercises = 0
    for bank_stats in all_stats.values():
        total_exercises += bank_stats["total"]
        for tag, count in bank_stats["tag_counts"].items():
            aggregate[tag] = aggregate.get(tag, 0) + count

    output = {
        "total_exercises": total_exercises,
        "taxonomy": {
            "grammar": GRAMMAR_TAGS,
            "thematic": THEMATIC_TAGS,
        },
        "by_bank": all_stats,
        "aggregate_tag_counts": {tag: aggregate.get(tag, 0) for tag in ALL_TAGS},
    }

    stats_path = BANK_DIR / "topic_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Stats written to bank/topic_stats.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tag Slovak exercises with topic taxonomy")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print stats only, don't write files")
    args = parser.parse_args()

    all_stats: dict[str, dict] = {}

    for bank_name, (filename, tagger) in BANK_FILES.items():
        path = BANK_DIR / filename
        print(f"Processing {filename}...")

        with open(path, encoding="utf-8") as f:
            exercises = json.load(f)

        for ex in exercises:
            ex["tags"] = tagger(ex)

        stats = build_stats(bank_name, exercises)
        all_stats[bank_name] = stats

        if not args.dry_run:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(exercises, f, ensure_ascii=False, indent=2)
            print(f"  ✓ Written {len(exercises)} exercises with tags")
        else:
            print_stats(bank_name, exercises)

    if not args.dry_run:
        write_stats_file(all_stats)
        print("\nDone. Run with --dry-run to see tag statistics.")
    else:
        print("\n(Dry run — no files written)")


if __name__ == "__main__":
    main()
