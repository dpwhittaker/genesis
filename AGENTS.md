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

**Class time.** The group meets at **10am**. If any material refers to the
time of day, keep it generic — use **"today"**, never "tonight," "this
morning," or "this evening." The same handout may be read before, during, or
after the meeting, and on any day, so a fixed time of day will often be wrong.

## Sourcing quotations & translations

This is a **public** repo. Every quoted text (Scripture, ANE myths, rabbinic
or patristic sources) must rest on a translation we are licensed to publish.

**Always search for an existing, permissively licensed translation first —
only translate from scratch as a last resort.** Producing your own rendering
from the original language is a real option (we did it for the *Atrahasis*
Akkadian when the only modern translations were all-rights-reserved), but it
is slow and easy to get wrong. A vetted scholarly translation under an open
license is almost always the better choice. Look in this order:

1. **Public domain** — pre-1929 editions, ancient originals, JPS 1917 for the
   Tanakh, KJV/ASV/WEB, classic translations (King's *Enuma Elish*, Breasted,
   Charles Taylor / Singer for Pirkei Avot). No restriction beyond honesty.
2. **Permissive open licenses** — CC BY (e.g. Sefaria's *Mishnah Yomit* by
   Joshua Kulp). Free to use with attribution.
3. **"Copyleft" / restricted-but-open licenses** — CC BY-SA, **CC BY-NC-SA**
   (e.g. the eBL Akkadian corpus, ETCSL Sumerian texts). These are fine here:
   the site is **non-commercial** study material, so the NC clause is no
   obstacle, and we attribute and (for SA) share alike. Prefer these over a
   from-scratch translation.
4. **Translate it yourself** — only when 1–3 turn up nothing usable, or the
   only available translations are fully copyrighted. When you do, work from a
   public-domain or openly-licensed *original-language* edition, say plainly
   that it is "an original working translation," and cite the source edition.

Whatever the source, **record provenance and license on the text's own page**
(translator, edition, license, link) — see the `texts/` files in session 1
and 2 for the pattern. When in doubt about a license, surface it to the user
rather than guessing.
