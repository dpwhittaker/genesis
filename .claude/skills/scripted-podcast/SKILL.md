---
name: scripted-podcast
description: Make a Genesis lesson's podcasts — the SHORT (~20 min) and LONG (~40 min) episodes every lesson ships with, plus an optional trailer — as two-host scripts: two friends who have both read the handout, talking it over, light-hearted and conversational, not a lecture. Claude writes sessions/<slug>/<slug>-short.script.md and <slug>-long.script.md from the handout and source sheets, with an actor's direction on every line; the user reads and revises them, and only then does Fish Audio's Drama 3 (Ethan and Sarah; ElevenLabs remains as a second engine) voice them into <slug>-short.m4a and <slug>-long.m4a. Then Claude transcribes the audio locally to check it against the script, and links both on the page. This replaced the NotebookLM flow from Session 10 on. Use when the user says "make podcasts for session N", "short and long podcast", "deep dive for lesson N", "trailer", or wants a line, a voice or a take changed. Never send a script to a voice service before the user has approved it.
---

# Lesson podcasts: script first, then a voice service

Every lesson ships with two podcasts, a **short** and a **long** one. From
Session 10 on, both are made here. **Claude writes a script the user can read;
the voice service only performs it.** So every claim and every quotation is
checked before anyone hears it, and a wrong line is fixed by editing one line.

**The engine is Fish Audio's Drama 3**, chosen by the user on 2026-10-17 as
"the cheapest acceptable option". Session 10 was first voiced on ElevenLabs
v4, which sounded good but cost one credit a character: about 50,000 credits a
lesson, a sixth of the monthly plan. The user then compared Drama 3 (API) with
four local models (Fish S2 Pro, VibeVoice 1.5B and 7B, Dia, Dia2; test rig in
`~/tts-compare`) and picked Drama 3 with Ethan and Sarah. `podcast.py` speaks
both services; a script's front matter picks one with `engine:`.

> Sessions 1–9 were made in NotebookLM (`Medium_Podcast.m4a`/`Longer_Podcast.m4a`
> through Session 7, `<slug>-short/-long.m4a` for 8–9). Leave them alone: their
> URLs are in past emails, GroupMe posts and Church Center resources. The
> `notebooklm` skill was removed on 2026-10-09 when this one replaced it. It
> survives in git history at commit `00c8fb6` if it's ever needed.

The tool is `podcast.py` beside this file. It needs Python 3 with PyYAML (both
on the system `python3`) and ffmpeg. The WebSocket transport and `verify` need
packages that only `uv` provides here:

```bash
P=.claude/skills/scripted-podcast/podcast.py
UV="$HOME/.local/bin/uv run --quiet --no-project --with pyyaml"
python3 $P check  sessions/<slug>/<slug>-long.script.md     # lint, stats, chunk plan, cost; no API calls
python3 $P render sessions/<slug>/<slug>-long.script.md     # dry run: says what would be sent
python3 $P render … --yes                                    # voice new/changed chunks, assemble the .m4a
python3 $P render … --only 7 --yes --copy                    # voice/audition chunk 7 alone
$UV --with faster-whisper python $P verify …                 # transcribe locally, diff against the script
python3 $P voices --engine fish [search]                    # Fish's voice library (ElevenLabs without --engine)
python3 $P quota --engine fish                               # API credit left, in dollars
$UV --with websockets python $P render … --transport ws --yes   # experimental; see "Transports"
python3 $P render … --out X.m4a --model eleven_v3            # variants side by side, for comparing
```

## What each lesson gets

| Episode | Length | Words | Script → audio | What it is |
|---|---|---|---|---|
| **short** | ~20 min | ~3,000 | `<slug>-short.script.md` → `<slug>-short.m4a` | The overview: the session's aim and each part's core move, with one or two key quotations per part. Someone who hears only this should be ready for class. |
| **long** | ~40 min | ~6,000 | `<slug>-long.script.md` → `<slug>-long.m4a` | The deep dive: every part, in the handout's order, with more of the source sheets' best lines, and each reading given at its strongest, along with its hardest question. |
| trailer | 2 min | ~300 | `<slug>-trailer.script.md` → `<slug>-trailer.m4a` | **Only when asked.** It asks the session's questions and answers none of them. `example-trailer.script.md` beside this file is a worked one (Session 9's test, never published). |

These names are the ones `publish-lesson` looks for, so keep them. The lengths
match the NotebookLM pairs (shorts ran 19–25 min, longs 30–71). The user may
ask for others: set them per lesson, and remember that the user reads every
word before it's voiced. The short is **not** the long one cut down. Write it
as its own episode, though it can reuse the long's best lines.

## The hosts

**Two friends who have both read the handout and the source sheets, talking
about what they found.** Not a teacher and a student, and not a lecture with
interruptions. Session 10 was first written that way: an erudite teacher
carrying 73% of the words, exact citations, a student asking "And the hard
question?". The user heard it and said it sounded "like they're reading an
academic paper", and asked for "a more light-hearted, casual, and
conversational tone. Two friends talking about what they read, not a scholar
teaching a student" (2026-10-16).

| Label | Voice (Fish Audio) | Who | Directed as |
|---|---|---|---|
| `ETHAN` | **Ethan** (`536d3a5e000945adb7038665781a4aca`) | Warm, dry, easily delighted by an old text. Likes reading out the strange lines (the rabbis' stories, a god talking to a wall). Gets there slowly and then sees the point. | warm, relaxed, easygoing; amused; thoughtful when it turns serious |
| `SARAH` | **Sarah** (`933563129e564b19a115bedd57b7406a`) | Quick, funny, honest. Says the obvious question out loud, notices what's absurd, pushes back when something doesn't add up, and brings her own finds from the sheets. | **understated**: wry, dry, quietly amused, warm. Never bright, gleeful or shouting |

Both carry the content. Either one introduces a part, reads a quotation, makes
the point or raises the objection. Swap who knows what from part to part, so
neither is the expert. Each should have **40–60% of the words** (`check`
prints the split). Neither is a cheerleader: if a line is only "Wow,
that's fascinating," replace it with a real reaction, a joke, a question or a
disagreement.

The user chose Sarah over Hannah because she is less bright, and turned down a
first take whose directions made her "bright", "gleeful" and "shouting": "Sarah
shouting at the beginning is too much." Write her directions low-key. Keep the
pair across every lesson so the class knows the voices. The front matter of
every script starts from this:

```yaml
---
title: "Session N — <short|long>: <lesson title>"
output: <slug>-<short|long>.m4a
engine: fish
model: drama-3
speed: 1.1          # prosody.speed; the user asked for "a bit" faster than 1.0
max_pause: 0.35     # seconds; every longer pause is cut to this when assembling
speakers:
  ETHAN: { voice: 536d3a5e000945adb7038665781a4aca, name: Ethan }   # Fish Audio library
  SARAH: { voice: 933563129e564b19a115bedd57b7406a, name: Sarah }   # Fish Audio library
---
```

**ElevenLabs, if it's ever wanted again:** `engine: elevenlabs` (or no
`engine:`), `model: eleven_v4`, `stability: 0.5`, `seed: <N>`, and the voices
Flint (`qAZH0aMXY8tw1QufPN0D`, deep, raspy, warm; Ethan's part) and Lauren
(`DODLEQrClDo8wCz460ld`; Sarah's part), chosen after George and Jessica.
ElevenLabs wants short tags, not full directions (see *Audio tags*).

The labels are never voiced. **No names on air**, and **no invented lives**:
the hosts react to what they *read* ("I had to read that twice", "this one made
me laugh"), which is the premise, but they have no biography: no seminary,
congregation, spouse, children, or memory from before the handout ("growing
up, I…"). They don't mention being AI either.

## Workflow

### 1. Gather (read, don't skim)

- `sessions/<slug>/index.md`: the handout. **This is the source of truth.**
  Everything voiced must be in it, or in its `texts/` sheets.
- `sessions/<slug>/texts/*.md`: the source sheets, for exact quotations and
  for the long episode's extended readings.
- `sessions/<slug>/NOTES.md`: why the session is shaped the way it is, and
  what was **cut** (and why). Never voice anything that is only in NOTES.
- The project `CLAUDE.md` and memories: the audience is the class, quotations
  are NET, the time of day stays generic, contested questions get both sides,
  and New Testament readings are authoritative.

The handout should be finished (panel-reviewed, printed) before you write the
scripts. A script written against a draft goes stale when the draft changes.

### 2. Outline both episodes

Budget words at **150 a minute** (`check` estimates the same way; v4 dialogue
runs a little faster, so a 6,000-word script comes out near 38 minutes). Split
the budget across the handout's parts by their weight in the handout, not
equally. Write the outline into each script file as `##` headings with a
`<!-- ~N words: what this part must land -->` comment under each, then write
underneath them. If the session's shape is unusual, or the user asks, show the
outline before writing the lines.

### 3. Write

Write the long episode first, part by part, running `check` after each. Then
write the short one. The craft is in *Writing an episode* and *Writing for the
ear* below. Put a `---` line at each part boundary. That makes the part a
section, so an edit inside it can't shift the chunking anywhere else.

### 4. Check

`podcast.py check` until there are no `ERROR`s, and read every `warn`. It catches
references written as digits, LORD in capitals, transliteration diacritics,
parentheses and abbreviations, SSML, turns too long to send, and, for Fish,
turns of more than six words with no opening direction (for ElevenLabs: tags a
listener can't hear, and tags crowding a turn). It also prints each host's
share, the estimated length, the chunk plan and the characters to be sent.

### 5. STOP: the user reads the scripts

Don't paste 9,000 words into the chat. Give the user:
- the two paths (they open them in claude-hub's file explorer);
- for each episode, its parts with their minutes and the main quotations;
- what `check` says: the length, the host split and the cost.

A trailer's text can go in the reply whole. **Do not render until the user
approves.** Revise as asked, re-run `check`, and say what changed. This loop is
free, so iterate here rather than after voicing.

### 6. Voice

`podcast.py render <script> --yes` for each episode. You can run both at once,
each in the background.

- **Chunking.** Each `---` section is split at turn boundaries into the fewest
  chunks under the engine's limit, cut near equal shares so none is a stub:
  **≤ 3,000 characters for Fish** (it states no limit, and splits long text
  into 100–300-character pieces itself, carrying the voice across them; the
  2,600-character opening voiced cleanly), **≤ 1,800 for ElevenLabs** (its
  limit is 2,000). Each chunk is one request; directions count toward the size.
- **What Fish is sent.** One `POST https://api.fish.audio/v1/tts` per chunk with
  the header `model: drama-3`: the turns as `<|speaker:N|>` lines (N is the
  label's place in `speakers:`), `reference_id` listing every speaker's voice in
  that order, mp3 at 128 kbps, and `prosody.speed`. `*word*` in the script goes
  out as `<emphasis>word</emphasis>`. A 5xx ("under high load") or a dropped
  connection is retried twice.
- **Cache.** Each chunk is cached in `~/.cache/scripted-podcast/` under a hash of
  exactly what was sent (text, voices, model, settings, seed or take). A sidecar
  `.json` keeps the request and the time.
- **Stitching (ElevenLabs only).** Chunks are voiced **in script order**. Each
  request carries `previous_request_ids` (the takes before it, up to 3), so a
  chunk picks up where the last one left off. When a chunk mid-script is
  retaken, it also carries `next_request_ids` (the takes after it).
  - Request ids can be stitched to for 2 hours only. Past that, or for a
    neighbour being re-voiced in the same run, the request sends 100
    characters of that neighbour's text instead (`previous_text`/
    `future_text`). The render line says which it used.
  - None of this is in the cache key, so an edit re-voices only its own chunk.
  - `stitch: false` sends chunks independently. Fish has no equivalent, so its
    chunks are independent; the fixed voices keep them matched.
- **Truncation check.** After each chunk, the renderer compares its length
  with its word count and flags one much shorter than its text (cut off).
- **Assembly.** With `max_pause:` (Fish scripts), each chunk first has its
  leading and trailing silence removed and every pause longer than
  `max_pause` cut down to it, keeping the pause's first and last halves so
  breaths and word endings survive. The chunks are then joined with
  `max_pause` of silence, so a seam sounds like any other turn. Without it,
  chunks are joined with a 0.35 s gap. Then everything is loudness-normalised
  to −16 LUFS and encoded as **64 kbps mono AAC with `+faststart`**, about
  0.5 MB a minute. That keeps the site inside GitHub Pages' 1 GB limit, where
  audio is nearly all the bytes. The file's metadata carries the script's
  `title` and the engine's credit.

**Cost on Fish** is per character sent, directions included, from prepaid API
credit: about **$10 per million characters**. Session 10's pair (47,843 + 19,874
characters with directions) cost $0.65, where the same pair on ElevenLabs had
cost 52,462 credits. Check the balance with
`podcast.py quota --engine fish`.

**Cost on ElevenLabs** is **one credit per character**, tags included: the
`character-cost` header equals the characters sent. Session 10's first pair
(36,372 + 16,090 characters) used 52,462 of the Creator plan's 300,000 a
month: about 50,000 credits a lesson. That cost is why the engine changed.

### 7. Verify (you can't listen, so transcribe)

```bash
HF_HUB_OFFLINE=1 ~/.local/bin/uv run --quiet --no-project --with faster-whisper --with pyyaml \
  python $P verify sessions/<slug>/<slug>-long.script.md
```

This transcribes the `.m4a` on the CPU with the cached Whisper large-v3-turbo
model (int8). It runs at about a third of real time, so an hour of audio takes
~20 minutes; run it in the background. It then diffs the transcript against
the script and prints each difference with its **chunk, script line and
timestamp**. Numbers and ordinals are matched to Whisper's digits, so
"First Samuel" vs "1 Samuel" isn't reported.

- A run of missing words at the end of a chunk means that chunk was cut off.
  Retake it.
- An isolated word that "differs" is usually Whisper mishearing (names,
  homophones). Give the user the timestamp and let them judge.
- Report what verify found. Never say how the audio *sounds*.

### 8. The user listens; iterate

- **A line is wrong, or reads badly:** edit it and render again. Only that
  chunk is re-voiced and billed.
- **The words are right but the delivery isn't:** first rewrite that line's
  direction (on Fish this is the main lever; it re-voices only its chunk). Or
  add `<!-- take: 2 -->` (then 3, …) anywhere in the chunk's lines: on
  ElevenLabs that changes the seed; Fish has no seed, so it just files a fresh
  sample under a new cache key. Audition a chunk alone with `--only N --copy`,
  which writes `<output>.chunkN.mp3` beside the script (gitignored), pauses
  capped as in the episode. Then render the whole.
- **A retake's seam is audible** (ElevenLabs, a day later, when the ids have
  expired): give the neighbouring chunk a take too, so the two are stitched
  afresh.
- **Mispronunciation:** respell the word in the script. The printed handout
  keeps the scholarly spelling; the script is for the voice.
- **Too slow, or the gaps too long (Fish):** raise `speed` (1.15, 1.2) or lower
  `max_pause` (0.25). `max_pause` costs nothing: it's applied when
  assembling, from the cache. `speed` re-voices every chunk.
- **Too flat, or too wild (ElevenLabs):** lower `stability` for more range
  (0.3–0.4), raise it for steadier reading (0.6–0.7). Every chunk re-voices.

### 9. Put them on the page

Round each duration to whole minutes (`ffprobe` or verify's first line).

**`sessions/<slug>/index.md`:** a `## 🎧 Listen` section right after the
opening `**Passage:**` / source-sheet / PDF lines, before the first `##`
section. Wrap it in a `no-print` div so it's on screen but not on paper:

```markdown
<div class="no-print" markdown="1">

## 🎧 Listen

Two companion podcasts for this session — good before you read, or to revisit afterward:

- **Short overview** (~<SHORT> min): <audio controls preload="none" src="<slug>-short.m4a">Your browser can't play audio — [download the file](<slug>-short.m4a).</audio>
- **Longer deep dive** (~<LONG> min): <audio controls preload="none" src="<slug>-long.m4a">Your browser can't play audio — [download the file](<slug>-long.m4a).</audio>

*Voiced by AI with [Fish Audio](https://fish.audio) from scripts written for this session.*

</div>
```

A trailer, if there is one, goes first in the list:
`- **Two-minute trailer**: <audio … src="<slug>-trailer.m4a">…</audio>`.
Keep `src`/`href` as bare file names: the page is served from the session
folder.

**`README.md`:** append to the lesson's bullet, short first:
`🎧 Podcasts: [short (<SHORT>m)](sessions/<slug>/<slug>-short.m4a) · [long (<LONG>m)](sessions/<slug>/<slug>-long.m4a)`

Then:
- `index.md` changed, so re-render the PDF with `print-session`. The Listen
  block doesn't print, but `publish-lesson` refuses a PDF older than its page.
- Commit the scripts, the two `.m4a` files and the page, README and PDF edits
  together, and push. `publish-lesson` takes it from there.
- Add a line to the session's `NOTES.md` status: when the podcasts were voiced,
  their lengths, and anything retaken.

## Writing an episode

- **Open cold, on the text.** Start with the most arresting line of the
  passage or the sharpest question, not "Welcome back" or "Today we're going
  to talk about". Name the session within the first minute.
- **Follow the handout's parts, in its order.** In the long episode, a part
  usually has:
  - one host bringing what struck them ("Okay, the part that got me…");
  - the line itself, read exactly;
  - what's going on in it, in plain words;
  - the other reading at its strongest, and its hardest question, said the
    way you'd say it to a friend;
  - a laugh, an "oof" or a "huh", and a hand-off to the next part.

  Don't run every part on the same template. Vary the order and the pace.
- **A part gets its best two or three things, not all of them.** The episode
  is a conversation about the handout, not a reading of it; the rest is "in
  the handout". A podcast that delivers a fact in every line sounds like a
  paper read aloud, however short the turns.
- **Light-hearted, where the text allows it.** Laugh at what's genuinely funny
  in the old stories (gods who cower like dogs, a god whispering to a wall), and
  enjoy the surprises. Never laugh at Scripture or at anyone in the class. When
  the subject turns hard (the children in the flood, a verse used to defend
  slavery), the hosts get quieter, and the change should be audible.
- **Read the best lines aloud, exactly, and keep them short.** Mostly 10–35
  words; read a longer passage only when its wording is the point. Introduce
  a quotation the way a friend would ("Listen to this.", "Here's how Gilgamesh
  puts it:"), and name the source as a friend would ("Augustine", "a rabbi in
  the twelfth century, Ibn Ezra", "an old translation from the twenties"),
  not with a full citation. These exact readings are still what NotebookLM
  could never get right.
- **Hand the listener the questions.** Each "Talk about it" box can become one
  question a host puts to the listener ("Okay, one to chew on before
  class…"). Offer it as a question, never as a verdict on what the class
  thinks.
- **Recap at the turns.** In the long episode, a two-line "so far" at the
  midpoint and before the landing helps the ear ("Okay, let me see if I've
  got this…").
- **Land on the handout's "So what?"** and close on a question to bring, then
  the session name.
- **Don't invent.** Every fact, number and attribution must be traceable to
  the handout or a sheet. If the script needs something the handout lacks, ask
  the user, or add it to the handout first. Don't slip it in by audio.

## Writing for the ear

- **One idea per turn; one to three sentences.** Long monologues are where
  listeners drift. Let the other host break them up, finish a sentence, or
  laugh.
- **Quote exactly, and say the reference in words**, when you give one:
  "Genesis six, verse six," not `6:6`; "First Samuel fifteen". Friends don't
  cite every verse: "back in chapter six" is often enough. Introduce a
  quotation so the ear knows it's one.
- **Write "the Lord", never LORD.** CAPS mean emphasis to the voice.
- **Respell what a reader would stumble on.** Hebrew in the handout's spelling
  (*yēṣer*, *ḥēn*) gets read badly; write *yetzer*, *khen*, or skip the word
  and give its meaning.
- **No parentheses, footnotes, "cf.", "BCE".** Say "about two hundred and
  fifty years before Jesus", or just "before Jesus".
- **Numbers in words** where a person would say them that way.
- **Never point at a page.** Say "in the handout", not "on page three": page
  breaks move.
- **Talk, don't write.** Contractions, fragments, "okay so", "honestly",
  "wait, wait", a sentence that starts over. Everyday words: "the gods
  panic", not "the divine council loses control".
- **Contractions and spoken rhythm.** "It's", "doesn't", fragments, a "Wait."
  An ellipsis (…) trails off or hesitates; a dash cuts in. Use both
  sparingly: v4 takes punctuation seriously.
- **Interruptions:** end the cut-off line with a dash ("so the flood was—")
  and start the next turn with `[interrupting]` or `[jumping in]`.
- **Class rules hold in audio, too.** Talk *to* the class, never *about*
  them. Use "today", "this session", "last session", "next session", never
  "tonight" or "this morning". Lay out contested questions at their strongest
  on each side. Where the New Testament reads a passage, it settles it for
  this class. And nothing goes in that the handout has dropped.
- **Avoid podcast tics:** "Exactly!", "Right?", "That's fascinating",
  "unpack", "deep dive", "let's dive in", "game-changer". Not every turn opens
  with a reaction.

## Script format

```markdown
---
(front matter: see The hosts)
# similarity: 0.75     optional; how closely to hold the voice
# stitch: false        default true
# language: en
# credit: "…"          default "Voiced with ElevenLabs (elevenlabs.io)", into the file's metadata
---

<!-- Notes for writers and reviewers. Never voiced; may span lines. -->

## Part 1 — Whose fault is it?     ← headings organise the script for readers; never voiced
<!-- ~900 words: the verdict falls on humankind; Eden's excuses; 8:21 -->

ETHAN: [quiet, measured, reading it slowly] "The Lord regretted that he had made humankind on the earth."

SARAH: [quietly taken aback] Wait. God *regretted*?
A turn may wrap onto following lines until a blank line.

---                                ← section break: chunks never cross it

## Part 2 — …
<!-- take: 2 -->                   ← re-rolls the chunk this sits in
ETHAN: …
```

- A turn is `LABEL: text`, where LABEL is a key of `speakers`. After a blank
  line, any text must start a new turn.
- `*emphasis*` is stripped before sending: it's for the human reader. To make
  the voice stress a word, use CAPS (sparingly) or reword the sentence.
- Put `---` at each part boundary. Within a section, chunk cuts fall at
  turn boundaries automatically. A seam is a slight pause and could shift the
  voices' energy, which is another reason to keep sections to natural parts.
  (On the Session 9 trailer, the user heard no seam.)
- One turn can't exceed 2,000 characters; `check` makes it an error. Nothing
  near that length belongs in a podcast anyway.

## Directions for Fish

Drama 3 reads a bracketed note the way an actor reads a direction, and never
speaks it. Fish's own advice is to direct each line where the mood changes; for
these two hosts, **open every turn with one**, as Session 10 does.

- **Write it as you'd direct an actor**, in a few words: `[wry, deadpan]`,
  `[warm and thoughtful, slowing down to make the point]`, `[jumping in,
  finishing his sentence]`, `[a beat, quietly]`. Sounds go where they happen:
  `[small laugh]`, `[soft gasp]`, `[sighs, then fair]`.
- **A direction mid-line changes the read from there on**: `It's a little bit
  of a trap. [reading it out with a touch of drama, but keeping her voice low]
  "Tear down the house…"`.
- **Paired tags for single words:** `*this*` in the script is sent as
  `<emphasis>this</emphasis>`. Fish also has `<whisper>`, `<soft>`, `<fast>`,
  `<slow>`, `<stress>` and `<forceful>`; write those literally if needed.
- **Keep Sarah low**: wry, dry, quietly amused, warm, quietly delighted. Not
  bright, excited, gleeful or shouting (see *The hosts*).
- **The hard parts get quiet, careful directions** (`[softly, honest]`,
  `[serious, steady]`), so the change of mood is audible.
- Session 10's scripts are the worked example: 470 directed turns.

## Audio tags (ElevenLabs)

On v3 and v4, a tag in square brackets directs the delivery of what follows
it. Tags are **free text, not a fixed list**. Documented examples:

- **Emotion and attitude:** `[curious]` `[excited]` `[surprised]`
  `[thoughtful]` `[sarcastic]` `[happy]` `[sad]` `[annoyed]` `[appalled]`
  `[mischievously]`
- **Delivery:** `[whispers]` `[softly]` `[warmly]`, or a description such as
  `[quiet, measured]`, `[lower, thoughtful]` or `[warm, amused]`
- **Non-verbal:** `[laughs]` `[chuckles]` `[starts laughing]` `[sighs]`
  `[exhales]` `[inhales deeply]` `[clears throat]` `[gulps]` `[snorts]`
- **Pacing:** `[pause]` `[short pause]` `[long pause]`
- **Dialogue:** `[interrupting]` `[jumping in]` `[overlapping]`

Rules of thumb:

- **One tag at the start of a turn, most of the time; two at most.** Aim for
  about 2–4 tags per 100 words (`check` prints the rate). Session 10's first
  scripts ran 0.7 per 100 and read flat. Untagged lines read naturally; a tag
  is for a *change* in delivery.
- **Both hosts get the expressive tags**: laughter (`[laughs]`,
  `[chuckles]`, `[starts laughing]`), surprise, `[amused]`, `[deadpan]`,
  `[incredulous]`, and the quiet ones (`[softly]`, `[quieter]`) for the hard
  parts.
- **Only tag what can be heard.** `[smiling]`, `[nods]`, `[pacing]`,
  `[music]`: the model may read the word aloud or invent a sound effect.
  Describe the voice instead. `check` flags these.
- **No sound effects** (`[applause]`, `[door creaks]`) in class material.
- **No SSML.** `<break time="1s"/>` doesn't work on v3/v4. Use `[pause]`, an
  ellipsis, or a new turn.

## Transports: REST (default) vs WebSocket

`--transport ws` sends the whole script through the Text to Dialogue
WebSocket (`wss://api.elevenlabs.io/v1/text-to-dialogue/stream-input`) in one
session, with no chunks. It was compared with the default REST render on the
Session 9 trailer (2026-10-09, `eleven_v4`). **The user preferred REST:** its
seam was inaudible, and the voices "sounded more like they were naturally
reacting to each other." What we learned about the WebSocket:

- **It takes `eleven_v4`**, although the API reference says v3 only.
- **It voices one turn at a time.** The account history shows one generation
  per turn under one request-id. A REST chunk, by contrast, is one generation
  of a whole stretch of dialogue, which is why its reactions sound live.
- **Each turn has to be sent with `flush: true`** (the renderer does). Without
  it, the server voices the last word or two of each turn as a separate
  fragment.
- It costs the same, runs about 8% longer (longer pauses between turns), and a
  retake re-voices the whole session.

## ElevenLabs facts (checked 2026-10-09)

- **Endpoint:** `POST https://api.elevenlabs.io/v1/text-to-dialogue?output_format=mp3_44100_128`,
  with the header `xi-api-key`.
  - Body: `{inputs: [{text, voice_id}], model_id, settings: {stability,
    similarity}, seed, language_code?, previous_text?, future_text?,
    previous_request_ids?, next_request_ids?, apply_text_normalization?}`.
  - Response: raw audio bytes; a 422 returns `{detail: [...]}`.
  - Docs: <https://elevenlabs.io/docs/api-reference/text-to-dialogue/convert>,
    and the cookbook
    <https://elevenlabs.io/docs/eleven-api/guides/cookbooks/text-to-dialogue>.
- **Models:** `eleven_v4` (released 2026-09-28; recommended) and `eleven_v3`
  (the API's default, now "previous generation"). Only these two do dialogue
  and audio tags. Style and speed settings don't apply to v4.
- **Limits:**
  - ≤ 2,000 characters of text per request ("longer requests may end early or
    return a validation error"), and ≤ 10 distinct voices.
  - `previous_text`/`future_text`: 100 characters each.
  - Request stitching (`previous_request_ids`/`next_request_ids`): ≤ 3 ids
    each, each < 2 hours old. Not available on v3; v4 accepts it.
- **Billing:** per character, tags included, as the `character-cost` response
  header shows: one credit per character on Creator with v4 (an earlier
  note here said ~0.1; Session 10 showed it was 1).
- **Output formats:** `mp3_44100_128` works on every tier. 192 kbps needs
  Creator; 44.1 kHz PCM/WAV needs Pro. The renderer re-encodes to 64k mono
  anyway.
- **Determinism:** `seed` makes output repeatable on a best-effort basis only.
  Changing the seed (a take) is the supported way to get a different
  performance of the same text.

## Voices

- **Fish:** `podcast.py voices --engine fish [title]` searches Fish's English
  library by popularity. Fish's official voices (Ethan, Sarah, Hannah, Caleb,
  Naomi…) are published by the author `d8b0991f96b44e489422ca2ddf0bd31d`. Fish's
  terms license its audio "solely for purposes of using the Services", so its
  voices can't be used as samples for a local model.
- **ElevenLabs:** `podcast.py voices [search]` lists the account's own voices (`GET /v2/voices`).
  Library voices aren't listed there. `GET /v1/shared-voices?search=…` finds
  them, and on a paid plan their ID works directly, without adding them to the
  account. That's how Flint and Lauren are used.
- **Default ("premade") voices** (George, Jessica, Brian…) **are retired on
  2026-12-31**, so a script that names one can't be re-voiced after that.
- To audition a new voice, give it to one speaker and render one chunk with
  `--only 1 --copy`. Let the user listen before re-voicing everything.

## The API keys

- **Fish:** `$FISH_API_KEY`, or else `FISH_API_KEY=…` from
  **`~/.config/genesis/fishaudio.env`** (mode 0600, outside the repo).
- **ElevenLabs:** `$ELEVENLABS_API_KEY`, or else `ELEVENLABS_API_KEY=…` from
  **`~/.config/genesis/elevenlabs.env`** (mode 0600; `*.env` is also
  gitignored).

Never commit a key or echo it.

The current key is unrestricted but **locked to this machine's public IPv4**
(`curl -4 https://api.ipify.org`). It's a residential address and can change.
If every call suddenly fails with an IP or authorisation error, check the
address and ask the user to update the key's allow-list. A scoped key needs
**Text to Speech** (dialogue included), plus **Voices: read** and **User:
read** for `voices` and `quota`.

## Licensing and credit

- **Fish Audio:** API credit is a paid service, and paid users "are licensed to
  use the Services for commercial uses", which more than covers a free class
  site. (The free plan is "internal, personal, non-commercial use" only.) Fish
  "encourage[s] you to proactively disclose that such Content was created
  using artificial intelligence technologies", so the Listen block says
  *Voiced by AI with Fish Audio*. The hosts still never say it on air.
- **ElevenLabs:** the account is on a paid plan (Creator), so the free plan's
  rules (non-commercial use only, "elevenlabs.io" in the published title)
  don't bind.
- Either way, the renderer writes the engine's `credit:` into each file's
  metadata.

The words are ours. The quotations follow the project's sourcing rules (NET
for Scripture), and the session page's attribution already covers them.

## Gotchas

- **You can't hear the result.** Don't call it good: the user is the judge.
  `verify` checks the words; the user checks everything else.
- **Stitching ids expire after 2 hours.** A retake the next day falls back to
  its neighbours' text. If the seam shows, take the neighbour too.
- **The cache is keyed on what was sent.** Changing `model`, a voice,
  `stability`, `seed` or any word re-voices the chunks it touches. Comments,
  headings and `*emphasis*` marks don't. An edit can re-cut the chunks of its
  own section, never another.
- **`--force`** re-voices even cached chunks. You rarely want it: use a take.
- **A late handout change can outdate the podcasts.** If `index.md` changes
  in substance after voicing, tell the user which episode it touches and offer
  to retake those lines.
