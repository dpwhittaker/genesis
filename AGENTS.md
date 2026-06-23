# genesis — AGENTS.md

This is the orientation doc for any agent (you) working in this project.
Human-facing details — project title, one-sentence summary, and tags — live
in `README.md`, which is what the landing page reads. Keep README current.

## Bootstrap

This folder was just created via the landing page's "+" card. A
`ttyd@genesis.service` systemd unit serves a browser terminal at
`/term/genesis/` (long-lived tmux session, `claude --continue`). Browse
files at `/view/genesis/`.

## What to do first

1. Ask the user what they want to build here.
2. Update `README.md`: rewrite the H1 (card title), rewrite the first
   paragraph (card description), and set `tags: [...]` in the YAML
   frontmatter (card badges) — short tags like `Game`, `Tool`, `API`,
   `Library`, `Service`, plus status flags like `WIP` or `Stable`.
3. Start scaffolding.

## Audience & tone

**Everything published on this site is read by the class participants** —
this is study material handed directly to them, not a private leader's guide.
So do **not** publish "leader notes" that talk *about* the participants or
that read as manipulative or patronizing (e.g. "expect them to feel
threatened," "frame it so they don't resist"). If a note would be awkward to
read aloud to the people it describes, it does not belong on the site.

Instead, write any such guidance **to the class directly, with empathy and
grace** — acknowledge honestly that some of this material can feel
unsettling, meet that feeling with respect, and invite the reader in rather
than managing them. Genuinely leader-only logistics (timing, what to skip)
can stay, but phrased as a warm note to everyone.
