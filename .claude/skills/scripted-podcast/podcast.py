#!/usr/bin/env python3
"""Lint a two-voice podcast script and voice it with ElevenLabs.

    podcast.py check  SCRIPT              lint, stats, chunk plan, cost (no API calls)
    podcast.py render SCRIPT [--yes]      voice new/changed chunks, assemble the output
    podcast.py render SCRIPT --only N     voice just chunk N (for auditioning a retake)
    podcast.py voices [SEARCH]            voices on the account (needs voices_read)
    podcast.py quota                      credits used and left (needs user_read)

The script format is described in SKILL.md next to this file. Every chunk is one
API request, cached by a hash of exactly what was sent, so editing one chunk
re-bills only that chunk. Nothing is sent without --yes.

The API key comes from $ELEVENLABS_API_KEY or ~/.config/genesis/elevenlabs.env.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

API = "https://api.elevenlabs.io"
KEY_FILE = Path.home() / ".config/genesis/elevenlabs.env"
CACHE = Path.home() / ".cache/scripted-podcast"

# Text to Dialogue: keep each request's text at or under 2,000 characters
# ("longer requests may end early or return a validation error"), at most 10
# voices. Shorter chunks are also cheaper to retake.
HARD_MAX = 2000
SOFT_MAX = 1800
WPM = 150            # spoken pace used for the duration estimate
GAP = 0.35           # seconds of silence between chunks

DEFAULTS = {
    "model": "eleven_v4",   # the API's default is still eleven_v3; v4 is the recommended one
    "stability": 0.5,       # lower = broader emotional range; higher = steadier, flatter
    "continuity": False,    # send previous_text/future_text (100 chars) across chunk seams
    "seed": 1,
    "output_format": "mp3_44100_128",  # 192k needs Creator tier, 44.1 kHz PCM/WAV needs Pro
    "bitrate": "64k",
    "credit": "Voiced with ElevenLabs (elevenlabs.io)",
}

# Tags are free-text direction on v3/v4, not an enum: [curious], [laughs],
# [quiet, measured]. Things a listener can't hear are the failure mode: the
# model may read them aloud or invent a sound effect for them.
NOT_A_SOUND = re.compile(
    r"\b(stand|standing|sit|sitting|grin|grinning|smil|nod|pacing|walk|lean|"
    r"shrug|wink|wince|frown|gestur|looks?|music|points?)", re.I)
SOUND_EFFECTS = re.compile(r"\b(applause|clapping|gunshot|explosion|door|footsteps|thunder|rain)\b", re.I)

DIACRITICS = re.compile(r"[ḥḤēĒṣṢšŠʿʾāĀīĪūŪôâêîûṭṬḏḇḡ]")
REFERENCE = re.compile(r"\b\d+:\d+")
TURN = re.compile(r"^([A-Z][A-Z0-9_]*):\s*(.*)$")
TAG = re.compile(r"\[([^\]]+)\]")
COMMENT = re.compile(r"<!--(.*?)-->", re.S)


class ScriptError(Exception):
    pass


# ---------------------------------------------------------------- parsing

def parse(path):
    raw = Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise ScriptError("script must start with a --- YAML front matter block ---")
    meta = {**DEFAULTS, **(yaml.safe_load(m.group(1)) or {})}
    speakers = meta.get("speakers") or {}
    if not speakers:
        raise ScriptError("front matter needs `speakers:` mapping each label to a voice")
    for label, spec in speakers.items():
        if not isinstance(spec, dict) or not spec.get("voice"):
            raise ScriptError(f"speaker {label}: needs `voice: <voice_id>`")
    if not meta.get("output"):
        raise ScriptError("front matter needs `output:` (file name, relative to the script)")

    body = m.group(2)
    body_line0 = raw[: m.start(2)].count("\n") + 1

    # Comments are notes, never voiced, and may span lines: blank them out but
    # keep the line numbers. A `<!-- take: N -->` comment re-rolls its chunk.
    take_marks = [(mo.start(), int(t.group(1))) for mo in COMMENT.finditer(body)
                  if (t := re.search(r"\btake:\s*(\d+)", mo.group(1)))]
    stripped = COMMENT.sub(lambda mo: "\n" * mo.group(1).count("\n"), body)
    breaks_at = [mo.start() for mo in re.finditer(r"(?m)^---\s*$", body)]

    chunks = [{"turns": [], "take": 0, "line": body_line0}]
    turn = None
    blank_since_turn = False

    for i, line in enumerate(stripped.split("\n")):
        lineno = body_line0 + i
        s = line.strip()
        if re.fullmatch(r"---", s):
            chunks.append({"turns": [], "take": 0, "line": lineno})
            turn = None
            continue
        if not s:
            blank_since_turn = turn is not None
            continue
        if s.startswith("#"):
            turn = None
            continue
        mo = TURN.match(s)
        if mo:
            label, text = mo.groups()
            if label not in speakers:
                raise ScriptError(f"line {lineno}: unknown speaker {label} (front matter has {', '.join(speakers)})")
            turn = {"speaker": label, "text": text, "line": lineno}
            chunks[-1]["turns"].append(turn)
            blank_since_turn = False
            continue
        if turn is None or blank_since_turn:
            raise ScriptError(f"line {lineno}: text outside a turn — start it with SPEAKER: ({s[:40]!r})")
        turn["text"] += " " + s

    for pos, take in take_marks:
        idx = sum(1 for b in breaks_at if b < pos)  # chunk = breaks before it
        chunks[idx]["take"] = take

    chunks = [c for c in chunks if c["turns"]]
    if not chunks:
        raise ScriptError("no turns found")
    for c in chunks:
        for t in c["turns"]:
            t["voiced"] = clean(t["text"])
    return meta, chunks


def clean(text):
    """What is actually sent: markdown emphasis dropped, whitespace collapsed."""
    text = re.sub(r"(\*\*|\*|__)(.+?)\1", r"\2", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------- linting

def words(text):
    return len(TAG.sub(" ", text).split())


def lint(meta, chunks):
    notes = []
    tag_counts = {}
    for ci, c in enumerate(chunks, 1):
        chars = sum(len(t["voiced"]) for t in c["turns"])
        if chars > HARD_MAX:
            notes.append(("ERROR", c["line"], f"chunk {ci} is {chars} chars; a request may carry {HARD_MAX}. Add a --- break."))
        elif chars > SOFT_MAX:
            notes.append(("note", c["line"], f"chunk {ci} is {chars} chars, close to the {HARD_MAX} limit — a small edit could push it over"))
        if len({t["speaker"] for t in c["turns"]}) > 10:
            notes.append(("ERROR", c["line"], f"chunk {ci} has more than 10 voices"))
        for t in c["turns"]:
            v, ln = t["voiced"], t["line"]
            for tag in TAG.findall(v):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                if NOT_A_SOUND.search(tag):
                    notes.append(("warn", ln, f"[{tag}] can't be heard — describe the voice instead ([warm, amused])"))
                elif SOUND_EFFECTS.search(tag):
                    notes.append(("note", ln, f"[{tag}] will be rendered as a sound effect"))
            bare = TAG.sub(" ", v)
            if not bare.strip():
                notes.append(("warn", ln, "turn has tags but no words"))
            if "LORD" in bare:
                notes.append(("warn", ln, "LORD in capitals reads as shouting — write 'the Lord'"))
            caps = [w for w in re.findall(r"\b[A-Z]{2,}\b", bare) if w not in {"LORD", "OK", "TV", "I"}]
            if caps:
                notes.append(("note", ln, f"CAPS read as emphasis: {', '.join(caps)}"))
            if REFERENCE.search(bare):
                notes.append(("warn", ln, f"write references as words ('Genesis six, verse six'): {REFERENCE.search(bare).group()}"))
            elif re.search(r"\d", bare):
                notes.append(("note", ln, "digits — numbers usually read better spelled out"))
            if DIACRITICS.search(bare):
                notes.append(("warn", ln, "transliteration diacritics — respell for the ear (yetzer, khen)"))
            if re.search(r"[()]|\b(BCE|CE|e\.g\.|i\.e\.|cf\.|etc\.|vv?\.)", bare):
                notes.append(("warn", ln, "parentheses or abbreviations don't survive being spoken"))
            if re.search(r"<break|<phoneme", bare):
                notes.append(("warn", ln, "SSML tags don't work on v3/v4 — use [pause] or punctuation"))
            if len(bare) > 450:
                notes.append(("note", ln, f"long turn ({len(bare)} chars) — a podcast turn rarely runs past three sentences"))
            if len(TAG.findall(v)) > 2:
                notes.append(("note", ln, "more than two tags in one turn — tags work best sparingly"))
    return notes, tag_counts


def stats(meta, chunks):
    per = {}
    total_words = total_chars = 0
    for c in chunks:
        for t in c["turns"]:
            w, ch = words(t["voiced"]), len(t["voiced"])
            p = per.setdefault(t["speaker"], [0, 0])
            p[0] += 1
            p[1] += w
            total_words += w
            total_chars += ch
    return per, total_words, total_chars


# ---------------------------------------------------------------- API

def api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key and KEY_FILE.exists():
        for line in KEY_FILE.read_text().splitlines():
            if line.startswith("ELEVENLABS_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit(f"no API key: set ELEVENLABS_API_KEY or put ELEVENLABS_API_KEY=... in {KEY_FILE}")
    return key


def call(method, path, body=None, timeout=600):
    req = urllib.request.Request(
        API + path, method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"xi-api-key": api_key(), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        try:
            detail = json.loads(detail).get("detail", detail)
        except ValueError:
            pass
        sys.exit(f"ElevenLabs {method} {path.split('?')[0]} → HTTP {e.code}: {detail}")


def seam(text, tail):
    """Up to 100 characters of a neighbouring chunk, cut at a word boundary."""
    text = TAG.sub("", text).strip()
    if len(text) <= 100:
        return text
    cut = text[-100:] if tail else text[:100]
    return cut.split(" ", 1)[1] if tail else cut.rsplit(" ", 1)[0]


def request_for(meta, chunks, i):
    chunk = chunks[i]
    speakers = meta["speakers"]
    body = {
        "inputs": [{"text": t["voiced"], "voice_id": speakers[t["speaker"]]["voice"]} for t in chunk["turns"]],
        "model_id": meta["model"],
        "settings": {"stability": meta["stability"],
                     **({"similarity": meta["similarity"]} if "similarity" in meta else {})},
        "seed": int(meta["seed"]) + int(chunk["take"]),
    }
    if meta.get("language"):
        body["language_code"] = meta["language"]
    if meta.get("continuity"):
        # Ties each chunk's cache entry to its neighbours' edges, so an edit at
        # a seam re-voices both sides of it.
        if i > 0:
            body["previous_text"] = seam(chunks[i - 1]["turns"][-1]["voiced"], tail=True)
        if i + 1 < len(chunks):
            body["future_text"] = seam(chunks[i + 1]["turns"][0]["voiced"], tail=False)
    return body


def cache_path(meta, body):
    h = hashlib.sha256(json.dumps([body, meta["output_format"]], sort_keys=True).encode()).hexdigest()[:20]
    return CACHE / f"{h}.mp3"


def voice_chunk(meta, body, dest):
    q = urllib.parse.urlencode({"output_format": meta["output_format"]})
    audio, headers = call("POST", f"/v1/text-to-dialogue?{q}", body)
    if not audio or audio[:1] == b"{":
        sys.exit(f"unexpected response (not audio): {audio[:300]!r}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(audio)
    tmp.replace(dest)
    rid, cost = headers.get("request-id", "?"), headers.get("character-cost", "?")
    chars = sum(len(x["text"]) for x in body["inputs"])
    dest.with_suffix(".json").write_text(json.dumps(
        {"request_id": rid, "character_cost": cost, "characters": chars, "body": body}, indent=1))
    return rid, cost


# ---------------------------------------------------------------- audio

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def assemble(parts, out, bitrate, title, credit):
    """Concatenate chunk mp3s with short gaps, normalise to podcast loudness,
    and encode as mono AAC — the same 64k mono / faststart as the NotebookLM
    episodes, so Pages' 1 GB budget holds."""
    with tempfile.TemporaryDirectory() as td:
        inputs, labels = [], []
        for i, p in enumerate(parts):
            inputs += ["-i", str(p)]
            labels.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=mono,apad=pad_dur={GAP}[a{i}]")
        concat = "".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[cat]"
        graph = ";".join(labels + [concat, "[cat]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100[out]"])
        tmp = Path(td) / "out.m4a"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs,
                        "-filter_complex", graph, "-map", "[out]", "-c:a", "aac", "-b:a", bitrate,
                        "-metadata", f"title={title}", "-metadata", f"comment={credit}",
                        "-ac", "1", "-ar", "44100", "-movflags", "+faststart", str(tmp)], check=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(tmp, out)
        out.chmod(0o644)


# ---------------------------------------------------------------- commands

def fmt_min(sec):
    return f"{int(sec // 60)}:{int(round(sec % 60)):02d}"


def cmd_check(args):
    meta, chunks = parse(args.script)
    notes, tags = lint(meta, chunks)
    per, total_words, total_chars = stats(meta, chunks)
    print(f"{Path(args.script).name}: {meta.get('title', '')}")
    print(f"  model {meta['model']}  stability {meta['stability']}  seed {meta['seed']}  → {meta['output']}")
    for label, (n, w) in per.items():
        spec = meta["speakers"][label]
        share = 100 * w / total_words if total_words else 0
        print(f"  {label:<9} {spec.get('name', ''):<10} {n:>3} turns  {w:>5} words  {share:4.0f}%")
    est = total_words / WPM * 60
    tagged = sum(tags.values())
    print(f"  total     {total_words} words, {total_chars} billed characters (tags included), ~{fmt_min(est)} at {WPM} wpm")
    print(f"  tags      {tagged} ({100 * tagged / max(1, total_words):.1f} per 100 words): "
          + ", ".join(f"{k}×{v}" if v > 1 else k for k, v in sorted(tags.items(), key=lambda kv: -kv[1])))
    print("  chunks")
    cached_chars = 0
    for i, c in enumerate(chunks, 1):
        body = request_for(meta, chunks, i - 1)
        chars = sum(len(t["voiced"]) for t in c["turns"])
        hit = cache_path(meta, body).exists()
        cached_chars += chars if hit else 0
        take = f" take {c['take']}" if c["take"] else ""
        print(f"    {i:>2}. line {c['line']:>4}  {len(c['turns']):>3} turns  {chars:>5} chars{take}  {'cached' if hit else 'to voice'}")
    print(f"  cost      {total_chars - cached_chars} characters to voice now ({cached_chars} cached)")
    if notes:
        print("  notes")
        for level, ln, msg in notes:
            print(f"    {level:<5} line {ln:>4}: {msg}")
    return 1 if any(n[0] == "ERROR" for n in notes) else 0


def cmd_render(args):
    meta, chunks = parse(args.script)
    notes, _ = lint(meta, chunks)
    errors = [n for n in notes if n[0] == "ERROR"]
    if errors:
        for _, ln, msg in errors:
            print(f"ERROR line {ln}: {msg}")
        return 1
    script = Path(args.script).resolve()
    out = script.parent / meta["output"]
    which = range(len(chunks)) if args.only is None else [args.only - 1]
    if args.only is not None and not 0 <= args.only - 1 < len(chunks):
        sys.exit(f"--only {args.only}: there are {len(chunks)} chunks")

    plan = []
    for i in which:
        body = request_for(meta, chunks, i)
        p = cache_path(meta, body)
        plan.append((i, body, p, p.exists() and not args.force))
    todo = [(i, b, p) for i, b, p, hit in plan if not hit]
    chars = sum(len(x["text"]) for _, b, _ in todo for x in b["inputs"])
    if todo and not args.yes:
        print(f"{len(todo)} chunk(s), {chars} characters to voice with {meta['model']}. Re-run with --yes to send.")
        return 2

    for i, body, p in todo:
        n = sum(len(x["text"]) for x in body["inputs"])
        print(f"  voicing chunk {i + 1} ({n} chars)…", flush=True)
        rid, cost = voice_chunk(meta, body, p)
        print(f"    {fmt_min(duration(p))}  request {rid}  cost {cost}")

    if args.only is not None:
        p = plan[0][2]
        preview = script.parent / f"{Path(meta['output']).stem}.chunk{args.only}.mp3"
        print(f"chunk {args.only}: {p}  ({fmt_min(duration(p))})")
        if args.copy:
            shutil.copy(p, preview)
            print(f"copied to {preview}")
        return 0

    assemble([p for _, _, p, _ in plan], out, meta["bitrate"], meta.get("title", out.stem), meta["credit"])
    print(f"wrote {out}  {fmt_min(duration(out))}  {out.stat().st_size / 1e6:.1f} MB")
    return 0


def cmd_voices(args):
    q = {"page_size": 100}
    if args.search:
        q["search"] = args.search
    data, _ = call("GET", "/v2/voices?" + urllib.parse.urlencode(q))
    for v in json.loads(data).get("voices", []):
        labels = v.get("labels") or {}
        desc = ", ".join(str(labels[k]) for k in ("gender", "age", "accent", "descriptive", "use_case") if labels.get(k))
        print(f"{v['voice_id']}  {v['name']:<28} {v.get('category', ''):<12} {desc}")
    return 0


def cmd_quota(args):
    data, _ = call("GET", "/v1/user/subscription")
    s = json.loads(data)
    used, limit = s.get("character_count", 0), s.get("character_limit", 0)
    print(f"tier {s.get('tier')}: {used} of {limit} credits used, {limit - used} left")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("script")
    r = sub.add_parser("render")
    r.add_argument("script")
    r.add_argument("--yes", action="store_true", help="actually send uncached chunks (costs credits)")
    r.add_argument("--only", type=int, metavar="N", help="voice only chunk N; don't assemble")
    r.add_argument("--copy", action="store_true", help="with --only: copy the chunk next to the script")
    r.add_argument("--force", action="store_true", help="ignore the cache and re-voice")
    v = sub.add_parser("voices")
    v.add_argument("search", nargs="?")
    sub.add_parser("quota")
    args = ap.parse_args()
    try:
        return {"check": cmd_check, "render": cmd_render, "voices": cmd_voices, "quota": cmd_quota}[args.cmd](args)
    except ScriptError as e:
        print(f"script error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
