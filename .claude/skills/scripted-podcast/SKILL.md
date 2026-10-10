---
name: scripted-podcast
description: Make a Genesis lesson's podcasts — the SHORT (~20 min) and LONG (~40 min) episodes every lesson ships with, plus an optional trailer — as two-host scripts voiced by ElevenLabs. An erudite TEACHER and an expressive, inquisitive STUDENT. Claude writes sessions/<slug>/<slug>-short.script.md and <slug>-long.script.md from the handout and source sheets, the user reads and revises them, and only then does ElevenLabs Text to Dialogue (eleven_v4, audio tags) voice them into <slug>-short.m4a and <slug>-long.m4a. Then Claude transcribes the audio locally to check it against the script, and links both on the page. This replaced the NotebookLM flow from Session 10 on. Use when the user says "make podcasts for session N", "short and long podcast", "deep dive for lesson N", "trailer", or wants a line, a voice or a take changed. Never send a script to ElevenLabs before the user has approved it.
---

# Lesson podcasts: script first, then ElevenLabs

Every lesson ships with two podcasts, a **short** and a **long** one. From
Session 10 on, both are made here. **Claude writes a script the user can read;
ElevenLabs only performs it.** So every claim and every quotation is checked
before anyone hears it, and a wrong line is fixed by editing one line.

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
python3 $P voices [search]  ·  python3 $P quota               # account voices · credits left
$UV --with websockets python $P render … --transport ws --yes   # experimental; see "Transports"
python3 $P render … --out X.m4a --model eleven_v3            # variants side by side, for comparing
```

## What each lesson gets

| Episode | Length | Words | Script → audio | What it is |
|---|---|---|---|---|
| **short** | ~20 min | ~3,000 | `<slug>-short.script.md` → `<slug>-short.m4a` | The overview: the session's aim and each part's core move, with one or two key quotations per part. Someone who hears only this should be ready for class. |
| **long** | ~40 min | ~6,000 | `<slug>-long.script.md` → `<slug>-long.m4a` | The deep dive: every part, in the handout's order, with the source sheets' primary texts read at length and each reading given at its strongest, along with its hardest question. |
| trailer | 2 min | ~300 | `<slug>-trailer.script.md` → `<slug>-trailer.m4a` | **Only when asked.** It asks the session's questions and answers none of them. `example-trailer.script.md` beside this file is a worked one (Session 9's test, never published). |

These names are the ones `publish-lesson` looks for, so keep them. The lengths
match the NotebookLM pairs (shorts ran 19–25 min, longs 30–71). The user may
ask for others: set them per lesson, and remember that the user reads every
word before it's voiced. The short is **not** the long one cut down. Write it
as its own episode, though it can reuse the long's best lines.

## The hosts

| Label | Voice | Who | Writes like |
|---|---|---|---|
| `TEACHER` | **Flint** – Deep, Raspy, and Warm (`qAZH0aMXY8tw1QufPN0D`) | An erudite teacher: has read the rabbis, the fathers and the commentaries, and wears it lightly. Warm, unhurried, exact. | Carries the content. Quotes the text word for word and says where it's from. Says "maybe" where scholars disagree, and states each view at its strongest. Enjoys the student's questions. |
| `STUDENT` | **Lauren** (`DODLEQrClDo8wCz460ld`) | An expressive, inquisitive student: quick, funny, honest about being surprised or unconvinced. | Asks what a class member would ask, at the moment they'd ask it. Reacts out loud ("Wait." "No way." "Oof."). Pushes back. Restates things in plain words, and sometimes gets there first. |

The user chose Flint and Lauren after hearing George and Jessica. Keep the pair
across every lesson so the class knows the voices. The front matter of every
script starts from this:

```yaml
---
title: "Session N — <short|long>: <lesson title>"
output: <slug>-<short|long>.m4a
model: eleven_v4
stability: 0.5
seed: <N>
speakers:
  TEACHER: { voice: qAZH0aMXY8tw1QufPN0D, name: Flint }    # Deep, Raspy, and Warm (library)
  STUDENT: { voice: DODLEQrClDo8wCz460ld, name: Lauren }   # library
---
```

The student is not a cheerleader and not a straw man. If every student line is
"Wow, that's fascinating," cut half of them and give the student a real
question or a real objection. The student should have **25–35% of the words**
(`check` prints the split).

**No invented lives.** The hosts are voices, not people. They don't have names
on air, and they don't claim a seminary, a congregation, a spouse or a
memory ("when I first read this…"). They don't mention being AI either. They
talk about the text.

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
parentheses and abbreviations, SSML, tags a listener can't hear, turns too
long to send, and tags crowding a turn. It also prints each host's share, the
estimated length, the chunk plan and the characters to be billed.

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
each in the background (a long episode is ~20 chunks, about 13 s each).

- **Chunking.** Each `---` section is split at turn boundaries into the fewest
  chunks of ≤ 1,800 characters, cut near equal shares so none is a stub. Each
  chunk is one Text to Dialogue request (the API's limit is 2,000).
- **Cache.** Each chunk is cached in `~/.cache/scripted-podcast/` under a hash of
  exactly what was sent: text, voices, model, settings and seed. A sidecar
  `.json` keeps the `request-id`, the `character-cost` and the time.
- **Stitching.** Chunks are voiced **in script order**. Each request carries
  `previous_request_ids` (the takes before it, up to 3), so a chunk picks up
  where the last one left off. When a chunk mid-script is retaken, it also
  carries `next_request_ids` (the takes after it), so it leads back into them.
  - Request ids can be stitched to for 2 hours only. Past that, or for a
    neighbour being re-voiced in the same run, the request sends 100
    characters of that neighbour's text instead (`previous_text`/
    `future_text`). The render line says which it used.
  - None of this is in the cache key, so an edit re-voices only its own chunk.
  - `stitch: false` sends chunks independently.
- **Truncation check.** After each chunk, the renderer compares its length
  with its word count and flags one much shorter than its text (cut off).
- **Assembly.** Chunks are joined with a 0.35 s gap, loudness-normalised to
  −16 LUFS, and encoded as **64 kbps mono AAC with `+faststart`**, about
  0.5 MB a minute. That keeps the site inside GitHub Pages' 1 GB limit, where
  audio is nearly all the bytes. The file's metadata carries the script's
  `title` and the ElevenLabs credit.

Cost on Creator is about 0.1 credit per character: roughly 5,000–6,000
credits a lesson for both episodes, out of 300,000 a month. Check with
`podcast.py quota`.

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
  chunk is re-voiced and billed, stitched to its neighbours.
- **The words are right but the delivery isn't:** add `<!-- take: 2 -->`
  (then 3, …) anywhere in that chunk's lines. That changes its seed, so it is
  re-voiced as a fresh take. Audition it alone with `--only N --copy`, which
  writes `<output>.chunkN.mp3` beside the script (gitignored). Then render the
  whole.
- **A retake's seam is audible** (common a day later, when the ids have
  expired): give the neighbouring chunk a take too, so the two are stitched
  afresh.
- **Mispronunciation:** respell the word in the script. The printed handout
  keeps the scholarly spelling; the script is for the voice.
- **Too flat, or too wild:** lower `stability` for more range (0.3–0.4), raise
  it for steadier reading (0.6–0.7). Every chunk re-voices.

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

*Voiced with [ElevenLabs](https://elevenlabs.io) from scripts written for this session.*

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
- **Follow the handout's parts, in its order.** In the long episode, each part
  usually goes like this:
  - the student's question;
  - the passage, read exactly by the teacher, with its reference;
  - what the words do (the Hebrew, the echoes, the counts, in plain words);
  - the readings, each at its strongest, with its hardest question;
  - the student's honest reaction or objection;
  - a landing line that hands on to the next part.

  Don't run every part on the same template. Vary the order and the pace.
- **Read the primary sources aloud.** In the long episode, the teacher reads
  key passages from the source sheets (Philo, Calvin, Rashi, the Talmud,
  *Atrahasis*), up to ~60 words each. Name the writer and their century. These
  readings are what NotebookLM could never get exactly right; they are the
  point of this flow.
- **Hand the listener the questions.** Each "Talk about it" box can become one
  question the student or teacher puts to the listener ("Here's one to bring
  with you…"). Offer it as a question, never as a verdict on what the class
  thinks.
- **Recap at the turns.** In the long episode, a two-line "so far" at the
  midpoint and before the landing helps the ear. The student often does it best
  ("So let me see if I've got this…").
- **Land on the handout's "So what?"** and close on a question to bring, then
  the session name.
- **Don't invent.** Every fact, number and attribution must be traceable to
  the handout or a sheet. If the script needs something the handout lacks, ask
  the user, or add it to the handout first. Don't slip it in by audio.

## Writing for the ear

- **One idea per turn; one to three sentences.** Long monologues are where
  listeners drift. Let the student break them up.
- **Quote exactly, and say the reference in words.** "Genesis six, verse six,"
  not `6:6`. "First Samuel fifteen." "The book of Numbers." Introduce a
  quotation so the ear knows it's one ("Verse eight: …").
- **Write "the Lord", never LORD.** CAPS mean emphasis to the voice.
- **Respell what a reader would stumble on.** Hebrew in the handout's spelling
  (*yēṣer*, *ḥēn*) gets read badly; write *yetzer*, *khen*, or skip the word
  and give its meaning.
- **No parentheses, footnotes, "cf.", "BCE".** Say "about two hundred and
  fifty years before Jesus", or just "before Jesus".
- **Numbers in words** where a person would say them that way.
- **Never point at a page.** Say "in the handout", not "on page three": page
  breaks move.
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

TEACHER: [quiet, measured] "The Lord regretted that he had made humankind on the earth."

STUDENT: [surprised] Wait. God *regretted*?
A turn may wrap onto following lines until a blank line.

---                                ← section break: chunks never cross it

## Part 2 — …
<!-- take: 2 -->                   ← re-rolls the chunk this sits in
TEACHER: …
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

## Audio tags

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

- **One tag at the start of a turn, most of the time; two at most.** About
  3–5 tags per 100 words is plenty (`check` prints the rate). Untagged lines
  read naturally. A tag is for a *change* in delivery.
- **The student gets the expressive tags; the teacher's are quieter** (`[warmly]`,
  `[chuckles]`, `[thoughtful]`).
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
  header shows. On Creator, v4 came to ~0.1 credit per character.
- **Output formats:** `mp3_44100_128` works on every tier. 192 kbps needs
  Creator; 44.1 kHz PCM/WAV needs Pro. The renderer re-encodes to 64k mono
  anyway.
- **Determinism:** `seed` makes output repeatable on a best-effort basis only.
  Changing the seed (a take) is the supported way to get a different
  performance of the same text.

## Voices

- `podcast.py voices [search]` lists the account's own voices (`GET /v2/voices`).
  Library voices aren't listed there. `GET /v1/shared-voices?search=…` finds
  them, and on a paid plan their ID works directly, without adding them to the
  account. That's how Flint and Lauren are used.
- **Default ("premade") voices** (George, Jessica, Brian…) **are retired on
  2026-12-31**, so a script that names one can't be re-voiced after that.
- To audition a new voice, give it to one speaker and render one chunk with
  `--only 1 --copy`. Let the user listen before re-voicing everything.

## The API key

`podcast.py` reads `$ELEVENLABS_API_KEY`, or else `ELEVENLABS_API_KEY=…`
from **`~/.config/genesis/elevenlabs.env`** (mode 0600, outside the repo;
`*.env` is also gitignored). Never commit it or echo it.

The current key is unrestricted but **locked to this machine's public IPv4**
(`curl -4 https://api.ipify.org`). It's a residential address and can change.
If every call suddenly fails with an IP or authorisation error, check the
address and ask the user to update the key's allow-list. A scoped key needs
**Text to Speech** (dialogue included), plus **Voices: read** and **User:
read** for `voices` and `quota`.

## Licensing and credit

The account is on a paid plan (Creator), so the free plan's rules (non-commercial
use only, "elevenlabs.io" in the published title) don't bind. Credit
ElevenLabs anyway, as the project credits every source:
- the renderer writes `credit:` into each file's metadata;
- the Listen block says *Voiced with ElevenLabs*.

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
