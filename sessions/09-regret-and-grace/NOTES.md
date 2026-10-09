# Session 9 — planning notes

**Not published.** `_config.yml` excludes `sessions/*/NOTES.md` from the Jekyll
build, so this file is for whoever builds the session, not for the class.

---

## Scope and renumbering (2026-10-08)

The class ran out of time in Session 8 before Part 5 (*Two hearts*, Genesis
6:5–8). David asked for the next lesson to pick up there and focus on:

1. **Genesis 6:5** — where the class stopped: in spite of the Nephilim, the
   verdict falls on *humankind*. Humans answer for their own actions.
2. **"The LORD regretted"** (6:6–7) — and the different ways it has been read.
3. **The first mention of grace / favor** (6:8).
4. **The structure of the Flood narrative** — the doublets, and how they are
   read: **chiasm**, **J/P**, **Sinai**.
5. **A closing callback to *Atrahasis* and *Gilgamesh*** as a teaser for next
   week.

So, as with Sessions 7 and 8: this became **Session 9**, *Regret, Grace, and
a Story Told Twice*, and the Flood moved to **Session 10** (Genesis
6:9–9:29), with everything after it renumbered down by one (git mv from the
top: 17→18 … 09-the-flood→10-the-flood; titles and README bumped). The
Flood's planning notes stay with it in `../10-the-flood/NOTES.md`.

**What "Sinai" means (settled 2026-10-09).** David pointed to Zara Zhang,
"*Sintflut* and Sinai: Genesis 6–8's allusion to Exodus 24–40," *JSOT* 50.3
(2026): 272–298, doi 10.1177/03090892251367447 — open access, **CC BY 4.0**.
The first draft had guessed "Torah from Sinai" (the rabbis' mercy/justice,
Rashi, Breuer); that material now sits in Part D of the
[one story or two?](texts/one-story-or-two.md) sheet, and Part 4 §3 of the
handout is Zhang's reading: the Flood alludes to Exodus 24–40 in three clusters
(Gen 6 // Exod 32, fifteen parallels, six in each announcement of judgment;
Gen 6–8 // Exod 25, 39–40, the ark/tabernacle and the calendar; Gen 7 // Exod
24, *entry + 7 days + entry + 40 days*), and those allusions explain the
doublets (judgment ×2, chronology, double entry, two/seven ~ seventy/two). Her
allusive reading — Moses' *wipe me out* "may have influenced… Isa. 53" —
gives the section its landing. The article was read in full in Chrome
(sagepub blocks curl); 28 quoted lines were confirmed with `String.includes()`
on the article text. She is a St Andrews doctoral researcher; the article has
not yet been answered in print.

Session 8's handout already has a short Part 5 on 6:5–8 (*yēṣer*; *ʿeṣeb* and
Lamech's two words; 1 Samuel 15; *Genesis Rabbah* 27:4; the נח/חן anagram).
This session should not repeat it: it links back and goes further.

**Status (2026-10-08):** draft built — handout plus four source sheets. Draft
render is 8 pages (Letter, `pdf/09-regret-and-grace.pdf`, scratch only). Not
yet panel-reviewed; no podcasts; no committed PDF (run `print-session` once
the content is final).

---

## The shape of the session

Four parts, a teaser and a close:

1. **Whose fault is it? (6:5)** — the subject changes to *hāʾādām*; Eden's
   excuses (3:12–13) heard and not accepted; *1 Enoch* (evil from above) vs Ben
   Sira 15:11–12 (*"Say not…"*) and 4 Ezra 3:21–22 (the evil heart); James
   1:13–14 and Mark 7:21–23; Ephesians 6:12 so the powers are not denied.
   *Yēṣer* occurs in Genesis only at 6:5 and 8:21 — after the flood the same
   diagnosis is the reason for mercy; Ezekiel 36:26.
2. **"The LORD regretted" (6:6–7)** — five readings, each with *its strength*
   and *the question it has to answer*: (1) translate gently — LXX, Targum;
   (2) accommodation — Philo, Augustine, Aquinas, Westminster, Calvin; (3) real
   grief — Genesis Rabbah 27:4, Heschel, Eph 4:30; (4) open theism and the ETS
   2001 vote; (5) relenting as character — Jer 18, Jonah 4:2 / Joel 2:13,
   Calvin's "tacit condition", Tertullian vs Marcion, Chisholm. Lands with
   Hebrews 6:17–18; 7:21 and Ephesians 4:30 (per the standing decision that the
   NT reading is authoritative): a purpose that does not change, a Spirit who
   can be grieved.
3. **Grace, for the first time (6:8)** — the idiom (39×, usually lower before
   higher; Ruth 2:10); Genesis 6:8 the only narrator's "found favor in the eyes
   of the LORD"; *charis* → Luke 1:30; then Exodus 32–34, where *māḥâ*, *niḥam*
   and *ḥēn* meet again (the only place in the rest of the Torah).
4. **A story told twice (6:9–9:17)** — the 6:5–7 / 6:11–13 comparison (*šāḥat*
   ×4; 6:12 built on 1:31); the doublet table; three readings at their
   strongest (J/P; Wenham's chiasm, the Gilgamesh order, Cassuto with the
   rabbis' mercy/justice; Sinai = Zhang's three allusion clusters),
   with a summary table and the common ground (the critics catalogued the Sinai
   echoes first).
5. **Next week** — Atrahasis's "clamor" (Clay 1922), Gilgamesh XI's weeping
   goddess and the flies/necklace (Clay 1922), and three questions to bring:
   why each flood comes, who regrets and when, what each god remembers.

**Sinai** is Zhang's allusion reading (see the top of this file).

## Panel review (2026-10-09)

Five seats ran independently (rabbi, modern Jewish scholar, evangelical,
mainline, skeptic) on the draft with Zhang's Sinai reading. Convergent
findings — the ones reached by two or more seats from different methods — and
what was done:

- **Isaiah 54:9** (four seats): the exiles' reading of the Flood as an oath.
  Added to Part 4 §1 (what P lets you hear), §4 (the oath), the Scripture
  sheet Part F.
- **God refuses Moses' offer, Exod 32:33** (mainline, evangelical; the rabbi
  supplied *Sotah* 14a): the Isaiah 53 landing moved from Part 4 to Part 3's
  Sinai bullets and now runs Moses' offer → God's refusal (32:33; Ps 49:7) →
  *Sotah* 14a (R. Samlai reads Isa 53:12 of Moses, *"he gave himself over to
  death"* — only the bold words of the Davidson edition are quoted) → 1 Pet
  2:24; 3:18, labelled as the Christian step.
- **Zhang overweighted** (mainline, modern Jewish, skeptic, evangelical): now
  "a new proposal"; leads with the rare words (*tēbâ*, *mikseh*); "both clocks
  are Sinai's" cut; her calendar starts in the wilderness of Sin (Exod 16:1);
  her scope limit stated; four doublets she explains, not "the very doublets";
  the reply that the echoes sort by school (and editors can allude) added.
- **The drowned** (mainline, skeptic): 6:7 quoted in full; new "What it costs"
  (Gen 18:23–25; Jonah 4:11; 1 Pet 3:20) and a discussion question; Ea's rebuke
  added to the teaser, with "Who objects to the flood?"
- **7:1 against "grace before righteousness"** (evangelical, skeptic; the rabbi
  added the parashah break at 6:8/6:9 and GR 28:9 vs Ramban): Part 3 now holds
  both; Hebrews 11:7 no longer said to "keep the order".
- **Reading 5 over-crowned / the NT formula settles nothing** (mainline,
  evangelical, skeptic): "may be the most biblical" → "many hold it together
  with reading 2, as Calvin did"; the NT paragraph now admits it does not
  settle 6:6 and lets 1 Sam 15 stand unresolved.
- **The source question** (mainline: two-against-one tilt, J/P undersold;
  evangelical: Mosaic view missing; rabbi: the tradition's own answer missing):
  §1 now states the field as of 2026 (P/non-P near-consensus; Baden vs
  Blum/Kratz/Schmid; Kaufmann/Milgrom's earlier P), what each strand lets you
  hear, its real strength (the continuity test) and weakness (the editor
  absorbs exceptions); a fourth reading, **"the oldest answer: one Author"**
  (Rashi 6:19, 7:2, 7:12; *Sanhedrin* 108b; *Shevuot* 36a; Kitchen; hard
  question Gen 36:31; Breuer); the table is now four rows.
- **Single-seat corrections taken:** the LXX sentence (both verbs of 6:6 became
  thought; 6:7 anger); 8:21 drops "only" and "all the time"; 5:29 and Gen 34:7;
  the maxim "the Torah speaks in the language of people" is R. Ishmael's on a
  doubled verb (*Sanhedrin* 64b); Rambam vs Ramban separated; R. Yehoshua ben
  Korḥa and R. Aivu named; GR 33:3's full point (deeds turn the attributes);
  *yēṣer hāraʿ* (GR 9:7; *Sukkah* 52a); Ben Sira 15:15's optimism and Rom
  5:12; 1 Pet 3:21; classical impassibility defined (not "no love"), Calvin's
  "clothes himself with our affections"; Fretheim and Moltmann in reading 3;
  Heschel's question reframed; Mark 3:5; Wenham's two 150s are one span;
  Luke 1:30 "the same idiom"; "the word ḥēn" (Abel, 4:4); source critics named
  as churchmen (Driver, Skinner); the "unsettles" sentence made two-sided;
  closing question per the evangelical seat.
- **Not taken / deferred:** the evangelical's request for a fourth *column* in
  the table (done as a fourth row instead); Barth on God's "constancy"
  (mainline) — not added; the Jonah "control exercise" (skeptic) — on the
  sheet, not the handout; Frymer-Kensky's noise/*ḥāmās* contrast (modern
  Jewish) — saved for Session 10 (see below).

The handout grew to 9 pages (last page ~3/4). The print pass should either
trim ~1 page or set breaks for an even 10.

## Verification notes worth keeping

Research was done 2026-10-08 by four parallel agents (Scripture/Hebrew, the
history of "regret", the doublets, the ANE texts), each quoting only from
files it downloaded and script-checking every quotation (165 + 179 + 154
verified, plus the Scripture report). A final script re-checked the handout
and sheets against those files. Things that corrected the brief or are easy
to get wrong:

- **Counts (OSHB, CC BY 4.0):** *niḥam* (niphal/hithpael) with God as subject
  = 37 verses (our reading of 54); categorical denials only Num 23:19 and 1 Sam
  15:29 (Ps 110:4, Jer 4:28, Ezek 24:14 are particular oaths/decrees). God
  regrets something already *done* only at Gen 6:6–7, 1 Sam 15:11, 35 and Jer
  42:10. *Ḥēn* first at Gen 6:8; 69× in all. *Find favor in the eyes of* = 39×;
  God-ward in 10 verses; **Gen 6:8 is the only narrator's statement**. *Yēṣer*
  in Genesis only 6:5 and 8:21. *Mikseh* 16×, all tabernacle except Gen 8:13.
  *Bərît ʿôlām* 16×, first at Gen 9:16. *Zākār ûnəqēbâ* side by side in 7
  verses. *Mabbûl* only Gen 6–11 and Ps 29:10.
- **Greek:** the Greek Pentateuch never uses *metanoeō* at all; the prophets
  use it of God freely. Gen 6:7 LXX = *ethymōthēn* in Rahlfs and Swete, but
  Brenton's Greek has *enethymēthēn* and his English "I am grieved". The
  First1KGreek digital Swete drops words in Gen 6:6–8 — don't quote it.
- **NET hides** the idiom at Ruth 2:10 and Judg 6:17, the pain root at Gen 6:6
  and Isa 63:10 ("offended"), and the *šāḥat* ×4 of 6:11–13.
- **Philo:** Yonge's footnote cites Deut 1:31 but Philo's Greek is Deut 8:5;
  Yonge mistranslates Gen 6:7 at §51 ("repent") but not at §§70–72.
- **Rashi on 7:16** does *not* contrast the names — that reading is
  Cassuto's. Rashi's mercy/justice is at 6:6 and 8:1 (with Genesis Rabbah
  33:3). *Zevaḥim* 116a asks whether clean/unclean existed before Sinai; it
  does not discuss two vs seven.
- **Wenham 1978** made the "17 Mesopotamian features, usually in the same
  order" argument (J alone 12, P alone 10); he did **not** argue for Moses (he
  preferred one epic source reworked by a priestly editor). A "Wenham chiasm"
  on Wikipedia ("Curse on earth (6:13b)") is not his.
- **Gilgamesh:** the weeping goddess and the necklace are Bēlet-ilī's on the
  modern reading (eBL note quoting George: Ishtar "quite out of place"); the
  jewels are fly-shaped lapis beads; the rainbow reading is Smith 1876's.
  Thompson 1928 renders XI 117–119 "May that day turn to dust" — the
  "turned to clay" wording is Clay 1922's. Atrahasis is named twice in XI
  (197, and XI 49 in one manuscript). The handout quotes **Clay 1922 (PD)**
  rather than eBL, because the licence on eBL's corpus translations is stated
  only on its fragment-library page — if David wants George's modern wording,
  confirm that licence first.
- **No open English** exists for Atrahasis Tablet III (the goddess's lament,
  the flies) or for the "bellowing like a bull / could not sleep" lines;
  Clay's "clamor" is the safe public-domain line.
- **Session 5.2 quotes Ben Sira 15:14–17 inaccurately.** Its wording (*"gave
  him into the hand of his inclination [yitzro]. If thou choose, thou mayest
  keep the commandment… Fire and water are poured out before thee"*) is
  credited to Charles 1913, but Charles reads *"God created man from the
  beginning, / And placed him in the hand of his Yeṣer. / If thou (so)
  desirest, thou canst keep the commandment… Poured out before thee (are) fire
  and water"* (APOT I, Sirach 15:14–16). Session 9 quotes Charles exactly.
  Fixed 2026-10-09 from the page image (APOT I, p. 371; translators Box and
  Oesterley).
- **NET credit line:** netbible.com/copyright asks for "(NET)" after each
  quotation *or* an acknowledgement-page line; our footer line is close to but
  not verbatim the second option. Worth tidying site-wide some day.

## Threads handed forward to Session 10 (the Flood)

- **Frymer-Kensky's contrast** (T. Frymer-Kensky, "The Atrahasis Epic and Its
  Significance for Our Understanding of Genesis 1–9," *Biblical Archaeologist*
  40, 1977 — verify before quoting): Atrahasis's cause is noise and its remedy
  population control; Genesis's cause is *ḥāmās* and its remedy *"be
  fruitful"* plus a law against bloodshed (9:1–7). The modern Jewish panel seat
  urged it; the teaser's first question sets it up.
- The skeptic's point: Genesis's God also speaks *after* the flood (*"as I have
  just done,"* 8:21) — so "before or after?" is not a clean contrast.

- The **three questions** the teaser sets: why each flood comes (Atrahasis:
  noise/overpopulation; Gilgamesh: no reason given — only "the great gods
  decided"; Genesis: the heart, and violence), who regrets and when (the
  goddess *after*; the LORD *before*), and what each god remembers (the
  necklace; the bow, *"I will remember my covenant"*, 9:15–16).
- **Ea's rebuke** (*"On the sinner place his sin"*, Clay XI 184) against
  Genesis 18's *"Will not the judge of the whole earth do what is right?"* —
  and Ezekiel 18.
- **The birds** (dove, swallow, raven in Gilgamesh; raven and dove in
  Genesis) and the Ugarit fragment with a dove and a pelican (eBL "Ug₂").
- **"The gods like flies"** vs *"the LORD smelled the soothing aroma"* (8:21)
  — *rêaḥ hannîḥōaḥ*, the *n-w-ḥ* of Noah's name (Session 7's thread).
- **Noah the man of the soil** (9:20) — the payoff of 5:29 promised in Session
  7; 9:18–29 (the vineyard, Ham) is still unread.
- **Zhang 2026** goes on (her §4.5) to Numbers 13: the birds sent *"at the
  end of 40 days"* and the dove's olive leaf // the spies back *"after 40
  days"* with grapes, and the **Nephilim** of Num 13:33 // Gen 6:4 — a
  callback to Session 8 waiting for the end of the Flood.
- The agents' raw files and verified-quote lists are in this session's
  scratchpad only (not kept); regenerate from the URLs on the sheets.
