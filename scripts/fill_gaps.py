#!/usr/bin/env python3
"""
fill_gaps.py — Fill thematic and grammatical gaps in the A1 exercise bank.

Targets (from CURRICULUM.md):
  Thematic : colours (L5), clothing (L5), professions (L4),
             countries/nationalities (L2), daily_routine (thin)
  Grammar  : verb conjugation groups I-IV (L2), V-VII (L6), VIII-X (L7),
             byť present (L2), negation/double-negation (L8)

Usage:
    python fill_gaps.py                       # all topics
    python fill_gaps.py --topic colours       # single topic
    python fill_gaps.py --list                # show available topics
    python fill_gaps.py --workers 5           # more parallelism (default 3)
"""

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

BANK_DIR = Path(__file__).parent.parent / "bank"

# ─────────────────────────────────────────────────────────────────
# GAP DEFINITIONS
# Each gap specifies how many of each exercise type to generate and
# provides pools of themes/scenarios/grammar combos to sample from.
# ─────────────────────────────────────────────────────────────────

GAPS = {

    # ── THEMATIC GAPS ────────────────────────────────────────────

    "colours": {
        "translates": 8, "gapfills": 4, "stories": 2,
        "translate_themes": [
            "describing the colours of clothes in a shop",
            "choosing what colour to paint a room",
            "what colours do you see in the Slovak flag?",
            "describing someone's appearance and outfit",
            "favourite colours and why",
            "colours in nature — seasons and landscapes",
            "picking a birthday gift by colour preference",
            "mixing colours in an art class",
        ],
        "translate_grammar": [
            ["colour adjective agreement (masc/fem/neut)", "accusative (direct object)", "adjective in predicate"],
            ["colour + noun in accusative (červenú sukňu, modrý sveter)", "adjective opposites (svetlý/tmavý)", "present tense (chcieť/kupovať)"],
            ["colour adjective agreement (plural)", "demonstrative (ten/tá/to)", "possessive (môj/tvoj)"],
        ],
        "gapfill_scenarios": [
            "Johanna is choosing clothes in a shop and asks about colours",
            "Carlo describes the colours in his new apartment",
            "Zuzana explains the colours of the Slovak national flag to a friend",
            "Marianna packs a suitcase and mentions the colours of her clothes",
        ],
        "gapfill_grammar": [
            "colour adjective agreement (gender: červený/červená/červené)",
            "accusative + colour adjective (kúpim červenú sukňu)",
            "adjective in predicate vs attribute (sveter je modrý / modrý sveter)",
            "demonstrative + colour + noun (tá zelená taška)",
        ],
        "story_scenarios": [
            "shopping for new clothes — everything is the wrong colour",
            "an art class where students describe paintings using Slovak colour adjectives",
        ],
        "story_grammar": [
            ["colour adjective agreement", "accusative (direct object)", "present tense (chcieť/kupovať)"],
            ["adjective opposites (svetlý/tmavý, jasný/bledý)", "colour + noun in accusative", "demonstrative (ten/tá/to)"],
        ],
    },

    "clothing": {
        "translates": 8, "gapfills": 4, "stories": 2,
        "translate_themes": [
            "shopping for clothes — asking for size and colour",
            "packing a suitcase for a weekend trip",
            "describing what people are wearing at a party",
            "buying a winter coat in a Slovak shop",
            "getting dressed for a job interview",
            "describing a friend's style",
            "what to wear in different Slovak weather",
            "comparing two outfits in a fitting room",
        ],
        "translate_grammar": [
            ["accusative (buying clothes: kúpim kabát)", "colour + clothing noun in accusative", "modal chcieť + infinitive"],
            ["accusative (animate vs inanimate)", "adjective agreement with clothing nouns", "present tense (obliecť si / nosiť)"],
            ["accusative pronouns (ho/ju/ich)", "adjective opposites (dlhý/krátky, úzky/široký)", "demonstrative + noun"],
        ],
        "gapfill_scenarios": [
            "Johanna is trying on clothes in a shop and talking to the shop assistant",
            "Róbert packs a bag for a conference and describes what he is taking",
            "Zuzana describes what her friends are wearing at a birthday party",
            "Carlo buys a Slovak folk costume as a souvenir",
        ],
        "gapfill_grammar": [
            "accusative of clothing nouns (kúpim sveter / vidím sukňu)",
            "adjective agreement with clothing (nový kabát / nová bunda / nové tričko)",
            "colour + clothing in accusative (chcem modrú košeľu)",
            "present tense verbs: obliecť si, nosiť, kupovať, skúšať si",
        ],
        "story_scenarios": [
            "first day at a new job — deciding what to wear",
            "a clothes swap event at the university dormitory",
        ],
        "story_grammar": [
            ["accusative of clothing nouns", "colour adjective agreement", "modal musieť + infinitive"],
            ["adjective opposites (dlhý/krátky)", "accusative + preposition (pre koho)", "present tense clothing verbs"],
        ],
    },

    "professions": {
        "translates": 8, "gapfills": 4, "stories": 2,
        "translate_themes": [
            "introducing yourself and your job at a conference",
            "asking someone what they do for work",
            "describing a typical workday for different professions",
            "talking about what you want to be",
            "professions in a Slovak family",
            "a job fair at the university",
            "asking about someone's workplace and role",
            "comparing two different professions",
        ],
        "translate_grammar": [
            ["profession with byť (Som lekár/lekárka)", "noun gender (prof masc/fem: učiteľ/učiteľka)", "question Čo ste / Čo robíte?"],
            ["nominative (profession as predicate)", "present byť conjugation (som/si/je/sme/ste/sú)", "adjective + profession (dobrý lekár)"],
            ["instrumental (profession: pracujem ako...)", "present tense (pracovať/robiť)", "workplace vocabulary"],
        ],
        "gapfill_scenarios": [
            "Johanna introduces herself and her profession at a conference in Bratislava",
            "Carlo asks classmates about their future career plans",
            "Zuzana describes what various family members do for work",
            "Marianna fills in a form with her profession and workplace details",
        ],
        "gapfill_grammar": [
            "profession with byť — gender agreement (lekár/lekárka, učiteľ/učiteľka)",
            "question forms: Čo ste? / Kde pracujete? / Ako sa voláte?",
            "instrumental 'pracujem ako' + profession",
            "present tense: pracovať, robiť, učiť, liečiť, predávať",
        ],
        "story_scenarios": [
            "a career day at university — students present their dream professions",
            "Carlo meets people from different professions on his first day in Slovakia",
        ],
        "story_grammar": [
            ["profession with byť", "noun gender (masc/fem profession pairs)", "present tense (pracovať/robiť)"],
            ["nominative plural of professions", "question Čo robíte? / Kde pracujete?", "instrumental 'ako + profession'"],
        ],
    },

    "countries": {
        "translates": 8, "gapfills": 4, "stories": 2,
        "translate_themes": [
            "introducing yourself — where are you from?",
            "talking about which countries your classmates come from",
            "describing a country you have visited",
            "nationality adjectives and languages spoken",
            "asking and saying where people live",
            "a map of Europe — naming countries in Slovak",
            "an international students' meeting in Bratislava",
            "comparing Slovakia with another country",
        ],
        "translate_grammar": [
            ["present byť (Som z Nemecka / Som Nemec/Nemka)", "nationality adjective agreement", "question Odkiaľ ste? / Z ktorej krajiny?"],
            ["country names in Slovak", "nationality nouns (masc/fem: Francúz/Francúzka)", "present tense (bývať/žiť/pochádzať)"],
            ["personal pronouns (ja/ty/on/ona/my/vy/oni)", "negation (Nie som z Talianska)", "locative (bývam v + country)"],
        ],
        "gapfill_scenarios": [
            "Johanna introduces herself and her German nationality to new Slovak classmates",
            "students at an international conference say where they come from",
            "Carlo explains the difference between Italy and Slovakia to a child",
            "Zuzana fills in a form asking for nationality and country of birth",
        ],
        "gapfill_grammar": [
            "Som z + country (Som z Nemecka / Som z Talianska) — byť + z",
            "nationality nouns gender: Nemec/Nemka, Talian/Talianka, Francúz/Francúzka",
            "nationality adjectives: nemecký/á/é, taliansky/á/é, slovenský/á/é",
            "locative: bývam v Nemecku / v Taliansku / na Slovensku",
        ],
        "story_scenarios": [
            "an Erasmus welcome event — students introduce themselves and their nationalities",
            "a geography quiz at the Slovak language school — naming countries and capitals",
        ],
        "story_grammar": [
            ["byť + z + country", "nationality noun (masc/fem)", "personal pronouns (ja/ty/on/ona)"],
            ["nationality adjective agreement", "locative v/na + country", "question Odkiaľ ste? / Kde bývate?"],
        ],
    },

    "daily_routine": {
        "translates": 8, "gapfills": 4, "stories": 0,  # stories already covered
        "translate_themes": [
            "a student's morning routine step by step",
            "evening routine before bed",
            "a busy Monday schedule with times",
            "comparing morning routines with a flatmate",
            "a lazy Sunday versus a busy weekday",
            "what time do you get up and go to sleep?",
            "routine disrupted — alarm didn't go off",
            "planning tomorrow's schedule",
        ],
        "translate_grammar": [
            ["present tense (regular verbs: vstávať, umývať sa, raňajkovať)", "time expressions (o siedmej, o pol ôsmej)", "reflexive verbs (vstávať sa → umývať sa)"],
            ["past tense (what I did this morning)", "time (o koľkej)", "already/not yet (už/ešte)"],
            ["present tense irregular (ísť, jesť, piť)", "daily routine verbs", "reflexive (učiť sa, obliekať sa)"],
        ],
        "gapfill_scenarios": [
            "Mišo describes his typical university morning from alarm to lecture",
            "Johanna compares her morning routine in Germany to her routine in Slovakia",
            "Carlo explains his evening wind-down routine to his flatmate",
            "Zuzana's unusual Sunday routine — no alarm, slow breakfast",
        ],
        "gapfill_grammar": [
            "present tense routine verbs: vstávať, umývať sa, raňajkovať, odchádzať",
            "time expressions with o + time (o siedmej, o pol ôsmej, o štvrť na deväť)",
            "reflexive routine verbs: obliekať sa, učiť sa, pripravovať sa",
            "past tense: what the character did this morning (vstal, išiel, jedol)",
        ],
        "story_scenarios": [],
        "story_grammar": [],
    },

    # ── GRAMMAR GAPS ─────────────────────────────────────────────

    "verb_groups_I_IV": {
        "translates": 6, "gapfills": 3, "stories": 2,
        "translate_themes": [
            "introducing yourself using volať sa",
            "talking about studying Slovak",
            "asking if someone speaks your language",
            "describing what people do at university",
            "talking about what you understand or don't understand",
            "a conversation about hobbies — what do you study / work on?",
        ],
        "translate_grammar": [
            ["verb group I: volať sa conjugation (volám sa / voláš sa / volá sa)", "personal pronouns", "question Ako sa voláš?"],
            ["verb group II: hovoriť/rozumieť (hovorím/hovoríš/hovorí)", "negation (nehovorím po slovensky)", "present tense all persons"],
            ["verb group III: študovať (študujem/študuješ/študuje)", "verb group IV: rozumieť (rozumiem/rozumieš)", "question formation"],
        ],
        "gapfill_scenarios": [
            "Johanna introduces herself using volať sa and talks about what she studies",
            "Carlo struggles to understand Slovak and practises the verbs hovoriť and rozumieť",
            "students at a language class conjugate common group I-IV verbs",
        ],
        "gapfill_grammar": [
            "volať sa conjugation: volám sa / voláš sa / volá sa / voláme sa / voláte sa / volajú sa",
            "group II verb hovoriť: hovorím/hovoríš/hovorí/hovoríme/hovoríte/hovoria",
            "group III verb študovať: študujem/študuješ/študuje/študujeme/študujete/študujú",
        ],
        "story_scenarios": [
            "first day of Slovak class — students introduce themselves with volať sa and say what languages they speak",
            "Carlo calls a Slovak help line and struggles with hovoriť and rozumieť",
        ],
        "story_grammar": [
            ["volať sa all persons", "group II hovoriť/rozumieť", "negation (nerozumiem / nehovorím)"],
            ["group III študovať", "group IV rozumieť", "personal pronouns + present tense"],
        ],
    },

    "verb_groups_V_VII": {
        "translates": 5, "gapfills": 2, "stories": 1,
        "translate_themes": [
            "inviting a friend to a party (pozvať)",
            "describing city life (žiť v meste)",
            "carrying things home from the market (niesť)",
            "planning a dinner and deciding who brings what",
            "a phone call inviting someone to an event",
        ],
        "translate_grammar": [
            ["verb group V: pozvať (pozval/pozvem)", "accusative (direct object: pozvem kamaráta)", "future perfective"],
            ["verb group VI: žiť (žijem/žiješ/žije)", "locative (žijem v Bratislave)", "present tense all persons"],
            ["verb group VII: niesť (nesiem/nesieš/nesie)", "accusative (niesť tašku)", "instrumental (niesť s niekým)"],
        ],
        "gapfill_scenarios": [
            "Maja invites friends to her name-day party using pozvať",
            "Zuzana describes everyday life in Bratislava using žiť",
        ],
        "gapfill_grammar": [
            "group V pozvať conjugation and usage: pozval/pozvala, pozvem/pozveš",
            "group VI žiť and group VII niesť present tense forms",
        ],
        "story_scenarios": [
            "planning a dinner party — who brings what, who invites whom",
        ],
        "story_grammar": [
            ["verb group V pozvať", "verb group VI žiť", "verb group VII niesť"],
        ],
    },

    "verb_groups_VIII_X": {
        "translates": 5, "gapfills": 2, "stories": 1,
        "translate_themes": [
            "a bad night's sleep (spať)",
            "bumping into someone unexpectedly (stretnúť)",
            "watching a film at the cinema (vidieť)",
            "past tense stories using sleep, meet, see",
            "asking if someone slept well or saw the news",
        ],
        "translate_grammar": [
            ["verb group VIII: spať (spím/spíš/spí)", "past tense spať (spal/spala/spali)", "time expression (koľko hodín)"],
            ["verb group IX: stretnúť (stretnem/stretneš — perfective)", "past stretnúť (stretol/stretla)", "reflexive stretnúť sa"],
            ["verb group X: vidieť (vidím/vidíš/vidí)", "past vidieť (videl/videla)", "accusative (vidím + object)"],
        ],
        "gapfill_scenarios": [
            "Mišo tells Carlo about a strange night — he couldn't sleep and saw something odd",
            "Johanna describes meeting an old friend she hadn't seen in years",
        ],
        "gapfill_grammar": [
            "group VIII spať: spím/spíš/spí/spíme/spíte/spia + past spal/spala/spali",
            "group X vidieť: vidím/vidíš/vidí + group IX stretnúť sa (past: stretol sa)",
        ],
        "story_scenarios": [
            "a late night at the dormitory — students couldn't sleep, met in the kitchen, saw something funny",
        ],
        "story_grammar": [
            ["verb group VIII spať", "verb group IX stretnúť (sa)", "verb group X vidieť"],
        ],
    },

    "time_date": {
        "translates": 20, "gapfills": 5, "stories": 0,
        "translate_themes": [
            "telling the time — full hours and half hours",
            "telling the time — quarter past and quarter to",
            "making an appointment and agreeing on a time",
            "a busy university timetable with exact times",
            "train and bus departure times",
            "daily schedule from morning to evening",
            "asking what time it is",
            "days of the week and planning the week",
            "months and seasons of the year",
            "writing and saying the date",
            "talking about what day and date something happens",
            "asking when an event starts and ends",
            "how long something takes",
            "weekend plans — what time and which day",
            "public transport schedule",
            "restaurant booking — date and time",
            "calendar — birthdays and name days",
            "lecture schedule at university",
            "arrival and departure times on a trip",
            "time zones — what time is it in different cities?",
        ],
        "translate_grammar": [
            ["Koľko je hodín? — full hour (Je sedem hodín.)", "time with o + hour (o siedmej)", "AM/PM expressions (ráno/poobede/večer)"],
            ["half hour: pol + ordinal genitive (pol ôsmej)", "quarter past: štvrť na + cardinal (štvrť na osem)", "quarter to: trištvrte na + cardinal"],
            ["weekday expressions (v pondelok, v utorok)", "date: prvého januára / piateho mája", "ordinal numbers (prvý, druhý, tretí...)"],
            ["numerals 5+ with hodín (päť hodín, desať hodín)", "numerals 2-4 with hodiny (dve hodiny, tri hodiny)", "time duration (trvá + acc)"],
            ["od...do... = from...to... (od ôsmej do štvrtej)", "o koľkej? — asking the time", "past tense + time expression"],
            ["months (január, február, ...)", "seasons (jar, leto, jeseň, zima)", "v + month/season (v januári, na jar)"],
            ["day + time combo (v pondelok o deviatej)", "already/not yet with time (už je neskoro / ešte je skoro)", "Kedy? / O koľkej? question forms"],
        ],
        "gapfill_scenarios": [
            "Johanna tells Carlo what time her lectures start and end each day",
            "Zuzana checks the train timetable and tells Mišo when they need to leave",
            "Róbert describes his weekly schedule — which days he works and at what times",
            "Maja makes a doctor's appointment — agreeing on a date and time",
            "Carlo asks about opening hours of a shop and a museum in Bratislava",
            "Johanna writes out her university timetable in an email to her parents",
            "Mišo and Zuzana arrange to meet — they negotiate a day, date and time",
            "a receptionist takes a restaurant reservation — date, time and number of guests",
            "Carlo describes how long his morning routine takes step by step",
            "Johanna explains what month and season she arrived in Slovakia",
        ],
        "gapfill_grammar": [
            "telling the time: Je + hour + hodín; o + hour for 'at what time'",
            "pol + ordinal (pol ôsmej), štvrť na + cardinal (štvrť na osem)",
            "weekdays in locative (v pondelok, v utorok, v stredu...)",
            "ordinal date: prvého, druhého, piateho + month in locative",
            "duration: trvá + accusative (trvá dve hodiny / päť minút)",
            "od + time + do + time (od deviatej do piatej)",
            "Kedy? / O koľkej? / Ktorý dátum? — question words for time",
            "months in locative: v januári, vo februári, v marci...",
            "past tense + time: prišiel o ôsmej / skončil v stredu",
            "already/still with time: Je už neskoro. / Ešte je skoro.",
        ],
        "story_scenarios": [],
        "story_grammar": [],
    },

    "negation": {
        "translates": 5, "gapfills": 3, "stories": 0,
        "translate_themes": [
            "saying you don't have or don't do something",
            "double negation — nobody, nothing, never",
            "correcting a misunderstanding politely",
            "saying what you can't or don't want to do",
            "a quiz where all the answers are negative",
        ],
        "translate_grammar": [
            ["simple negation (ne- prefix: neviem, nemám, nechcem)", "negation + present tense", "word order with negation"],
            ["double negation (nikto nič nehovorí, nikdy nejdem)", "nikto/nič/nikdy/nikam/nijaký", "present and past tense"],
            ["double negation in past (nikto neprišiel)", "negation of byť (nie som / nie sú)", "negative questions (Naozaj nevieš?)"],
        ],
        "gapfill_scenarios": [
            "Johanna explains to her landlord that nobody came and nothing happened",
            "Carlo insists he never said anything and nobody told him anything",
            "Zuzana politely refuses several suggestions using negative forms",
        ],
        "gapfill_grammar": [
            "double negation: nikto + ne-, nič + ne-, nikdy + ne-",
            "simple ne- negation of common verbs (neviem, nemám, nechcem, nemôžem)",
            "double negation in past tense (nikto neprišiel, nič nevidela)",
        ],
        "story_scenarios": [],
        "story_grammar": [],
    },
}


# ─────────────────────────────────────────────────────────────────
# PROMPT BUILDERS
# ─────────────────────────────────────────────────────────────────

def make_targeted_translate_prompt(theme, grammar_set):
    g_list = "; ".join(grammar_set)
    return f"""Generate 4 English sentences to translate into Slovak. Theme: "{theme}".

Each sentence MUST test a DIFFERENT grammar point from this list: {g_list}
Order: easy → hard. Sentences: 6-10 words each.

Return JSON:
{{"theme":"{theme}","sentences":[{{"en":"...","sk":"...","altSk":["..."],"hint":"grammar hint","focus":"grammar point"}}]}}

Include questions, negatives, different tenses. Natural conversational style.

CRITICAL for altSk — include ALL naturally correct Slovak alternatives, not just word-order variants.
Aim for 2-4 entries in altSk whenever genuine alternatives exist.

CRITICAL: NEVER use genitive case or dative case. Stick to nominative, accusative, instrumental, locative only."""


def make_targeted_gapfill_prompt(scenario, grammar_focus):
    return f"""Write a short Slovak paragraph (4-5 sentences, ~40-50 words) about: {scenario}

Then create a gap-fill exercise from it with exactly 6 blanks. Each blank should test: {grammar_focus}

Return JSON:
{{"scenario":"{scenario}","scenarioEn":"<English description>","text":"<full correct Slovak paragraph>","textEn":"<full English translation>","gaps":[{{"position":"<word/phrase from text>","correct":"<correct answer>","options":["<3 wrong options>","<correct answer>"],"hint":"<grammar tested, 5 words max>"}}]}}

RULES:
- "position" must be exact words from "text"
- "options" must have exactly 4 items including correct answer, shuffled
- Wrong options must be plausible Slovak forms (real words, wrong form)
- Each blank tests something different
- Use natural everyday Slovak with correct diacritics
- Sentences max 12 words each
- NEVER use genitive case or dative case"""


def make_targeted_story_prompt(scenario, grammar_combo, characters):
    char1, char2 = characters
    g1, g2, g3 = grammar_combo
    return f"""Write a 15-sentence Slovak short story or dialogue about: {scenario}
Main characters: {char1} and {char2}
Required grammar (use all three naturally): {g1}; {g2}; {g3}

Return JSON:
{{"title":"<Slovak title>","titleEn":"<English title>","sentences":[{{"sk":"...","en":"..."}}],"grammarFocus":"<which grammar appears where>","newWords":[{{"sk":"...","en":"..."}}]}}

Rules:
- Sentences max 12 words each
- Include 1-2 new vocabulary words with glosses
- Small narrative arc
- NEVER use genitive case or dative case"""


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

CHARACTER_PAIRS = [
    ("Johanna", "Zuzana"), ("Carlo", "Róbert"), ("Marianna", "Mišo"),
    ("Johanna", "Carlo"), ("Zuzana", "Róbert"), ("Maja", "Johanna"),
    ("Mišo", "Carlo"), ("Róbert", "Marianna"), ("Johanna", "Mišo"),
    ("Zuzana", "Maja"),
]


def build_prompts_for_gap(gap_name, gap_def):
    prompts = []  # list of (prompt_str, exercise_type)

    themes = gap_def["translate_themes"]
    grammars = gap_def["translate_grammar"]
    for _ in range(gap_def["translates"]):
        theme = random.choice(themes)
        grammar = random.choice(grammars)
        prompts.append((make_targeted_translate_prompt(theme, grammar), "translate"))

    scenarios = gap_def["gapfill_scenarios"]
    gf_grammars = gap_def["gapfill_grammar"]
    for _ in range(gap_def["gapfills"]):
        scenario = random.choice(scenarios)
        grammar = random.choice(gf_grammars)
        prompts.append((make_targeted_gapfill_prompt(scenario, grammar), "gapfill"))

    story_scenarios = gap_def.get("story_scenarios", [])
    story_grammars = gap_def.get("story_grammar", [])
    if story_scenarios and story_grammars:
        for _ in range(gap_def.get("stories", 0)):
            scenario = random.choice(story_scenarios)
            grammar = random.choice(story_grammars)
            chars = random.choice(CHARACTER_PAIRS)
            prompts.append((make_targeted_story_prompt(scenario, grammar, chars), "story"))

    return prompts


def main():
    parser = argparse.ArgumentParser(description="Fill thematic/grammar gaps in the A1 exercise bank")
    parser.add_argument("--topic", help="Generate only this topic (use --list to see all)")
    parser.add_argument("--list", action="store_true", help="List topics and exit")
    parser.add_argument("--workers", type=int, default=3, help="Parallel API workers (default: 3)")
    parser.add_argument("--output", default="bank", help="Output directory (default: bank)")
    args = parser.parse_args()

    if args.list:
        print("Available topics:")
        for name, gap in GAPS.items():
            t = gap["translates"]
            g = gap["gapfills"]
            s = gap.get("stories", 0)
            print(f"  {name:<22} {t} translates, {g} gapfills, {s} stories")
        return

    try:
        from dotenv import load_dotenv
        load_dotenv()
        import anthropic
        from generate_bank import generate_parallel, save_bank, load_progress, flatten_translates
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with:  pip install anthropic python-dotenv")
        sys.exit(1)

    client = anthropic.Anthropic()
    base_dir = Path(args.output)
    bank = load_progress(base_dir)

    topics_to_run = [args.topic] if args.topic else list(GAPS.keys())
    if args.topic and args.topic not in GAPS:
        print(f"Unknown topic: {args.topic!r}  — run with --list to see available topics")
        sys.exit(1)

    total_new = {"translates": 0, "gapfills": 0, "stories": 0}

    for topic in topics_to_run:
        gap = GAPS[topic]
        print(f"\n── {topic} ──")
        prompts = build_prompts_for_gap(topic, gap)

        by_type: dict[str, list[str]] = {}
        for prompt, etype in prompts:
            by_type.setdefault(etype, []).append(prompt)

        for etype, plist in by_type.items():
            print(f"  {etype}: {len(plist)} prompts...")
            new = generate_parallel(client, plist, etype, args.workers)
            key_map = {"translate": "translates", "gapfill": "gapfills", "story": "stories"}
            key = key_map.get(etype, etype)
            if key == "translates":
                new = flatten_translates(new)
            bank[key].extend(new)
            total_new[key] = total_new.get(key, 0) + len(new)
            print(f"    +{len(new)} {key}")

    save_bank(bank, base_dir)
    print(f"\nSaved to {base_dir}/")
    print(f"New exercises: {total_new}")

    print("Re-running tagger...")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "tag_exercises.py")],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  ✓ Tags and stats updated")
    else:
        print(f"  Warning: tagger exited {result.returncode}:\n{result.stderr}")

    # Summary
    stats_path = base_dir / "topic_stats.json"
    if stats_path.exists():
        with open(stats_path) as f:
            stats = json.load(f)
        print(f"\nBank totals after fill:")
        for bname, bdata in stats["by_bank"].items():
            print(f"  {bname}: {bdata['total']}")
        print(f"  TOTAL: {stats['total_exercises']}")


if __name__ == "__main__":
    main()
