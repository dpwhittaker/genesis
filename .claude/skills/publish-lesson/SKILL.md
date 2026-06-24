---
name: publish-lesson
description: Publish a finished Genesis lesson to the class across three channels — add resource links to the Church Center group, email the group a short teaser with the links, and post the same to GroupMe. Use when the user says "publish lesson N", "send out session N", "the lesson is ready, push it to the group". HARD precondition: the lesson must have a complete, page-split-optimized handout plus a short AND a long podcast (and any other media linked under its README line) — refuse to publish if missing. ALWAYS draft the email + GroupMe text and get the user's explicit approval before sending anything. GroupMe goes via its REST API; Church Center has no API for resources/email, so those steps use the claude-in-chrome browser skill against an already-signed-in session.
---

# Publish a lesson

Takes one finished lesson and announces it to the class on three channels:

1. **Church Center → Resources** (browser): add the lesson's links to the group's resource list.
2. **Church Center → Email** (browser): email the group a short teaser + the links.
3. **GroupMe** (API): post the same teaser + links.

GroupMe has a real API; Church Center does **not** expose group resources or email sending, so those two are done by driving the member UI with `claude-in-chrome` against the user's already-signed-in Chrome.

## Trigger

`publish lesson <N|slug>` / "send out session N" / "push the lesson to the group". Resolve `<N>` to the session slug (e.g. `01` → `01-the-neighbors-stories`).

## Preconditions — verify ALL before publishing; refuse if any fails

A lesson is publishable only when it has, at minimum:

1. **A complete, page-split-optimized handout.** Run the **`print-session`** skill on the slug (render the live page → analyze). Require: page-break markers present **and** the analyzer reports **no warnings** (no sparse/overfull pages). If it warns, stop — the handout isn't ready; fix breaks first.
2. **A short podcast and a long podcast** in `sessions/<slug>/` (two `*.m4a`/audio files). If either is missing, stop.
3. **Everything committed and live on Pages.** `git status` clean for the session folder, and the session page + each media file return HTTP 200 on the published site.
4. **Other related media** linked under the lesson's line in `README.md` are included in the link set (step 1 below). "At minimum" is handout + 2 podcasts; include whatever else the README lists for that lesson.

If a precondition fails, tell the user exactly what's missing and stop. Do not partially publish.

## Step 1 — assemble the link set

```bash
.claude/skills/publish-lesson/lesson-links.sh <slug>
```

This prints the session page URL plus every media link the README lists under the lesson (short podcast, long podcast, any extras), and lists the local media files as a sanity check. Confirm the short + long podcast links are both present. This link set (3+ links) is what goes to all three channels.

## Step 2 — draft, then GET APPROVAL (hard gate)

Draft:
- a **short teaser** (2–4 sentences — what this session is about, an enticing hook), and
- the **link block**: session page, short podcast, long podcast, + extras.

Compose the **email** version (subject + body) and the **GroupMe** version (≤1000 chars, links inline). Then **show both to the user verbatim and wait for explicit approval** ("send it" / edits). Do **not** touch Church Center or GroupMe until approved. Preview the GroupMe text safely with:

```bash
node .claude/skills/publish-lesson/groupme-post.js --dry-run "…text…"
```

## Step 3 — publish (only after approval)

### 3a. Church Center — Resources (browser)

Load the claude-in-chrome tools, then drive the resources page:
`{CHURCHCENTER_BASE}/my/groups/{CHURCHCENTER_GROUP}/resources`
(from `~/.config/genesis/publish.env`; default group `reading-the-bible-like-rabbi-jesus`).

- Use `tabs_context_mcp` first; open a new tab to the resources URL.
- The member UI changes — **discover controls at runtime** with `find`/`read_page`; don't hardcode selectors. Re-`find` after every dialog open (refs renumber).
- Add each link as a resource (title = a clear label like "Session N — Long podcast"; URL = the published link). Add the session page and both podcasts at minimum.
- **Avoid anything that triggers a native confirm/alert dialog** (it freezes the extension) — see the claude-in-chrome dialog guidance.

### 3b. Church Center — Email (browser)

Navigate to `{CHURCHCENTER_BASE}/my/groups/{CHURCHCENTER_GROUP}/members/email/new`.
- Fill subject + the approved body (teaser + links) via `form_input`/`read_page`-discovered fields.
- **Before clicking Send**, re-read the composed email back to the user one last time (it goes to real people). Send only on the standing approval from Step 2.
- Capture confirmation that it sent.

### 3c. GroupMe — API

```bash
node .claude/skills/publish-lesson/groupme-post.js "…approved GroupMe text with links…"
```
HTTP 201 = posted. Token + group id come from `~/.config/genesis/publish.env`.

## Step 4 — confirm and record

Report what landed on each channel (resource links added, email sent, GroupMe message id). If any channel failed, say which and stop before retrying so nothing double-posts.

## Secrets & config

All non-public values live **outside the repo** in `~/.config/genesis/publish.env` (chmod 600), never committed:

```
GENESIS_PAGES_BASE=https://dpwhittaker.github.io/genesis
CHURCHCENTER_BASE=https://daystarchurch.churchcenter.com
CHURCHCENTER_GROUP=reading-the-bible-like-rabbi-jesus
GROUPME_GROUP_ID=110265443
GROUPME_TOKEN=          # from dev.groupme.com — secret, keep here only
```

The `GROUPME_TOKEN` is a secret; this skill lives in a **public** repo, so the token must stay in `~/.config` only.

## Guardrails

- **Approval gate is non-negotiable.** Never send email or post GroupMe without the user's explicit OK on the exact text (Step 2).
- **Idempotency.** If a run is re-invoked, check whether resources/email/GroupMe already went out before repeating — don't double-email the group.
- **Preconditions first, always.** No publishing a lesson whose handout still warns or that's missing a podcast.
- **Browser steps are member-authenticated.** They require the user signed into Church Center in the connected Chrome; if not signed in, stop and ask.
