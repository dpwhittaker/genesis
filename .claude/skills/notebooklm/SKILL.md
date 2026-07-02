---
name: notebooklm
description: Generate NotebookLM "Deep Dive" podcasts for a Genesis lesson. Uploads the lesson's handout + primary texts (as clean plain text) to the class NotebookLM notebook, then drives the site with claude-in-chrome to produce TWO Deep Dive audio episodes — a LONG one (Longer preset) and a MEDIUM one (Default preset) — each focus-prompted at the lesson you're working on (or narrower topics on request), and downloads them into sessions/<slug>/. Use when the user says "make podcasts for session N", "deep dive for lesson N", "generate the NotebookLM audio", "long and medium podcast". Browser-driven (no NotebookLM API): needs a Chrome with the Claude extension signed into the same claude.ai account; downloads land wherever that Chrome runs, so prefer a Chrome on THIS machine.
---

# NotebookLM Deep Dive podcasts

Genesis lessons ship with two podcasts (a long and a shorter one) generated from the lesson's handout + sources in **NotebookLM**. NotebookLM has **no API** for any of this — it is entirely browser automation via `claude-in-chrome`. This skill uploads the lesson's text sources, configures two Deep Dive episodes, and retrieves the audio into the repo (where the `publish-lesson` skill expects it).

**Default notebook:** `https://notebooklm.google.com/notebook/12348a6a-d64b-49f6-b764-99104fdd9321` (the class's existing project). Override only if the user names a different notebook.

## How the browser connection actually works (read this)

- Control is **not** over Tailscale and **not** a port/tunnel. The Claude-in-Chrome extension pairs a browser to your **claude.ai account**; any Chrome with the extension, signed into the *same account as this Claude session*, appears in `list_connected_browsers`. (claude-hub launches `claude --chrome`, so the integration is already enabled — but it does not itself pick the browser.)
- `file_upload` reads files from **this machine** (the one running Claude) and pushes them into the remote page's file input, ≤10 MB per call — so uploading sources works even if the browser is elsewhere.
- **Downloads go to the machine the browser runs on.** The user wants the audio to land here in the repo, so **prefer a Chrome on/reachable from this machine**. In practice the paired browser named "gpu-server" is the **Windows host's Chrome**, and WSL2 sees its downloads at **`/mnt/c/Users/<WinUser>/Downloads/`** (e.g. `/mnt/c/Users/David/Downloads/`) — that's where the `.m4a` files appear, not `~/Downloads`. Only fall back to the mini-pc browser for debugging / watching clicks (then the file is on the mini-pc and must be `scp`'d back — step 7 fallback).

## Prerequisites — check, and stop with a clear message if unmet

1. The target lesson exists: `sessions/<slug>/index.md`. Resolve `N` → slug (e.g. `2` → `02-history-or-poetry`).
2. A Chrome with the Claude extension is running and signed into the **same claude.ai account** — and, in that Chrome, the user is **signed into Google and NotebookLM**. (Claude can drive the browser but cannot log in for the user; entering Google credentials is the user's job.)
3. Confirm the length mapping and focus with the user if not already given: **long = "Longer" preset, medium = "Default" preset**; focus defaults to the lesson's theme unless they name specific topics.

## Step 1 — prep clean text sources

```bash
.claude/skills/notebooklm/prep-sources.sh <slug> <scratchpad-dir>
```

Pass this session's scratchpad directory as `<scratchpad-dir>` (its files are upload-eligible). It writes `<slug>__handout.txt` (the handout with front matter / HTML / kramdown stripped) and one `<slug>__text__<name>.txt` per file in `sessions/<slug>/texts/`, and prints their absolute paths. These plain-text files are what you upload — cleaner grounding than raw markdown, and a format NotebookLM always accepts. Keep the printed path list for step 4.

## Step 2 — pick the browser (required by the tool)

Call `list_connected_browsers`. Then **you MUST** call `AskUserQuestion` listing **every** connected browser as its own option (label = display name, deviceId in parentheses), plus a final option labeled exactly:
`Open a confirmation screen in every connected Chrome extension and let me select the right one there.`
Do not pick one yourself. On the user's choice: `select_browser` with that deviceId, or `switch_browser` for the final option. Prefer the browser flagged as on **this computer** if the user is unsure (downloads then land locally). If none are connected, stop and tell the user to open Chrome with the extension signed into the same claude.ai account.

## Step 3 — open a FRESH notebook for this lesson

`tabs_context_mcp` (createIfEmpty:true) → `tabs_create_mcp` → `navigate` to `https://notebooklm.google.com/`. Click **"Create notebook"** (top bar) to make a new, empty notebook for this lesson — this is cleaner than reusing the shared class notebook (no source-mixing, no isolation needed). Only reuse the default notebook URL if the user explicitly asks. If a Google sign-in wall appears, stop: the user signs in, then says "continue". Creating the notebook opens the add-source dialog automatically.

## Step 4 — add the sources as PASTED TEXT (not file upload)

**NotebookLM has no reachable file input** — the "Upload files" button opens a native OS picker you can't drive, and no `<input type=file>` exists in the DOM to target with `file_upload`. Use the **"Copied text"** path instead:

For each prepped `.txt` from step 1:
1. In the add-source dialog, `find`/click **"Copied text"** (icon `content_paste`).
2. `find` the "Pasted text" textbox and the "Insert" button. **`Read` the `.txt` file's content**, then `form_input` it into the textbox as the value. (Optionally lightly condense to clean prose — NotebookLM auto-titles the source from the text.)
3. Click **Insert**. The source appears in the Sources list, auto-titled.
4. Re-open **"Add sources"** and repeat for the next file.

(A single `form_input` value of ~25 KB works fine. NotebookLM auto-generates a title and notebook name from the content.)

## Step 5 — isolate this lesson's sources

Only needed if you **reused** a shared notebook (skip for a fresh one). In the Sources panel, deselect every source except the ones just added, so the Deep Dive is grounded only on this lesson.

## Step 6 — generate the two Deep Dives (can run in PARALLEL)

Both episodes can generate at once — queue the long one, then immediately queue the medium; you do **not** have to wait or download between them. Each takes several minutes.

For each episode (queue LONG, then MEDIUM):

1. Click **"Customize Audio Overview"** (the settings affordance on the Audio Overview card; `find` it by that name).
2. In the **Customize Audio Overview** dialog: leave **Format = Deep Dive** (default, first tile, has the checkmark). Language = English. The **Length** control is three radios labelled **Short / Default / Long**:
   - LONG → click **Long**
   - MEDIUM → click **Default**
3. Set the **focus textbox** ("What should the AI hosts focus on in this episode?") via `form_input` with the **focus prompt** (below). NotebookLM also offers auto-suggested focus chips — ignore them; set the full prompt explicitly.
4. Click **Generate**. The Studio panel shows "Generating Audio Overview… Come back in a few minutes."
5. Re-open Customize and repeat for the second episode. Do not busy-poll; check back after several minutes.

**Focus prompt template** (fill from `sessions/<slug>/index.md` — its title and the "Aim of this session" section):

> Focus this episode on **<lesson title>**. Center the conversation on the lesson's main argument: <one-sentence aim, paraphrased from the handout>. Ground everything in the uploaded sources; teach it for an adult small group; keep it warm and concrete. Do not drift to other lessons or outside material.

For the MEDIUM episode, add: "Keep it tighter — hit only the core moves."
If the user named specific topics, replace the focus sentence with those topics.

## Step 7 — retrieve the audio into the repo

When an episode is ready (Studio shows it with a duration, a ▶ play button, and a ⋮ menu), open its **⋮ → Download**. NotebookLM saves it named after the episode's auto-title, e.g. `The_Mathematical_Architecture_of_Genesis_1.m4a`.

- **Paired "gpu-server" Chrome (what actually happens):** it's the Windows host's Chrome, so downloads land at **`/mnt/c/Users/<WinUser>/Downloads/`** (e.g. `/mnt/c/Users/David/Downloads/`). Move both into the session folder — the LONGER (bigger/longer duration) is the long one:
  ```bash
  DL=/mnt/c/Users/David/Downloads
  mv "$DL/<long-episode-title>.m4a"   sessions/<slug>/Longer_Podcast.m4a
  mv "$DL/<medium-episode-title>.m4a" sessions/<slug>/Medium_Podcast.m4a
  ```
  Match the existing naming style — session 1 uses `Longer_Podcast.m4a` / `Shorter_Podcast.m4a`.
- **Browser on the mini-pc (debug fallback):** the file is on the mini-pc; this server can't pull from it (WSL2 has no Tailscale route to the mini-pc), so have the user push it — from the mini-pc: `scp <file> gpu-server:~/projects/genesis/sessions/<slug>/`.

Then confirm both files exist and are non-trivial in size (`ls -lh sessions/<slug>/*.m4a`). Verify duration if `ffprobe` is available.

## Step 8 — link the podcasts in two places (match session 1)

Round each duration to whole minutes (from the `ffprobe` values, e.g. 40:15 → 40, 20:08 → 20). Then add links in **both** spots, exactly like session 1:

**1) `README.md` — append to this lesson's bullet line** (the `🎧 Podcasts:` suffix), medium first then long:

```markdown
🎧 Podcasts: [medium (<MED>m)](sessions/<slug>/Medium_Podcast.m4a) · [long (<LONG>m)](sessions/<slug>/Longer_Podcast.m4a)
```

(Session 1 labels its shorter one "short"; use the label that matches the file — "medium" for `Medium_Podcast.m4a", "short" for `Shorter_Podcast.m4a`.)

**2) `sessions/<slug>/index.md` — a `## 🎧 Listen` section near the top** (right after the opening `**Passage:**` line / before the first `##` section), with inline `<audio>` players and a download fallback. **Wrap it in `<div class="no-print" markdown="1">…</div>`** so it renders on screen but is **hidden in the printed handout** (audio players are dead weight on paper, and it saves a page):

```markdown
<div class="no-print" markdown="1">

## 🎧 Listen

Two companion podcasts for this session — good before you read, or to revisit afterward:

- **Medium overview** (~<MED> min): <audio controls preload="none" src="Medium_Podcast.m4a">Your browser can't play audio — [download the file](Medium_Podcast.m4a).</audio>
- **Longer deep dive** (~<LONG> min): <audio controls preload="none" src="Longer_Podcast.m4a">Your browser can't play audio — [download the file](Longer_Podcast.m4a).</audio>

</div>
```

Keep the `src`/href as bare filenames (the page is served from the session dir, so relative links resolve). The `markdown="1"` attribute lets kramdown process the markdown inside the div. After adding it, **re-run the `print-session` page-break pass** — the Listen block (though print-hidden) plus any other new content can still shift on-screen layout, and page counts must stay even with no warnings.

## Step 9 — report

Tell the user the two files, their durations, and that they're in `sessions/<slug>/` and linked in the README bullet + the page's 🎧 Listen section. `publish-lesson` expects a short/long (or medium/long) pair here and will pick these up (it globs `*.m4a`). Leave committing to the user unless asked.

## Gotchas

- **No API — the UI drifts.** Locate every control by visible text via `find`/`read_page`, not fixed coordinates. If a step's control isn't found, screenshot, re-read the page, and adapt; if stuck after 2–3 tries, stop and ask the user to point at it (or temporarily switch to the mini-pc browser so they can watch).
- **Never click file inputs** — always `file_upload` by `ref`.
- **Don't trigger native dialogs** (alerts/pickers) — they freeze the extension.
- **Generation is slow (minutes).** Don't busy-poll; check back at intervals.
- **Login is the user's job.** If any Google/consent wall appears, stop and hand off; do not enter credentials.
- **Shared notebook drift.** Sources accumulate; always do step 5 (isolate) or the podcast will blend lessons.
