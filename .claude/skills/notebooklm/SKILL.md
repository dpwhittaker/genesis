---
name: notebooklm
description: Generate NotebookLM "Deep Dive" podcasts for a Genesis lesson. Adds the lesson's handout + primary texts (as clean plain text, fetched from the pushed repo) to a fresh NotebookLM notebook, then drives the site with claude-in-chrome to produce TWO Deep Dive audio episodes — a LONG one (Long preset) and a SHORT one (Default preset) — each focus-prompted at the lesson you're working on (or narrower topics on request), and downloads them into sessions/<slug>/ as <slug>-long.m4a and <slug>-short.m4a. Use when the user says "make podcasts for session N", "deep dive for lesson N", "generate the NotebookLM audio", "long and short podcast". Browser-driven (no NotebookLM API): needs a Chrome with the Claude extension signed into the same claude.ai account; downloads land wherever that Chrome runs, so prefer a Chrome on THIS machine.
---

# NotebookLM Deep Dive podcasts

> **Back in use from Session 11 (October 2026).** Session 10's podcasts were scripted and voiced with the `scripted-podcast` skill; the user then switched back to NotebookLM. `scripted-podcast` stays available if asked for by name.

Genesis lessons ship with two podcasts (a long and a shorter one) generated from the lesson's handout + sources in **NotebookLM**. NotebookLM has **no API** for any of this — it is entirely browser automation via `claude-in-chrome`. This skill uploads the lesson's text sources, configures two Deep Dive episodes, and retrieves the audio into the repo (where the `publish-lesson` skill expects it).

**Each lesson gets a fresh notebook** (step 3). The class's old shared notebook, `https://notebooklm.google.com/notebook/12348a6a-d64b-49f6-b764-99104fdd9321`, is reused only if the user asks for it.

## How the browser connection actually works (read this)

- Control is **not** over Tailscale and **not** a port/tunnel. The Claude-in-Chrome extension pairs a browser to your **claude.ai account**; any Chrome with the extension, signed into the *same account as this Claude session*, appears in `list_connected_browsers`. (claude-hub launches `claude --chrome`, so the integration is already enabled — but it does not itself pick the browser.)
- **Sources don't travel through Claude.** NotebookLM has no file input to upload into, so the page fetches the lesson's committed files from GitHub itself and pastes them in (step 4). That works wherever the browser runs.
- **Downloads go to the machine the browser runs on.** The user wants the audio to land here in the repo, so **prefer the Chrome running on this host** — this machine has a desktop session with `google-chrome` installed, and its downloads land in `~/Downloads`, on the same filesystem as the repo. Only fall back to a browser on another device for debugging / watching clicks (then the file is on that device and must be copied back — step 7 fallback).

## Prerequisites — check, and stop with a clear message if unmet

1. The target lesson exists: `sessions/<slug>/index.md`. Resolve `N` → slug (e.g. `2` → `02-history-or-poetry`).
2. A Chrome with the Claude extension is running and signed into the **same claude.ai account** — and, in that Chrome, the user is **signed into Google and NotebookLM**. (Claude can drive the browser but cannot log in for the user; entering Google credentials is the user's job.)
3. Confirm the length mapping and focus with the user if not already given: **long = "Long" preset → `<slug>-long.m4a`, short = "Default" preset → `<slug>-short.m4a`**; focus defaults to the lesson's theme unless they name specific topics.

## Step 1 — commit and push the sources

The browser fetches the handout and source sheets from GitHub at the current commit (step 4), so whatever the podcasts should hear must be **committed and pushed** first — usually it already is, after `print-session`. `add-sources-js.sh` refuses to run if `sessions/<slug>/` has uncommitted changes or HEAD is not on `origin/main`.

What NotebookLM receives is the clean plain text that `prep-sources.sh` makes — the handout as `<slug>__handout.txt` and one `<slug>__text__<name>.txt` per file in `texts/`, with front matter, HTML and kramdown stripped. To read exactly what the hosts will be grounded on:

```bash
.claude/skills/notebooklm/prep-sources.sh <slug> <scratchpad-dir>
```

## Step 2 — pick the browser (required by the tool)

Call `list_connected_browsers`. Then **you MUST** call `AskUserQuestion` listing **every** connected browser as its own option (label = display name, deviceId in parentheses), plus a final option labeled exactly:
`Open a confirmation screen in every connected Chrome extension and let me select the right one there.`
Do not pick one yourself. On the user's choice: `select_browser` with that deviceId, or `switch_browser` for the final option. Prefer the browser flagged as on **this computer** if the user is unsure (downloads then land locally). If none are connected, stop and tell the user to open Chrome with the extension signed into the same claude.ai account.

## Step 3 — open a FRESH notebook for this lesson

> **Rebrand (seen live 2026-07-29): NotebookLM is now "Gemini Notebook."** `notebooklm.google.com` redirects to **`notebook.google.com`**, the page title is "Gemini Notebook," and a first-visit welcome modal ("NotebookLM is now Gemini Notebook… **Let's go**") overlays the UI — dismiss it before anything else or clicks land on the overlay. The Studio panel is also restructured into a tile grid (Audio Overview / Slide Deck / Video Overview / Mind Map / Reports / Flashcards / Quiz / Infographic / Data Table); there is no longer a separate "Customize Audio Overview" affordance — click the **Audio Overview** tile and the Customize dialog opens directly. The dialog's own contents are unchanged.

`tabs_context_mcp` (createIfEmpty:true) → `tabs_create_mcp` → `navigate` to `https://notebook.google.com/`. Click **"New notebook"** (top right of the notebook list) to make a new, empty notebook for this lesson — this is cleaner than reusing the shared class notebook (no source-mixing, no isolation needed). Only reuse the old shared notebook if the user explicitly asks. If a Google sign-in wall appears, stop: the user signs in, then says "continue". The new notebook may or may not open the add-source dialog by itself (Session 11's didn't); step 4's script copes with either.

## Step 4 — add the sources: one script, fetched from GitHub

**NotebookLM has no reachable file input** — the "Upload files" button opens a native OS picker you can't drive, and no `<input type=file>` exists in the DOM to target with `file_upload`. Sources go in through **"Copied text"**. Don't retype them: a lesson's sources run to ~140 KB, and pasting that through `form_input` means writing every byte out again. Let the page fetch them:

```bash
.claude/skills/notebooklm/add-sources-js.sh <slug> > <scratchpad-dir>/add-sources.js
```

It prints a ~3 KB script: a `CONFIG` line (the repo at HEAD's SHA, each file's path, and the byte size `prep-sources.sh` makes of it) followed by `add-sources.js`. `Read` that file and pass its whole content as `text` in **one** `javascript_tool` call on the notebook tab. For each source the script:

1. fetches the markdown from `raw.githubusercontent.com` (it sends `Access-Control-Allow-Origin: *`, and the SHA pins the exact commit);
2. cleans it the way `prep-sources.sh` does, and **stops with an error if the result differs by a single byte** from what `prep-sources.sh` produced;
3. opens **Add sources → Copied text**, fills the **Pasted text** box (native value setter + `input` event, so the page sees it), clicks **Insert**, and waits for the dialog to close.

It returns `[{path, bytes}]` for every source added. Then take a screenshot: the Sources panel should list them all, each checked, auto-titled from its first heading.

Notes:

- **The repo must be public** for the unauthenticated fetch — it is.
- **Keep `clean()` in `add-sources.js` and `clean()` in `prep-sources.sh` in step.** The byte check catches any drift; if it fires, fix the JS, don't loosen the check. (Checked 2026-10-23: all 62 handouts and sheets in Sessions 1–11 come out byte-identical.)
- **The page has three textareas**: the "Discover sources" web-search box, the chat "Query box", and the "Pasted text" box. A generic `textarea` selector finds the search box first; the script targets `textarea[aria-label="Pasted text"]`.
- **Fallback, if the fetch is ever blocked:** `Read` each `.txt` from `prep-sources.sh` and `form_input` it into the Pasted text box by `ref`, then click **Insert**, once per file. A ~40 KB value works; it is just slow.

## Step 5 — isolate this lesson's sources

Only needed if you **reused** a shared notebook (skip for a fresh one). In the Sources panel, deselect every source except the ones just added, so the Deep Dive is grounded only on this lesson.

## Step 6 — queue the two Deep Dives: one script

Both episodes generate at once: queue them back to back, with no waiting or downloading between. Write the two focus prompts (template below) to files in the scratchpad, then:

```bash
.claude/skills/notebooklm/queue-audio-js.sh <scratchpad-dir>/focus-long.txt <scratchpad-dir>/focus-short.txt > <scratchpad-dir>/queue-audio.js
```

It checks each prompt against the dialog's 5000-character cap, appends the pronunciation line to a prompt that lacks it, and prints a script: a `CONFIG` line holding both prompts, followed by `queue-audio.js`. `Read` that file and pass its whole content as `text` in **one** `javascript_tool` call on the notebook tab. For each episode, long then short, the script:

1. clicks the **Audio Overview** tile in the Studio panel, which opens the **Customize Audio Overview** dialog directly;
2. checks **Format = Deep Dive** and **Language = English** (it stops rather than change the language);
3. selects the **Length**: **Long** for the long episode, **Default** for the short one (our "short" file is NotebookLM's Default preset, not its Short one);
4. fills the focus box ("What should the AI hosts focus on in this episode?") with the prompt, ignoring the suggested focus chips;
5. clicks **Generate now** (not "Generate later") and waits for the dialog to close.

It returns each episode it queued, with the dialog's source count (`6 sources`: check it matches the Sources panel), and the Studio panel's items. Take one screenshot to confirm both are generating. A "Get notified when it's ready — **Turn on notifications**" card appears too: leave it alone, since it opens Chrome's own permission prompt.

With `--dry-run` before the paths, the script does everything except generate: it fills and checks each dialog, then closes it. That makes it safe to try on any notebook after the UI changes. (Tested that way on Session 11's notebook on 2026-10-25; first real run Session 12, 2026-10-29, worked as written.)

**If a `javascript_tool` call is rejected or interrupted, it may still have run.** On Session 12 the user declined the permission prompt by accident and the queue script ran anyway; re-running it queued a second pair, four episodes in all. Before re-running `queue-audio.js`, read the Studio panel (`collect-audio.js` reports what is there) and queue only what is missing.

Then wait: run `sleep 480` as a background Bash command, not a busy poll. (Session 11: the Default episode was ready within about 9 minutes; the Long one was still going at 13 and done by 18.)

**Fallback, if the script stops:** its error names the control it couldn't find. Do that episode by hand: click the tile, `find` the controls and click by `ref` (the dialog often renders faded behind the notebook summary, so don't read it from a screenshot), `form_input` the prompt, and click **Generate now**.

**Focus prompt template** (fill from `sessions/<slug>/index.md` — its title and the "Aim of this session" section):

> Focus this episode on **<lesson title>**. Center the conversation on the lesson's main argument: <one-sentence aim, paraphrased from the handout>. Ground everything in the uploaded sources; teach it for an adult small group; keep it warm and concrete. Do not drift to other lessons or outside material. Say Bible references aloud as chapter then verse: "Genesis twelve three" for Genesis 12:3, never "twelve point three".

The last sentence is the user's standing instruction: keep it in every focus prompt, long and short. (`queue-audio-js.sh` appends it to a prompt that lacks it.)

For the SHORT episode, add: "Keep it tighter — hit only the core moves."
If the user named specific topics, replace the focus sentence with those topics.

## Step 7 — retrieve the audio into the repo

After each wait, pass the whole of `.claude/skills/notebooklm/collect-audio.js` as `text` in **one** `javascript_tool` call on the notebook tab. It needs no wrapper; it carries its own `CONFIG = { expect: 2 }`. It reads the Studio panel, where a finished episode shows its duration (`48:37 · Deep Dive · 6 sources · 1d ago`), a ▶ play button and a ⋮ button labelled **More**:

- **Until both are finished**, it returns `{waiting: "1 of 2 ready", studio: [...]}`. Wait again (a background `sleep 300`).
- **Once both are**, it returns `{ready: [{title, duration}, …]}`, longest first.
- **If it finds more finished episodes than it expects** (a reused notebook), it stops; pick the right ones by hand.

**Then download each with real clicks, not script.** **More → Download** opens a new tab that fetches the file, and Chrome blocks that tab unless the click is a genuine user gesture — a scripted `.click()` on the menu item does nothing at all, with no error (Session 12, 2026-10-29). For each episode: `find` "More button on the <title> studio item" → `computer left_click` by `ref` → `find` "Download menu item in the open menu" → `left_click` by `ref`. A blank "Untitled" tab flashes up in the tab group and usually closes itself once the download starts; close any that remain with `tabs_close_mcp`. Each file appears in `~/Downloads` within a few seconds.

NotebookLM names each file after the episode's auto-title, e.g. `The_Mathematical_Architecture_of_Genesis_1.m4a`. **The episodes finish in either order** (Session 11's Default one finished first, though queued second), so tell them apart by duration, never by order or title; the script lists the long one first.

- **Chrome on this host (the normal case):** downloads land in `~/Downloads`. Move both into the session folder — the LONGER (bigger/longer duration) is the long one:
  ```bash
  DL=~/Downloads
  mv "$DL/<long-episode-title>.m4a"  sessions/<slug>/<slug>-long.m4a
  mv "$DL/<short-episode-title>.m4a" sessions/<slug>/<slug>-short.m4a
  ```
  **Naming (from Session 8 on): `<slug>-short.m4a` and `<slug>-long.m4a`** — the
  Default-preset episode is "short", the Long-preset one "long". The slug in the
  name keeps a downloaded file identifiable on someone's phone. Sessions 1–7 keep
  their older names (`Medium_Podcast.m4a` / `Longer_Podcast.m4a`, and session 1's
  `Shorter_Podcast.m4a`): their URLs are already in past GroupMe posts, emails and
  Church Center resources, so renaming them would break links the class has.
- **Browser on another device (debug fallback):** the file is on that device. Both machines are on the tailnet, so either pull it (`scp <peer>:<file> sessions/<slug>/`) or have the user push it — from that device: `scp <file> gpu-server:~/projects/genesis/sessions/<slug>/`.

Then confirm both files exist and are non-trivial in size (`ls -lh sessions/<slug>/*.m4a`). Verify duration if `ffprobe` is available.

### Step 7b — RE-ENCODE before committing (required)

NotebookLM exports **257 kbps stereo AAC** — music-grade encoding on two people talking. Left alone, each session adds ~115 MiB and the site blows through **GitHub Pages' hard 1 GB published-site limit around session 9**. Audio is ~98% of this site's bytes, so this is the only size lever that matters.

Re-encode both files to **64 kbps mono** before committing. That is the knee of the quality curve (measured on session 4: SNR vs the original is 19.3 dB at 48k, **24.4 dB at 64k**, 26.4 dB at 80k — 48→64 buys 5.1 dB, 64→80 only 2.0), and it cuts **74%** off every file with duration preserved exactly.

```bash
for f in sessions/<slug>/*.m4a; do
  ffmpeg -hide_banner -loglevel error -y -i "$f" \
    -c:a aac -b:a 64k -ac 1 -ar 44100 -movflags +faststart "$f.tmp.m4a"
  # verify duration survived, then swap
  d0=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$f")
  d1=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$f.tmp.m4a")
  echo "$d0 $d1" | awk '{d=$1-$2; if(d<0)d=-d; exit (d<0.5)?0:1}' \
    && mv "$f.tmp.m4a" "$f" && chmod 644 "$f" \
    || { echo "DURATION MISMATCH on $f — keeping original"; rm -f "$f.tmp.m4a"; }
done
ffmpeg -hide_banner -v error -i sessions/<slug>/<slug>-long.m4a -f null -   # decode-integrity check; silence = clean
```

`+faststart` moves the moov atom to the front so the `<audio>` player can start before the whole file arrives. Durations are unchanged, so the minute labels in the README bullet and the 🎧 Listen block stay correct.

Two traps worth knowing:

- **`-loglevel error` suppresses `volumedetect`/`astats` output** (they print at info level). If you measure levels or SNR to sanity-check an encode, drop back to default loglevel or you'll silently get empty results.
- **Git LFS does not solve the Pages problem.** Pages serves the LFS *pointer file*, not the audio. Anything Pages must serve has to be a real file in the repo and counts against the 1 GB. Note also that the Pages limit measures the **current checkout, not history** — so re-encoding shrinks the published site immediately even though the original blobs stay in `.git` forever.

## Step 8 — link the podcasts in two places (match session 1)

Round each duration to whole minutes (from the `ffprobe` values, e.g. 40:15 → 40, 20:08 → 20). Then add links in **both** spots, exactly like session 1:

**1) `README.md` — append to this lesson's bullet line** (the `🎧 Podcasts:` suffix), short first then long:

```markdown
🎧 Podcasts: [short (<SHORT>m)](sessions/<slug>/<slug>-short.m4a) · [long (<LONG>m)](sessions/<slug>/<slug>-long.m4a)
```

(Sessions 1–7 predate this naming and label theirs "medium"/"short" against the old filenames; leave them.)

**2) `sessions/<slug>/index.md` — a `## 🎧 Listen` section near the top** (right after the opening `**Passage:**` line / before the first `##` section), with inline `<audio>` players and a download fallback. **Wrap it in `<div class="no-print" markdown="1">…</div>`** so it renders on screen but is **hidden in the printed handout** (audio players are dead weight on paper, and it saves a page):

```markdown
<div class="no-print" markdown="1">

## 🎧 Listen

Two companion podcasts for this session — good before you read, or to revisit afterward:

- **Short overview** (~<SHORT> min): <audio controls preload="none" src="<slug>-short.m4a">Your browser can't play audio — [download the file](<slug>-short.m4a).</audio>
- **Longer deep dive** (~<LONG> min): <audio controls preload="none" src="<slug>-long.m4a">Your browser can't play audio — [download the file](<slug>-long.m4a).</audio>

</div>
```

Keep the `src`/href as bare filenames (the page is served from the session dir, so relative links resolve). The `markdown="1"` attribute lets kramdown process the markdown inside the div. After adding it, **re-render the printable PDF with `print-session`** — the Listen block is print-hidden, so the layout should not move, but `index.md` has changed and the committed PDF must not be older than it (`publish-lesson` checks).

## Step 9 — report

Tell the user the two files, their durations, and that they're in `sessions/<slug>/` and linked in the README bullet + the page's 🎧 Listen section. `publish-lesson` expects the short/long pair here and will pick these up (it reads the README links and globs `*.m4a`). Commit the re-encoded audio, the page and README changes, and the re-rendered PDF, and push.

## Gotchas

- **No API — the UI drifts.** Locate every control by visible text via `find`/`read_page`, not fixed coordinates. The three scripts find controls by label and text too, and each stops with an error naming the control it couldn't find; fix the selector in the `.js` file, then re-test with `queue-audio-js.sh --dry-run`. If a step's control isn't found, screenshot, re-read the page, and adapt; if stuck after 2–3 tries, stop and ask the user to point at it (or temporarily switch to the mini-pc browser so they can watch).
- **Never click file inputs or "Upload files"** — it opens a native OS picker that freezes the extension. Sources go in as pasted text (step 4).
- **Don't trigger native dialogs** (alerts/pickers) — they freeze the extension.
- **Generation is slow (minutes).** Don't busy-poll; check back at intervals.
- **Login is the user's job.** If any Google/consent wall appears, stop and hand off; do not enter credentials.
- **Shared notebook drift.** Sources accumulate; always do step 5 (isolate) or the podcast will blend lessons.
