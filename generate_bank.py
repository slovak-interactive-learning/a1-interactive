#!/usr/bin/env python3
"""
Slovak Practice Exercise Generator v2
=======================================
Generates a large, non-repetitive bank by sampling exercise parameters
from combinatorial pools BEFORE prompting. Each exercise gets a unique
combination of scenario, grammar focus, vocabulary domain, and characters.

Usage:
    pip install anthropic
    export ANTHROPIC_API_KEY="sk-ant-..."
    python generate_bank.py --stories 100 --translates 100 --gapfills 100 --drills 100
"""

import anthropic
import json
import argparse
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# PARAMETER POOLS — exercises are built from combinations of these
# ═══════════════════════════════════════════════════════════════

SCENARIOS = [
    "ordering breakfast at a café",
    "arriving late to a university seminar",
    "describing a new apartment to a friend on the phone",
    "a rushed morning routine — alarm didn't ring",
    "meeting an old friend unexpectedly on the street",
    "shopping for clothes — nothing fits",
    "a rainy day — plans change",
    "planning a birthday party for a roommate",
    "at a restaurant — the waiter brings the wrong order",
    "taking the wrong bus and getting lost",
    "first day at a new job",
    "visiting Košice as a tourist",
    "celebrating a name day with cake and presents",
    "cooking dinner — missing an ingredient",
    "a phone call with bad news from home",
    "at the doctor — a bad cold",
    "at the post office — sending a package",
    "studying for exams in the library",
    "a train delay — waiting at the station",
    "helping a lost tourist find their hotel",
    "at the market — haggling over fruit prices",
    "moving into a new dormitory room",
    "a job interview — nervous but prepared",
    "at the cinema — the film is sold out",
    "weekend hiking in the mountains",
    "a flat tire on the way to work",
    "hosting dinner guests — the food burns",
    "at a concert — the band is late",
    "registering at the university — long queue",
    "a power cut during a storm",
    "visiting grandparents in a village",
    "at the gym — trying a new sport",
    "lost keys — locked out of the apartment",
    "a video call with family abroad",
    "picking up a friend at the airport",
    "at the pharmacy — describing symptoms",
    "organising a class trip",
    "at a wedding reception",
    "walking the neighbour's dog",
    "a broken washing machine — calling a repairman",
    "waiting for exam results",
    "selling old furniture online",
    "a surprise visit from a friend",
    "volunteering at a charity event",
    "taking a Slovak language test",
    "at the bank — opening an account",
    "a picnic in the park that gets rained out",
    "babysitting a friend's children",
    "car won't start on a cold morning",
    "receiving a mysterious letter",
    # KK-specific scenarios
    "introducing yourself at a party — nationalities and languages",
    "describing your dormitory room — furniture and colours",
    "a conference in Bratislava — meeting people from different countries",
    "explaining your daily schedule with exact times",
    "describing what everyone is wearing — colours and clothes",
    "reading a newspaper article and discussing it",
    "giving directions to a tourist inside a building",
    "comparing two apartments — one old, one modern",
    "a Fašiangy celebration — traditional Slovak customs",
    "explaining Slovak name days to a foreign friend",
]

GRAMMAR_COMBOS = [
    # Unit 1-2: introductions, nationalities, byť
    ["present byť (som/si/je)", "nationality/country vocabulary", "question Odkiaľ ste? / Kde bývate?"],
    ["present byť (sme/ste/sú)", "accusative (direct object)", "adjective agreement (nationality adj)"],
    # Unit 3: adjectives, possessives, interior
    ["possessive (môj/tvoj/jej/náš)", "adjective opposites (veľký/malý, nový/starý)", "question čí?/aký?/ktorý?"],
    ["possessive from names (-ov/-ova, -in/-ina)", "adjective in predicate", "direction words (vpredu/vzadu/vľavo/vpravo)"],
    ["adjective opposites", "locative (v + room/place)", "demonstrative (ten/tá/to)"],
    # Unit 4: nominative, numerals, professions
    ["nominative plural (masc animate -i/-ia)", "numeral 2-4 + nominative plural", "profession vocabulary"],
    ["pluralia tantum (dvere/nožnice/okuliare)", "present tense (stáť→stojím)", "numeral 5+ genitive plural"],
    # Unit 5: accusative, modals, shopping, colours
    ["accusative (direct object)", "modal chcieť + infinitive", "colour + noun (červenú sukňu, modrý sveter)"],
    ["accusative (after na/do/cez/pre)", "modal musieť + infinitive", "irregular ísť present (idem/ideš)"],
    ["accusative (animate masculine -a)", "modal môcť + infinitive", "shopping vocabulary"],
    ["accusative (feminine -u ending)", "accusative pronouns (ho/ju/ich)", "colour adjective agreement"],
    # Unit 6: instrumental, restaurant, transport
    ["instrumental (s + noun)", "present tense (jesť/piť)", "food/drink vocabulary"],
    ["instrumental (bare = transport)", "instrumental preposition (za niekým)", "restaurant ordering (Dám si...)"],
    ["instrumental (nad/pod/pred/za/medzi)", "verbs V-VII (pozvať/žiť/niesť)", "instrumental (profession with byť)"],
    ["instrumental pronoun (so mnou/s ňou/s nimi)", "s/so spelling rule", "instrumental (means/tool: perom, kľúčom)"],
    # Unit 7: verb groups VIII-X, past tense, time, už/ešte
    ["past tense (irregular ísť→išiel/išla)", "time expression (o koľkej)", "už/ešte + past tense"],
    ["past tense (regular -l/-la/-li)", "present tense (spať/vidieť/stretnúť)", "time (pol + ordinal, štvrť na + cardinal)"],
    ["past tense (jesť→jedol, niesť→niesol)", "time (Koľko je hodín?)", "reflexive verb (začínať sa, končiť sa)"],
    # Unit 8: locative, dates, double negation, workplace
    ["locative (v/na + place)", "date (v pondelok, prvého januára)", "workplace vocabulary"],
    ["locative (o + topic)", "double negation (nikto nebol, nič nevidím)", "weekday + time"],
    ["locative (pri/po + noun)", "locative pronouns (o ňom/o nej/o nich)", "ordinal numbers"],
    ["locative (v + adj + noun)", "past tense (môcť→mohol)", "double negation (nikdy/nikam/nič)"],
    # Unit 9: reflexive verbs, review combos
    ["reflexive (volať sa, učiť sa, pýtať sa)", "past tense reflexive (stretol sa, stalo sa)", "word order with sa/si"],
    ["reflexive (prechádzať sa, tešiť sa)", "future perfective (stretneme sa, pozvem)", "aspect pair (kupovať/kúpiť)"],
    # Cross-unit combos
    ["instrumental (s + noun)", "locative (v + place)", "past tense (irregular)"],
    ["accusative (after na)", "modal musieť", "time (o koľkej)"],
    ["weather expression", "future (budem + infinitive)", "numeral + noun agreement"],
    ["possessive (jeho/jej/ich)", "locative (na poschodí)", "adjective (veľký/malý)"],
    ["instrumental (medzi + two nouns)", "present (irregular ísť)", "accusative pronoun (ho/ju)"],
]

CHARACTER_PAIRS = [
    ("Johanna", "Zuzana"), ("Carlo", "Róbert"), ("Marianna", "Mišo"),
    ("Johanna", "Carlo"), ("Zuzana", "Róbert"), ("Maja", "Johanna"),
    ("Mišo", "Carlo"), ("Róbert", "Marianna"), ("Johanna", "Mišo"),
    ("Zuzana", "Maja"),
]

TRANSLATE_THEMES = [
    "morning routine", "at the restaurant", "describing my apartment",
    "university schedule", "shopping for groceries", "weather forecast",
    "meeting a friend", "travel plans", "at the workplace", "family weekend",
    "cooking dinner", "health and illness", "hobbies and free time",
    "phone conversation", "giving directions", "at the cinema",
    "comparing two things", "asking for help", "celebrating a birthday",
    "weekend plans", "at the train station", "describing people",
    "at the bank or post office", "a typical Monday", "summer holidays",
    # Added for KK coverage:
    "introducing yourself and your nationality",
    "describing furniture and rooms in a flat",
    "what colour clothes to buy",
    "telling the time and making appointments",
    "talking about dates and weekdays",
    "professions and what people do",
    "saying what you already did and haven't done yet",
    "ordering food and drink at a restaurant",
    "describing the weather yesterday and tomorrow",
    "talking about a dormitory room",
]

TRANSLATE_GRAMMAR_SETS = [
    ["present tense (irregular verb)", "accusative (direct object)", "instrumental (s + noun)", "locative (v/na + place)"],
    ["past tense (irregular)", "modal verb (musieť/môcť)", "future perfective", "double negation"],
    ["reflexive verb (sa/si)", "time expression (o koľkej)", "accusative (animate masc -a)", "instrumental (bare = tool/transport)"],
    ["locative (o + topic)", "past tense (regular)", "numeral + genitive plural", "possessive adjective (môj/tvoj)"],
    ["accusative (after na/do)", "instrumental (profession)", "present irregular (jesť/piť)", "word order emphasis"],
    ["future (budem + inf)", "locative (pronoun o ňom/nej)", "instrumental (nad/pod/pred/za)", "past (ísť→išiel)"],
    ["aspect pair (impf→pf)", "accusative (feminine -u)", "modal chcieť + infinitive", "nominative plural"],
    ["present (vedieť/vidieť)", "instrumental (medzi)", "past (jesť→jedol)", "date/day expression"],
    ["weather expression", "double negation (nikto/nič/nikdy)", "accusative pronoun (ho/ju)", "instrumental (so + cluster)"],
    ["locative (pri + place)", "ordinal number + time", "reflexive (stretnúť sa)", "past modal (nemohla)"],
    # Added for KK coverage:
    ["byť conjugation (som/si/je)", "nationality adjective", "possessive from name (-ov/-in)", "question (odkiaľ/kde)"],
    ["adjective opposites", "čí/aký/ktorý question", "demonstrative (ten/tá/to)", "direction (vpredu/vzadu)"],
    ["numeral 2-4 + nom pl vs 5+ gen pl", "pluralia tantum", "present (stáť→stojím)", "profession"],
    ["colour + accusative noun", "modal môcť", "accusative (cez/pre)", "irregular ísť present"],
    ["už + past positive vs ešte ne- + past negative", "time (pol/štvrť/trištvrte)", "reflexive (začínať sa/končiť sa)", "locative (po + noun)"],
]

GAPFILL_SCENARIOS = [
    "Johanna's morning at the dormitory",
    "Carlo ordering lunch at the canteen",
    "Zuzana describing her new apartment",
    "a weekend trip to the mountains",
    "Róbert's first day at a new company",
    "shopping for a birthday present",
    "Marianna cooking dinner for friends",
    "a visit to the doctor",
    "Mišo's daily routine at university",
    "planning a name day celebration",
    "a rainy Saturday in Bratislava",
    "Johanna writing an email home",
    "waiting for a delayed train",
    "a phone call between Carlo and his family",
    "describing the weather this week",
    "Zuzana and Johanna at a café",
    "preparing for a Slovak exam",
    "Róbert moving to a new flat",
    "a day at the conference",
    "weekend at the grandparents' village",
    "Maja looking for a part-time job",
    "a cinema evening that goes wrong",
    "describing classmates and their nationalities",
    "Mišo buying furniture for his room",
]

GAPFILL_GRAMMAR_FOCUSES = [
    "case endings (mix of accusative, instrumental, locative)",
    "verb conjugation (present tense, mix of regular and irregular)",
    "past tense forms (regular and irregular, with auxiliaries)",
    "prepositions + correct case (v/na/s/do/za/pred/o)",
    "possessives and adjective agreement",
    "modal verbs (chcieť/musieť/môcť) + infinitive",
    "pronouns in different cases (accusative, instrumental, locative)",
    "time expressions (o koľkej, pol, štvrť na)",
    "future tense (budem + infinitive and perfective present)",
    "reflexive verbs (sa/si placement and forms)",
    "numeral + noun agreement (2-4 vs 5+)",
    "už/ešte with past tense",
    "double negation (nikto/nič/nikdy + ne-)",
    "adjective opposites and agreement (gender/number)",
    "mix of all cases in one paragraph",
]

DRILL_STEMS_BY_CATEGORY = {
    "instrumental": [
        ("s ___ (kamarátka)", "with a friend (f.)"),
        ("___ (vlak)", "by train"),
        ("pred ___ (škola)", "in front of the school"),
        ("s ___ (mlieko)", "with milk"),
        ("pod ___ (stôl)", "under the table"),
        ("so ___ (šľahačka)", "with whipped cream"),
        ("za ___ (dom)", "behind the house"),
        ("nad ___ (rieka)", "above the river"),
        ("medzi ___ a ___ (banka, obchod)", "between the bank and shop"),
        ("Je ___ (učiteľka)", "She is a teacher"),
        ("___ (električka)", "by tram"),
        ("s ___ (nový kolega)", "with a new colleague"),
        ("Píše ___ (pero)", "writes with a pen"),
        ("pod ___ (most)", "under the bridge"),
        ("s ___ (horúci čaj)", "with hot tea"),
        ("pred ___ (kino)", "in front of the cinema"),
        ("za ___ (hotel)", "behind the hotel"),
        ("___ (autobus)", "by bus"),
        ("s ___ (kamarát)", "with a friend (m.)"),
        ("nad ___ (mesto)", "above the city"),
        # Added: adj+noun combos, more vocabulary
        ("s ___ (veľké okno → veľkým oknom)", "with a big window"),
        ("s ___ (nová práčka)", "with a new washing machine"),
        ("Otvoril dvere ___ (kľúč)", "opened the door with a key"),
        ("___ (auto)", "by car"),
        ("medzi ___ a ___ (babka, dedko)", "between grandma and grandpa"),
        ("s ___ (český kamarát)", "with a Czech friend"),
        ("pred ___ (univerzita)", "in front of the university"),
        ("Je ___ (programátor)", "He is a programmer"),
    ],
    "accusative": [
        ("Vidím ___ (profesor)", "I see the professor"),
        ("Idem na ___ (prednáška)", "going to a lecture"),
        ("Čítam ___ (kniha)", "reading a book"),
        ("Kúpim ___ (nové auto)", "I'll buy a new car"),
        ("Pozývam ___ (kamarátka)", "inviting a friend (f.)"),
        ("Hľadám ___ (kľúč)", "looking for a key"),
        ("Vidíš ___ (ona)?", "Do you see her?"),
        ("Idem do ___ (knižnica)", "going to the library"),
        ("Pozvem ___ (profesor) na kávu", "inviting prof for coffee"),
        ("Máme ___ (nový študent)", "We have a new student"),
        ("Čakám na ___ (autobus)", "waiting for the bus"),
        ("Potrebujem ___ (silná káva)", "I need strong coffee"),
        ("Nevidím ___ (on)", "I don't see him"),
        ("Pozeráme ___ (film)", "watching a film"),
        ("Hľadá ___ (práca)", "looking for work"),
        # Added: colours, more animate, prepositions
        ("Kúpim ___ (červená sukňa)", "I'll buy a red skirt"),
        ("Chcem ___ (modrý sveter)", "I want a blue sweater"),
        ("Idem cez ___ (park)", "going through the park"),
        ("Kupujem to pre ___ (mama)", "buying it for mum"),
        ("Poznáš ___ (Carlo)?", "Do you know Carlo?"),
        ("Mám ___ (dobrý kamarát)", "I have a good friend (m.)"),
    ],
    "locative": [
        ("v ___ (Bratislava)", "in Bratislava"),
        ("na ___ (univerzita)", "at the university"),
        ("o ___ (nový film)", "about a new film"),
        ("v ___ (veľký dom)", "in a big house"),
        ("pri ___ (stanica)", "near the station"),
        ("na ___ (tretie poschodie)", "on the third floor"),
        ("v ___ (malá kuchyňa)", "in a small kitchen"),
        ("o ___ (oni)", "about them"),
        ("po ___ (obed)", "after lunch"),
        ("na ___ (pošta)", "at the post office"),
        ("v ___ (nemocnica)", "in the hospital"),
        ("o ___ (slovenská kultúra)", "about Slovak culture"),
        ("pri ___ (okno)", "by the window"),
        ("na ___ (balkón)", "on the balcony"),
        ("v ___ (centrum)", "in the centre"),
        # Added: more prepositions, rooms, weekday-like
        ("v ___ (kúpeľňa)", "in the bathroom"),
        ("na ___ (chodba)", "in the hallway"),
        ("v ___ (obchod)", "in the shop"),
        ("o ___ (on)", "about him"),
        ("o ___ (ja)", "about me"),
        ("po ___ (slovensky → slovensky is adverb; use: Slovensko)", "around Slovakia"),
        ("v ___ (reštaurácia)", "in the restaurant"),
        ("na ___ (stanica)", "at the station"),
    ],
    "nom_plural": [
        ("Tí ___ sú vysokí (študent)", "students are tall"),
        ("Tie ___ sú veľké (okno)", "windows are big"),
        ("___ sú drahé (kniha)", "books are expensive"),
        ("Naši ___ sú milí (sused)", "neighbours are nice"),
        ("___ bývajú tu (Talian)", "Italians live here"),
        ("Tie ___ sú moderné (auto)", "cars are modern"),
        ("___ čakajú (žena)", "women are waiting"),
        ("___ hovoria slovensky (študentka)", "students (f.) speak Slovak"),
        ("Tí ___ sú unavení (muž)", "men are tired"),
        ("___ sú zatvorené (obchod)", "shops are closed"),
        # Added: more variety
        ("___ sú na stole (pohár)", "glasses are on the table"),
        ("Tí ___ sú z Nemecka (kamarát)", "friends are from Germany"),
        ("___ sú nové (stolička)", "chairs are new"),
        ("Tie ___ sú pekné (izba)", "rooms are nice"),
    ],
    "pronoun": [
        ("Poď so ___ (ja)", "Come with me [instr]"),
        ("Hovorí o ___ (oni)", "talking about them [loc]"),
        ("Vidím ___ (on)", "I see him [acc]"),
        ("Idem s ___ (ty)", "going with you [instr]"),
        ("Sedí medzi ___ a ___ (on, ona)", "between him and her [instr]"),
        ("Stojí pred ___ (my)", "in front of us [instr]"),
        ("Hovorí o ___ (ty)", "about you [loc]"),
        ("Čaká na ___ (ona)", "waiting for her [acc]"),
        ("Príď s ___ (my)", "Come with us [instr]"),
        ("Myslí na ___ (ja)", "thinking about me [acc]"),
        # Added: more variety, ono
        ("Dieťa je choré, musí byť s ___ (ono)", "must be with it [instr]"),
        ("Hovorí o ___ (ona)", "about her [loc]"),
        ("Vidíš ___ (oni)?", "Do you see them? [acc]"),
        ("Pôjdem s ___ (vy)", "I'll go with you pl [instr]"),
    ],
    "present": [
        ("Oni ___ veľa (jesť)", "They eat a lot"),
        ("Ty ___ kávu? (piť)", "Do you drink coffee?"),
        ("___ po slovensky? (vedieť, ty)", "Do you know Slovak?"),
        ("Ja ___ dobre (spať)", "I sleep well"),
        ("My ___ do školy (ísť)", "We go to school"),
        ("Oni ___ to (vidieť)", "They see it"),
        ("Ja ___ to (chcieť)", "I want it"),
        ("Ty ___ to urobiť? (môcť)", "Can you do it?"),
        ("On ___ pri okne (stáť)", "He stands by the window"),
        ("My ___ slovensky (hovoriť)", "We speak Slovak"),
        ("Ona ___ knihy (niesť)", "She carries books"),
        ("Vy ___ tu (bývať)", "You live here"),
        # Added: more verb groups, persons
        ("Ona ___ Johanna (volať sa)", "She is called Johanna"),
        ("My ___ na seminár (ísť)", "We go to a seminar"),
        ("Ja ___ ísť domov (musieť)", "I must go home"),
        ("Oni ___ to urobiť (môcť)", "They can do it"),
        ("Ona ___ veľmi dobre (variť)", "She cooks very well"),
        ("Ty ___ na prednášku (ísť)", "You go to the lecture"),
    ],
    "past": [
        ("Johanna ___ do knižnice (ísť)", "Johanna went to the library"),
        ("My ___ unavení (byť)", "We were tired"),
        ("On ___ tašku (niesť)", "He carried a bag"),
        ("Deti ___ zmrzlinu (jesť)", "Children ate ice cream"),
        ("Zuzana ___ na to (zabudnúť)", "Zuzana forgot about it"),
        ("Ona ___ zaspať (môcť, neg)", "She couldn't fall asleep"),
        ("My ___ domov autom (ísť)", "We went home by car"),
        ("On ___ celý deň (pracovať)", "He worked all day"),
        ("Carlo ___ novú prácu (nájsť)", "Carlo found a new job"),
        ("Vy ___ to? (vedieť)", "Did you know that?"),
        ("Ja ___ dobrú knihu (čítať)", "I read a good book"),
        ("Oni ___ na oslavu (prísť)", "They came to the party"),
        # Added: reflexive past, aspect
        ("Seminár ___ o ôsmej (začať sa)", "The seminar started at 8"),
        ("Oni ___ v parku (stretnúť sa)", "They met in the park"),
        ("Ona ___ novú knihu (kúpiť)", "She bought a new book"),
        ("Výstava ___ v sobotu (skončiť sa)", "The exhibition ended on Saturday"),
    ],
    # ═══ NEW CATEGORIES for KK A1 coverage ═══
    "numeral": [
        ("___ (2) študenti čakajú (dva/dvaja)", "Two students are waiting"),
        ("Mám ___ (3) sestry (tri)", "I have three sisters"),
        ("V triede je ___ (5) študentov (päť)", "There are 5 students in class"),
        ("Kúpil ___ (4) knihy (štyri)", "He bought 4 books"),
        ("Máme ___ (7) stupňov (sedem)", "We have 7 degrees"),
        ("Bolo tam ___ (12) ľudí (dvanásť)", "There were 12 people"),
        ("Čakáme ___ (2) hodiny (dve)", "We're waiting 2 hours"),
        ("Na stole sú ___ (3) poháre (tri)", "There are 3 glasses on the table"),
        ("V dome je ___ (6) izieb (šesť)", "There are 6 rooms in the house"),
        ("Zostáva ___ (1) minúta (jedna)", "One minute remains"),
    ],
    "time": [
        ("Je ___ (7:00 → sedem hodín)", "It's 7:00"),
        ("Stretneme sa o ___ (5:30 → pol šiestej)", "We'll meet at 5:30"),
        ("Je ___ (8:15 → štvrť na deväť)", "It's 8:15"),
        ("Začíname o ___ (2:00 → druhej)", "We start at 2:00"),
        ("Je ___ (10:45 → trištvrte na jedenásť)", "It's 10:45"),
        ("Seminár je od ___ do ___ (8:00-8:45)", "Seminar is from 8 to 8:45"),
        ("Je ___ (12:30 → pol jednej)", "It's 12:30"),
        ("Prídeme o ___ (6:15 → štvrť na sedem)", "We'll come at 6:15"),
        ("Autobus ide o ___ (3:00 → tretej)", "The bus goes at 3:00"),
        ("Je ___ (11:00 → jedenásť hodín)", "It's 11:00"),
    ],
    "possessive": [
        ("___ byt je veľký (ja → Môj)", "My apartment is big"),
        ("To je ___ auto? (ty → tvoje)", "Is that your car?"),
        ("___ dom je ten vľavo (Juraj → Jurajov)", "Juraj's house is the one on the left"),
        ("___ izba je pekná (Zuzana → Zuzanina)", "Zuzana's room is nice"),
        ("___ je to kniha? (čí → Čia)", "Whose book is it?"),
        ("___ kamarát je z Talianska (ona → Jej)", "Her friend is from Italy"),
        ("To je ___ kancelária (my → naša)", "That is our office"),
        ("___ sestra sa volá Katka (on → Jeho)", "His sister is called Katka"),
        ("___ dom je moderný (Róbert → Róbertov)", "Róbert's house is modern"),
        ("___ spolubývajúca je Nemka (Mária → Máriina)", "Mária's roommate is German"),
    ],
    "adjective": [
        ("Byt je ___ a ___ (veľký/moderný)", "The flat is big and modern"),
        ("Opak slova 'lacný' je ___ (drahý)", "The opposite of cheap is..."),
        ("Opak slova 'nový' je ___ (starý)", "The opposite of new is..."),
        ("Káva je ___ a ___ (horúci/silný → horúca, silná)", "Coffee is hot and strong (f. agreement)"),
        ("Auto je ___ (showing, rýchly → rýchle)", "The car is fast (n. agreement)"),
        ("___ sveter je v skrini (modrý)", "The blue sweater is in the wardrobe"),
        ("Izba je ___ a ___ (tmavý/úzky → tmavá, úzka)", "The room is dark and narrow"),
        ("Opak slova 'veselý' je ___ (smutný)", "The opposite of happy is..."),
        ("Tie topánky sú ___ (červený → červené)", "Those shoes are red (pl. agreement)"),
        ("Dom je ___ a ___ (pekný/ekologický)", "The house is nice and ecological"),
    ],
    "uz_este": [
        ("1816 bicykel, v 1820: ___ mali bicykel (už)", "By 1820, they already had a bicycle"),
        ("1895 žiletka, v 1880: muži ___ nemali žiletku (ešte)", "In 1880, men didn't have a razor yet"),
        ("___ som jedla (Už → already ate)", "I already ate"),
        ("___ som nejedla (Ešte → haven't eaten yet)", "I haven't eaten yet"),
        ("Johanna si ___ objednala knihy (už)", "Johanna already ordered books"),
        ("Referát ___ nie je hotový (ešte)", "The presentation isn't ready yet"),
        ("1879 žiarovka, v 1889: žiarovka ___ bola (už)", "By 1889, the lightbulb already existed"),
        ("___ ste boli v Košiciach? (Už → already)", "Have you already been to Košice?"),
    ],
}

SYSTEM_PROMPT = """You generate Slovak language exercises for an A1-A2 learner (Krížom Krážom textbook).

GRAMMAR KNOWN: Cases (nominative, accusative, instrumental, locative) in sg+pl with nouns, adjectives, pronouns. Present tense (groups I-X, irregulars: byť/jesť/piť/vedieť/chcieť/môcť/musieť/ísť/spať/vidieť/stáť/niesť). Past tense (regular + irregular: ísť→išiel, jesť→jedol, niesť→niesol, môcť→mohol). Future (budem+inf, perfective present). Modals, reflexive verbs, aspect basics, possessives, adjective opposites, numerals+agreement, double negation, word order, time expressions, dates.

CRITICAL: Use correct Slovak diacritics. Write natural Slovak. Output ONLY valid JSON."""


def make_story_prompt(scenario, grammar_combo, characters):
    char1, char2 = characters
    g1, g2, g3 = grammar_combo
    return f"""Write a 15-sentence Slovak short-story. If it's a dialogue (it doesn't have to be, whatever makes sense, keep it varied), start sentences with names e.g. Johanna:<what she said.>.

SCENARIO: {scenario}
MAIN CHARACTERS: {char1} and {char2}
REQUIRED GRAMMAR (use all three naturally): {g1}; {g2}; {g3}

Return JSON:
{{"title":"<Slovak title>","titleEn":"<English title>","sentences":[{{"sk":"...","en":"..."}}],"grammarFocus":"<which grammar appears where>","newWords":[{{"sk":"...","en":"..."}}]}}

Rules: sentences max 12 words each. Include 1-2 new words with glosses. Small narrative arc with payoff."""


def make_translate_prompt(theme, grammar_set):
    g_list = "; ".join(grammar_set)
    return f"""Generate 4 English sentences to translate into Slovak. Theme: "{theme}".

Each sentence MUST test a DIFFERENT grammar point from this list: {g_list}
Order: easy → hard. Sentences: 6-10 words each.

Return JSON:
{{"theme":"{theme}","sentences":[{{"en":"...","sk":"...","altSk":["..."],"hint":"grammar hint","focus":"grammar point"}}]}}

Include questions, negatives, different tenses. Natural conversational style.

CRITICAL for altSk — include ALL naturally correct Slovak alternatives, not just word-order variants:
- Different prepositions that are both correct (e.g. "do kina" vs "na film", "na pláž" vs "na more")
- Synonym verbs (e.g. "pozerať" vs "sledovať", "hovoriť" vs "rozprávať", "prísť" vs "prísť")
- With or without optional subject pronoun (e.g. "Idem" vs "Ja idem")
- Different but equally valid nouns/phrases for the same concept
- Different word orders when meaning is identical
Aim for 2-4 entries in altSk whenever genuine alternatives exist. Only skip altSk entries if there is truly only one natural way to say it."""


def make_gapfill_prompt(scenario, grammar_focus):
    return f"""Write a short Slovak paragraph (4-5 sentences, ~40-50 words) about: {scenario}

Then create a gap-fill exercise from it with exactly 6 blanks. Each blank should test: {grammar_focus}

Return JSON:
{{"scenario":"{scenario}","scenarioEn":"<English description>","text":"<the full correct paragraph in Slovak>","textEn":"<full English translation>","gaps":[{{"position":"<the word/phrase that becomes a blank>","correct":"<correct answer>","options":["<3 wrong options>","<correct answer>"],"hint":"<what grammar this tests, 5 words max>"}}]}}

RULES:
- The "position" field should be the exact word(s) from "text" that get blanked out
- "options" must have exactly 4 items including the correct answer, shuffled randomly
- Wrong options must be plausible Slovak forms (real words, wrong case/tense/form)
- Each blank should test something different (different case, different verb form, etc.)
- Use natural everyday Slovak with correct diacritics
- Keep sentences short (8-12 words max each)"""


def make_drill_prompt(selected_stems):
    items_desc = []
    for cat, stem, context in selected_stems:
        items_desc.append(f'  category="{cat}", example_stem="{stem}", concept="{context}"')
    items_str = "\n".join(items_desc)

    return f"""Generate 8 grammar drill questions. For each entry below, invent a NEW stem that illustrates the SAME grammar concept — do NOT copy the example stem. Use different vocabulary, a different noun or verb, a different sentence frame.

{items_str}

For each question:
- Create your own stem in the format "... ___ (lemma)" where the blank tests the grammar concept. The hint in parentheses must be ONLY the base/lemma form — NEVER include the answer or a "→ answer" hint inside the parentheses
- Provide 4 plausible options (including the correct one)
- Give the correct answer, the full correct Slovak form, and a brief explanation (under 10 words)

Return JSON:
{{"questions":[{{"category":"...","stem":"...","context":"...","correct":"...","options":["4 opts"],"fullWord":"...","explanation":"..."}}]}}

All options must be real Slovak forms. Use correct diacritics. Make each stem feel fresh and varied."""


SCHEMAS = {
    "story": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "titleEn": {"type": "string"},
            "grammarFocus": {"type": "string"},
            "sentences": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"sk": {"type": "string"}, "en": {"type": "string"}},
                    "required": ["sk", "en"],
                    "additionalProperties": False
                }
            },
            "newWords": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"sk": {"type": "string"}, "en": {"type": "string"}},
                    "required": ["sk", "en"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["title", "titleEn", "grammarFocus", "sentences", "newWords"],
        "additionalProperties": False
    },
    "translate": {
        "type": "object",
        "properties": {
            "theme": {"type": "string"},
            "sentences": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "en": {"type": "string"},
                        "sk": {"type": "string"},
                        "altSk": {"type": "array", "items": {"type": "string"}},
                        "hint": {"type": "string"},
                        "focus": {"type": "string"}
                    },
                    "required": ["en", "sk", "altSk", "hint", "focus"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["theme", "sentences"],
        "additionalProperties": False
    },
    "gapfill": {
        "type": "object",
        "properties": {
            "scenario": {"type": "string"},
            "scenarioEn": {"type": "string"},
            "text": {"type": "string"},
            "textEn": {"type": "string"},
            "gaps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "position": {"type": "string"},
                        "correct": {"type": "string"},
                        "options": {"type": "array", "items": {"type": "string"}},
                        "hint": {"type": "string"}
                    },
                    "required": ["position", "correct", "options", "hint"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["scenario", "scenarioEn", "text", "textEn", "gaps"],
        "additionalProperties": False
    },
    "drill": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "stem": {"type": "string"},
                        "context": {"type": "string"},
                        "correct": {"type": "string"},
                        "options": {"type": "array", "items": {"type": "string"}},
                        "fullWord": {"type": "string"},
                        "explanation": {"type": "string"}
                    },
                    "required": ["category", "stem", "context", "correct", "options", "fullWord", "explanation"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["questions"],
        "additionalProperties": False
    }
}


def call_api(client, prompt, exercise_type, max_retries=6):
    schema = SCHEMAS[exercise_type]
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                output_config={"format": {"type": "json_schema", "schema": schema}}
            )
            text = response.content[0].text
            return json.loads(text)
        except anthropic.RateLimitError as e:
            wait = 2 ** attempt
            print(f"    Rate limited, waiting {wait}s (attempt {attempt+1})")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            if e.status_code == 529:  # overloaded
                wait = 2 ** attempt
                print(f"    Overloaded, waiting {wait}s (attempt {attempt+1})")
                time.sleep(wait)
            else:
                print(f"    Attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
        except Exception as e:
            print(f"    Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
    return None


BANK_KEYS = ["stories", "translates", "gapfills", "drills"]


def key_to_file(base_dir, key):
    return base_dir / f"{key}.json"


def load_progress(base_dir):
    bank = {}
    for key in BANK_KEYS:
        path = key_to_file(base_dir, key)
        if path.exists():
            with open(path) as f:
                bank[key] = json.load(f)
        else:
            bank[key] = []
    return bank


def save_bank(bank, base_dir):
    base_dir.mkdir(parents=True, exist_ok=True)
    for key in BANK_KEYS:
        with open(key_to_file(base_dir, key), "w", encoding="utf-8") as f:
            json.dump(bank[key], f, ensure_ascii=False, indent=2)
    # Write a tiny metadata file for the home screen stats
    meta = {key: len(bank[key]) for key in BANK_KEYS}
    with open(base_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)


def generate_parallel(client, tasks, exercise_type, workers=5):
    """Run API calls in parallel with a semaphore to cap concurrent in-flight requests.
    Returns results in original order."""
    lock = threading.Lock()
    semaphore = threading.Semaphore(workers)
    completed = [0]
    total = len(tasks)
    results = []

    def run(idx, prompt):
        with semaphore:
            result = call_api(client, prompt, exercise_type)
        with lock:
            completed[0] += 1
            print(f"  [{completed[0]}/{total}] done")
        return idx, result

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run, i, prompt): i for i, prompt in enumerate(tasks)}
        for future in as_completed(futures):
            idx, result = future.result()
            if result:
                results.append((idx, result))
    results.sort(key=lambda x: x[0])
    return [r for _, r in results]


def main():
    parser = argparse.ArgumentParser(description="Generate Slovak practice exercises (v2)")
    parser.add_argument("--stories", type=int, default=0)
    parser.add_argument("--translates", type=int, default=0)
    parser.add_argument("--gapfills", type=int, default=0)
    parser.add_argument("--drills", type=int, default=0)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--output", type=str, default="bank",
                        help="Output directory (default: bank/)")
    args = parser.parse_args()

    base_dir = Path(args.output)
    client = anthropic.Anthropic()
    bank = load_progress(base_dir)

    print(f"Loaded: {len(bank['stories'])}s / {len(bank['translates'])}t / "
          f"{len(bank['gapfills'])}g / {len(bank['drills'])}d")

    # ── STORIES ──
    remaining = args.stories - len(bank["stories"])
    if remaining > 0:
        print(f"\n{'='*50}\nGenerating {remaining} stories ({args.workers} parallel)\n{'='*50}")
        all_combos = [(s, g, c) for s in SCENARIOS for g in GRAMMAR_COMBOS for c in CHARACTER_PAIRS]
        random.shuffle(all_combos)
        params = all_combos[:remaining]
        prompts = [make_story_prompt(s, g, c) for s, g, c in params]
        bank["stories"].extend(generate_parallel(client, prompts, "story", args.workers))
        save_bank(bank, base_dir)

    # ── TRANSLATES ──
    remaining = args.translates - len(bank["translates"])
    if remaining > 0:
        print(f"\n{'='*50}\nGenerating {remaining} translate sets ({args.workers} parallel)\n{'='*50}")
        all_combos = [(t, g) for t in TRANSLATE_THEMES for g in TRANSLATE_GRAMMAR_SETS]
        random.shuffle(all_combos)
        params = all_combos[:remaining]
        prompts = [make_translate_prompt(t, g) for t, g in params]
        bank["translates"].extend(generate_parallel(client, prompts, "translate", args.workers))
        save_bank(bank, base_dir)

    # ── GAPFILLS ──
    remaining = args.gapfills - len(bank["gapfills"])
    if remaining > 0:
        print(f"\n{'='*50}\nGenerating {remaining} gap-fill sets ({args.workers} parallel)\n{'='*50}")
        all_combos = [(s, g) for s in GAPFILL_SCENARIOS for g in GAPFILL_GRAMMAR_FOCUSES]
        random.shuffle(all_combos)
        params = all_combos[:remaining]
        prompts = [make_gapfill_prompt(s, g) for s, g in params]
        bank["gapfills"].extend(generate_parallel(client, prompts, "gapfill", args.workers))
        save_bank(bank, base_dir)

    # ── DRILLS ──
    remaining = args.drills - len(bank["drills"])
    if remaining > 0:
        print(f"\n{'='*50}\nGenerating {remaining} drill sets ({args.workers} parallel)\n{'='*50}")
        categories = list(DRILL_STEMS_BY_CATEGORY.keys())
        prompts = []
        for _ in range(remaining):
            picked_cats = random.sample(categories, 8)
            selected = []
            for cat in picked_cats:
                stem, ctx = random.choice(DRILL_STEMS_BY_CATEGORY[cat])
                selected.append((cat, stem, ctx))
            random.shuffle(selected)
            prompts.append(make_drill_prompt(selected))
        bank["drills"].extend(generate_parallel(client, prompts, "drill", args.workers))
        save_bank(bank, base_dir)

    # ── SUMMARY ──
    print(f"\n{'='*50}")
    print(f"DONE! Files in {base_dir}/")
    print(f"  Stories:    {len(bank['stories'])}")
    print(f"  Translates: {len(bank['translates'])}")
    print(f"  Gapfills:   {len(bank['gapfills'])}")
    print(f"  Drills:     {len(bank['drills'])}")
    # Variety stats
    combos = len(SCENARIOS) * len(GRAMMAR_COMBOS) * len(CHARACTER_PAIRS)
    print(f"\n  Story variety: {len(SCENARIOS)} scenarios × {len(GRAMMAR_COMBOS)} grammar combos × "
          f"{len(CHARACTER_PAIRS)} char pairs = {combos} unique combinations")
    tcombos = len(TRANSLATE_THEMES) * len(TRANSLATE_GRAMMAR_SETS)
    print(f"  Translate variety: {len(TRANSLATE_THEMES)} themes × {len(TRANSLATE_GRAMMAR_SETS)} grammar sets = {tcombos}")


if __name__ == "__main__":
    main()