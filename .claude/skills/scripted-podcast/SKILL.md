---
name: scripted-podcast
description: Write, revise and voice a two-host podcast for a Genesis lesson WITHOUT NotebookLM — an erudite TEACHER and an expressive, inquisitive STUDENT. Claude drafts a script grounded in the lesson's handout and source sheets (sessions/<slug>/<slug>-<kind>.script.md), the user reads and revises it, and only then does ElevenLabs Text to Dialogue (eleven_v4, with audio tags like [curious] or [laughs]) voice it, chunk by chunk and cached, into sessions/<slug>/<slug>-<kind>.m4a. Use when the user asks for a trailer or teaser, a scripted or ElevenLabs podcast, a "two-voice" episode, or wants to change a line or a voice in one. Never send a script to ElevenLabs before the user has approved it.
---

# Scripted podcast: script first, then ElevenLabs

NotebookLM (the `notebooklm` skill) writes and voices in one opaque step: you
can steer it, but you can't read or fix what it will say. This skill splits the
two. **Claude writes a script the user can read; ElevenLabs only performs it.**
So every claim and every quotation is checked before anyone hears it, and a
wrong line is fixed by editing one line.

Use it for anything short and exact: a two-minute **trailer**, a focused
episode on one part of a lesson, a retake of something NotebookLM got wrong.
For a 20–70 minute free-ranging deep dive, NotebookLM is still the cheaper
tool.

The tool is `podcast.py` beside this file (Python 3 stdlib plus PyYAML, both
on the system `python3`; ffmpeg for audio):

```bash
P=.claude/skills/scripted-podcast/podcast.py
python3 $P check  sessions/<slug>/<slug>-trailer.script.md   # lint, stats, chunk plan, cost; no API calls
python3 $P render sessions/<slug>/<slug>-trailer.script.md   # dry run: says what would be sent
python3 $P render … --yes                                     # voice new/changed chunks, assemble the .m4a
python3 $P render … --only 2 --yes --copy                     # voice/audition chunk 2 alone
~/.local/bin/uv run --no-project --with websockets --with pyyaml \
  python $P render … --transport ws --yes                     # whole script in one WebSocket session
python3 $P render … --out X.m4a --model eleven_v3             # variants side by side, for comparing
python3 $P voices [search]                                    # voices this account can use
python3 $P quota                                              # credits used / left
```

## The hosts

| Label | Who | Writes like |
|---|---|---|
| `TEACHER` | An erudite teacher: has read the rabbis, the fathers and the commentaries, and wears it lightly. Warm, unhurried, exact. | Carries the content. Quotes the text word for word and says where it's from. Says "maybe" when scholars disagree, and states each view at its strongest. Enjoys the student's questions. |
| `STUDENT` | An expressive, inquisitive student: quick, funny, honest about being surprised or unconvinced. | Asks what a class member would ask, at the moment they'd ask it. Reacts out loud ("Wait." "No way." "Oof."). Pushes back. Restates things in plain words, and sometimes gets there first. |

The student is not a cheerleader and not a straw man. If every student line is
"Wow, that's fascinating," cut half of them and give the student a real
question or a real objection. Aim for the student to have **at least a quarter
of the words** (`check` prints the split); trailers can run nearer a third.

Voices are set per script in the front matter, so a series can keep the same
pair. Pick them with `podcast.py voices` (see *Voices* below), and keep the
pair contrasting in pitch and pace so a listener always knows who is talking.

## Workflow

### 1. Gather (read, don't skim)

- `sessions/<slug>/index.md`: the handout. **This is the source of truth.**
  Everything voiced must be in it, or in its `texts/` sheets.
- `sessions/<slug>/texts/*.md`: the source sheets, for exact quotations.
- `sessions/<slug>/NOTES.md`: why the session is shaped the way it is, and
  what was **cut** (and why). Never voice anything that is only in NOTES.
- The project `CLAUDE.md` and memories: the audience is the class, quotations
  are NET, the time of day stays generic, contested questions get both sides,
  and New Testament readings are authoritative.

### 2. Plan the length

Budget words at **150 per minute** (`check` estimates the same way; v4
dialogue often runs a little faster):

| Kind | Length | Words | File |
|---|---|---|---|
| trailer | 2 min | ~300 | `<slug>-trailer.m4a` |
| short episode | 8–12 min | 1,200–1,800 | `<slug>-<topic>.m4a` |
| episode | 15–25 min | 2,200–3,800 | `<slug>-<topic>.m4a` |

Don't reuse `-short`/`-long`: those names belong to the NotebookLM pair that
`publish-lesson` looks for.

Outline the beats before writing lines. A **trailer** asks the session's
questions and answers none of them: a cold open on the most startling line, three
or four quick hooks (one per part of the handout), and a close that names the
session and says where to find it. An **episode** follows the handout's parts.
Give each part a question the student asks, the text, the readings, and a
landing.

### 3. Draft the script

`sessions/<slug>/<slug>-<kind>.script.md` (format below). It is committed with
the session. `_config.yml` keeps `*.script.md` out of the published site.

### 4. Check it

`podcast.py check` until there are no `ERROR`s, and read every `warn`. It catches
references written as digits, LORD in capitals, transliteration diacritics,
parentheses and abbreviations, SSML, tags a listener can't hear, over-long
turns, and chunks over the 2,000-character request limit. It also prints the
estimated length and the characters to be billed.

### 5. STOP: the user reads the script

Show the user the script (its path, and for a trailer the whole text in the
reply), the estimated length, the word split and the cost. **Do not render until
they approve.** Revise as asked, re-run `check`, and show it again. This loop is
the point of the skill. It costs nothing, so iterate freely here rather than
after voicing.

### 6. Voice it

`podcast.py render <script> --yes`. Each chunk is one Text to Dialogue request.
It is cached in `~/.cache/scripted-podcast/` under a hash of exactly what was
sent: text, voices, model, settings and seed. A sidecar `.json` keeps the
`request-id` and `character-cost`.

Chunks are voiced **in script order and stitched**. Each request carries
`previous_request_ids` (the takes before it, up to 3), so a chunk picks up
where the last one left off. When a chunk mid-script is retaken, it also
carries `next_request_ids` (the takes after it), so it leads back into them.
Request ids can only be stitched to for 2 hours. Past that, or for a
neighbour being re-voiced in the same run, the request sends 100 characters
of that neighbour's text instead (`previous_text`/`future_text`). The render
line says which it used. None of this is part of the cache key, so an edit
still re-voices only its own chunk. Set `stitch: false` to send chunks
independently.

The chunks are then joined with a 0.35 s gap,
loudness-normalised to −16 LUFS, and encoded as **64 kbps mono AAC with
`+faststart`**, the same encoding the NotebookLM podcasts get, so the site stays
under the GitHub Pages 1 GB limit. The assembled file carries the script's
`title` and the ElevenLabs credit in its metadata.

Report the duration and the cost. The user listens. **You can't**, so never
describe how it sounds.

### 6b. Or over the WebSocket (no chunk seams)

`--transport ws` sends the whole script through the Text to Dialogue
WebSocket (`wss://api.elevenlabs.io/v1/text-to-dialogue/stream-input`) in one
session. `---` breaks are ignored, and the 2,000-character limit doesn't
apply. What we found on 2026-10-09 (Session 9 trailer, `eleven_v4`):

- **It takes `eleven_v4`**, although the API reference says v3 only (the
  guides say v3 or v4). History logs it as v4.
- **It doesn't voice the script in one pass.** The server makes one generation
  per turn: your account history shows one entry per turn under one
  request-id. So it swaps the one seam of a two-chunk render for a boundary at
  every change of speaker, where seams are least audible anyway.
- **Each turn must be sent with `flush: true`** (the renderer does this). If it
  isn't, the server holds back the last word or two of each turn and voices them
  as a separate fragment ("…every one of" / "them."). A trailing space
  didn't help.
- It cost the same as REST, and ran about 8% longer (2:25 vs 2:14) with longer
  pauses between turns. Retakes are all-or-nothing: a take or an edit anywhere
  re-voices the whole session.
- It needs the `websockets` package, which isn't in any venv here, so run it
  under `uv run` as shown above.

For the Session 9 trailer, both transports came back word-complete. At the
REST seam, the pause (0.50 s) and loudness (−23.5 vs −22.9 LUFS) matched the
rest of the file. **The user found the chunked REST version better:** its seam
was inaudible, and the voices "sounded more like they were naturally reacting
to each other." That fits the history: REST voices a whole chunk of dialogue in
one generation, while the WebSocket voices each turn alone. Default to REST.

### 7. Iterate on the audio

- **A line is wrong, or reads badly:** edit it and render again. Only the
  chunk(s) containing changed text are re-voiced and billed.
- **The words are right but the delivery isn't:** add `<!-- take: 2 -->`
  (then 3, …) anywhere in that chunk. That changes its seed, so it is re-voiced
  as a fresh take. Audition it alone with `--only N --copy`, which writes
  `<output>.chunkN.mp3` beside the script (gitignored), then render the whole.
- **A voice is wrong:** change it in the front matter. Every chunk re-voices.
- **Mispronunciation:** respell the word for the ear in the script (the
  printed handout keeps the scholarly spelling; the script is for the voice).
- **Too flat, or too wild:** lower `stability` for more emotional range
  (0.3–0.4), raise it for steadier reading (0.6–0.7).

### 8. Put it on the page

Same pattern as the NotebookLM podcasts (see the `notebooklm` skill, step 8):

- `sessions/<slug>/index.md`: add a line to the `## 🎧 Listen` block (inside its
  `no-print` div). A trailer goes **first**:
  `- **Two-minute trailer**: <audio controls preload="none" src="<slug>-trailer.m4a">…</audio>`
- `README.md`: add it to the lesson's `🎧 Podcasts:` links, e.g.
  `[trailer (2m)](sessions/<slug>/<slug>-trailer.m4a) · [short (23m)](…) · …`
- Credit ElevenLabs where the audio is offered (see *Licensing*), and keep the
  session's existing Scripture attribution, which already covers NET quotations.
- `index.md` changed, so re-render the PDF with `print-session`. The Listen
  block doesn't print, but `publish-lesson` refuses a PDF older than its page.
- Commit the script, the `.m4a`, and the page/README edits together.

## Script format

```markdown
---
title: "Session 9 — trailer"              # metadata title of the .m4a
output: 09-regret-and-grace-trailer.m4a   # relative to the script
model: eleven_v4                          # default eleven_v4
stability: 0.5                            # default 0.5; lower = more expressive
seed: 9                                   # any integer; a take adds to it
# similarity: 0.75                        # optional; how closely to hold the voice
# stitch: false                           # default true: condition chunks on their neighbours
# language: en
speakers:
  TEACHER: { voice: <voice_id>, name: <voice name, for humans> }
  STUDENT: { voice: <voice_id>, name: <voice name> }
---

<!-- Notes for writers and reviewers. Never voiced; may span lines. -->

## Cold open        ← headings organise the script for readers; never voiced

TEACHER: [quiet, measured] "The Lord regretted that he had made humankind on the earth."

STUDENT: [surprised] Wait. God *regretted*?
A turn may wrap onto following lines until a blank line.

---                ← chunk break: each chunk is one request, one cache entry, one retake unit

## Next part
<!-- take: 2 -->
TEACHER: …
```

- A turn is `LABEL: text`, where LABEL is a key of `speakers`. After a blank
  line, any text must start a new turn.
- `*emphasis*` is stripped before sending. It's for the human reader. To make
  the voice stress a word, use CAPS (sparingly) or reword the sentence.
- Put a `---` break every ~1,000–1,800 characters, at a topic change. Each
  request must stay **≤ 2,000 characters**. A seam between chunks is a slight
  pause and may shift the voices' energy a little, so put it where a pause
  belongs. A two-minute trailer fits in one or two chunks.

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
- **Contractions and spoken rhythm.** "It's", "doesn't", fragments, a "Wait."
  An ellipsis (…) trails off or hesitates; a dash cuts in. Use both
  sparingly: v4 takes punctuation seriously.
- **Interruptions:** end the cut-off line with a dash ("so the flood was—")
  and start the next turn with `[interrupting]` or `[jumping in]`.
- **Class rules hold in audio, too.** Talk *to* the class, never *about*
  them. Use "today", "this session", "last session", never "tonight" or "this
  morning". Lay out contested questions at their strongest on each side. Where
  the New Testament reads a passage, it settles it for this class. And nothing
  goes in that the handout has dropped.
- **Avoid podcast tics:** "Exactly!", "Right?", "That's fascinating",
  "unpack", "deep dive", "let's dive in", "game-changer". Not every turn opens
  with a reaction.

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
  `[chuckles]`, `[thoughtful]`). A grave, professional voice won't do
  `[giggles]` convincingly.
- **Only tag what can be heard.** `[smiling]`, `[nods]`, `[pacing]`,
  `[music]`: the model may read the word aloud or invent a sound effect.
  Describe the voice instead. `check` flags these.
- **Sound-effect tags are real** (`[applause]`, `[door creaks]`). Don't use
  them in class material.
- **No SSML.** `<break time="1s"/>` doesn't work on v3/v4. Use `[pause]`, an
  ellipsis, or a new turn.

## ElevenLabs facts (checked 2026-10-09)

- **Endpoint:** `POST https://api.elevenlabs.io/v1/text-to-dialogue?output_format=mp3_44100_128`,
  header `xi-api-key`. The body is `{inputs: [{text, voice_id}], model_id,
  settings: {stability, similarity}, seed, language_code?, previous_text?,
  future_text?, apply_text_normalization?}`. The response is raw audio bytes;
  a 422 returns `{detail: [...]}`. Docs:
  <https://elevenlabs.io/docs/api-reference/text-to-dialogue/convert>, and the
  cookbook <https://elevenlabs.io/docs/eleven-api/guides/cookbooks/text-to-dialogue>.
- **Models:** `eleven_v4` (released 2026-09-28; recommended) and `eleven_v3`
  (the API's default, now "previous generation"). Only these two do dialogue
  and audio tags. Style and speed settings don't apply to v4.
- **Limits:** ≤ 2,000 characters of text per request ("longer requests may end
  early or return a validation error"), and ≤ 10 distinct voices.
  `previous_text`/`future_text` are 100 characters each and "not supported by
  every model". Request stitching (`previous_request_ids`/`next_request_ids`,
  ≤ 3 each, ids < 2 hours old) is **not** available on v3. v4 accepts it
  (2026-10-09).
- **Billing:** per character, tags included (the `character-cost` response
  header is recorded in each chunk's sidecar). API usage is priced at about
  $0.08 per 1,000 characters on v3 and v4, so a two-minute trailer costs well
  under a dollar, and retakes only re-bill their chunk. The free plan has
  10,000 credits a month.
- **Output formats:** `mp3_44100_128` works on every tier. 192 kbps needs
  Creator; 44.1 kHz PCM/WAV needs Pro. The renderer re-encodes to 64k mono
  anyway.
- **Determinism:** `seed` makes output repeatable on a best-effort basis only.
  Changing the seed (a take) is the supported way to get a different
  performance of the same text.

## Voices

- `podcast.py voices [search]` lists what the account can use (`GET /v2/voices`).
- **Default ("premade") voices** (George, Jessica, Brian…) exist only on
  accounts created before March 2026, and **are retired on 2026-12-31**. Audio
  already rendered keeps working, but a script that names one can't be
  re-voiced after that, so prefer library or designed voices for anything
  you'll keep revising.
- **Voice Library voices can't be used through the API on the free tier.** On a
  free account the API voices are the premade ones (if the account is old
  enough) and up to three of your own Voice Design voices.
- Listed replacements for the premade voices include, for a teacher, *Wyatt –
  Seasoned Mentor*, *Darian – Warm Grounded Storyteller* and *Caleb – Trusted
  Guide*; for a student, *Jade – Upbeat and Natural* and *Elowen – Upbeat Modern
  Narrator*. On a paid plan, a library voice's ID works directly. No need to
  add it to the account first: `GET /v1/shared-voices?search=…` finds the ID.
  The Session 9 trailer uses *Flint – Deep, Raspy, and Warm*
  (`qAZH0aMXY8tw1QufPN0D`) as the teacher and *Lauren*
  (`DODLEQrClDo8wCz460ld`) as the student, the user's choice after hearing
  George and Jessica.
- After choosing, voice one short chunk with `--only 1 --copy` and let the user
  listen before rendering the whole thing.

## The API key

`podcast.py` reads `$ELEVENLABS_API_KEY`, or else
`ELEVENLABS_API_KEY=…` from **`~/.config/genesis/elevenlabs.env`** (mode 0600,
outside the repo; `*.env` is also gitignored). Never commit it or echo it.

ElevenLabs keys are scoped. This skill needs **Text to Speech** (dialogue
included), plus **Voices: read** for `voices` and **User: read** for `quota`.
A key made for speech-to-text, like Faceclaw's, fails with `missing the
permission text_to_speech`. Make a separate key for this project and give it a
credit limit.

## Licensing

ElevenLabs output from a **free** plan may be used only non-commercially, and
published content must carry "elevenlabs.io" in its title. This class site is
non-commercial. Credit ElevenLabs regardless, as the project credits every
source: the renderer puts `credit:` (default *Voiced with ElevenLabs
(elevenlabs.io)*) in the file's metadata, and the page's Listen line should say
it too. On a paid plan the requirement falls away, but the credit costs nothing.
The words are ours; the quotations follow the project's sourcing rules (NET for
Scripture), and the session page's attribution covers them.

## Gotchas

- **You can't hear the result.** Don't call it good; the user is the judge.
  What you can check: the duration matches the estimate (a chunk far shorter
  than its text means it was cut off), and `ffmpeg -v error -i out.m4a -f null -`
  decodes cleanly.
- **A chunk over 2,000 characters fails or gets truncated.** `check` makes it an
  error before anything is sent.
- **Stitching ids expire after 2 hours.** A retake the next day falls back to
  its neighbours' text, which is weaker. If a retake's seam is audible, re-voice
  the neighbour as well (add a take to it too) so the two are stitched afresh.
- **The cache is keyed on what was sent**, so changing `model`, a voice,
  `stability`, `seed` or any word re-voices that chunk. Comments, headings and
  `*emphasis*` marks don't.
- **`--force`** re-voices even cached chunks. You rarely want it: use a take.
