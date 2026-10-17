#!/usr/bin/env python3
"""Lint a two-voice podcast script and voice it with ElevenLabs or Fish Audio.

    podcast.py check  SCRIPT              lint, stats, chunk plan, cost (no API calls)
    podcast.py render SCRIPT [--yes]      voice new/changed chunks, assemble the output
    podcast.py render SCRIPT --only N     voice just chunk N (for auditioning a retake)
    podcast.py verify SCRIPT [AUDIO]      transcribe the result locally and diff it against the script
    podcast.py voices [--engine fish] [SEARCH]   voices on the account / in Fish's library
    podcast.py quota  [--engine fish]     credits used and left

The front matter's `engine:` picks the service: `elevenlabs` (the default; Text
to Dialogue, eleven_v4) or `fish` (Fish Audio's /v1/tts with the `drama-3`
model: <|speaker:N|> turns, a reference_id per speaker, free-text [directions],
`speed:` as prosody.speed, and `max_pause:` seconds as a cap on every pause,
applied when the chunks are assembled).

The script format is described in SKILL.md next to this file. `---` lines cut
the script into sections; each section is split at turn boundaries into chunks
of at most the engine's soft_max characters. Every chunk is one API request, cached by a hash
of exactly what was sent, so editing a line re-bills only its chunk. Nothing is
sent without --yes.

`render --transport ws` and `verify` need packages the system python lacks; run
them under `~/.local/bin/uv run --no-project --with websockets|faster-whisper
--with pyyaml python podcast.py …`.

API keys come from $ELEVENLABS_API_KEY or ~/.config/genesis/elevenlabs.env, and
$FISH_API_KEY or ~/.config/genesis/fishaudio.env.
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

API = "https://api.elevenlabs.io"
KEY_FILE = Path.home() / ".config/genesis/elevenlabs.env"
FISH_API = "https://api.fish.audio"
FISH_KEY_FILE = Path.home() / ".config/genesis/fishaudio.env"
CACHE = Path.home() / ".cache/scripted-podcast"

WPM = 150            # spoken pace used for the duration estimate
GAP = 0.35           # seconds of silence between chunks
STITCH_TTL = 2 * 3600 - 600  # request ids can be stitched to for 2 hours; keep a margin

DEFAULTS = {"bitrate": "64k"}
ENGINES = {
    # Text to Dialogue: keep each request's text at or under 2,000 characters
    # ("longer requests may end early or return a validation error"), at most 10
    # voices. Shorter chunks are also cheaper to retake.
    "elevenlabs": {
        "model": "eleven_v4",   # the API's default is still eleven_v3; v4 is the recommended one
        "stability": 0.5,       # lower = broader emotional range; higher = steadier, flatter
        "stitch": True,         # condition each chunk on its neighbours (see context_for)
        "seed": 1,
        "output_format": "mp3_44100_128",  # 192k needs Creator tier, 44.1 kHz PCM/WAV needs Pro
        "credit": "Voiced with ElevenLabs (elevenlabs.io)",
        "soft_max": 1800, "hard_max": 2000, "max_voices": 10,
    },
    # Fish states no length limit: the service splits text into 100-300 character
    # pieces itself and conditions each on the audio before it. ~3,000 characters
    # (about two minutes) keeps seams few and a retake cheap. No seed, no stitching.
    "fish": {
        "model": "drama-3",
        "speed": 1.0,           # prosody.speed, 0.5-2.0; Drama 3 honours it
        "max_pause": None,      # seconds; every longer pause is cut down to this when assembling
        "stitch": False,
        "output_format": "mp3-128",
        "credit": "Voiced with Fish Audio (fish.audio)",
        "soft_max": 3000, "hard_max": 6000, "max_voices": 16,
    },
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
    user = yaml.safe_load(m.group(1)) or {}
    engine = user.get("engine", "elevenlabs")
    if engine not in ENGINES:
        raise ScriptError(f"engine: {engine!r} — use one of {', '.join(ENGINES)}")
    meta = {"engine": engine, **DEFAULTS, **ENGINES[engine], **user}
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
    takes = [(body_line0 + body[: mo.start()].count("\n"), int(t.group(1)))
             for mo in COMMENT.finditer(body) if (t := re.search(r"\btake:\s*(\d+)", mo.group(1)))]
    stripped = COMMENT.sub(lambda mo: "\n" * mo.group(1).count("\n"), body)

    sections = [[]]
    turn = None
    blank_since_turn = False
    for i, line in enumerate(stripped.split("\n")):
        lineno = body_line0 + i
        s = line.strip()
        if s == "---":
            sections.append([])
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
            sections[-1].append(turn)
            blank_since_turn = False
            continue
        if turn is None or blank_since_turn:
            raise ScriptError(f"line {lineno}: text outside a turn — start it with SPEAKER: ({s[:40]!r})")
        turn["text"] += " " + s

    chunks = []
    for si, turns in enumerate(t for t in sections if t):
        for t in turns:
            t["voiced"] = clean(t["text"])
        for part in split_section(turns, meta["soft_max"]):
            chunks.append({"turns": part, "take": 0, "line": part[0]["line"], "section": si + 1})
    if not chunks:
        raise ScriptError("no turns found")
    for line, take in takes:
        # the last chunk starting at or before the mark (else the first one)
        mine = [c for c in chunks if c["line"] <= line] or chunks[:1]
        mine[-1]["take"] = take
    return meta, chunks


def split_section(turns, soft_max):
    """Cut one section into the fewest chunks of <= soft_max characters, at the
    turn boundaries nearest to equal shares, so no chunk is a stub."""
    sizes = [len(t["voiced"]) for t in turns]
    total = sum(sizes)
    cum = [sum(sizes[: j + 1]) for j in range(len(sizes))]
    n = max(1, math.ceil(total / soft_max))
    while True:
        cuts = sorted({min(range(len(turns) - 1), key=lambda j: abs(cum[j] - k * total / n))
                       for k in range(1, n)}) if len(turns) > 1 else []
        parts, start = [], 0
        for j in cuts + [len(turns) - 1]:
            parts.append(turns[start: j + 1])
            start = j + 1
        parts = [x for x in parts if x]
        if all(sum(len(t["voiced"]) for t in x) <= soft_max for x in parts) or n >= len(turns):
            return parts
        n += 1


def clean(text):
    """What is actually sent: markdown emphasis dropped, whitespace collapsed."""
    text = re.sub(r"(\*\*|\*|__)(.+?)\1", r"\2", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def fish_text(text):
    """What Fish is sent: *stressed* words become <emphasis>…</emphasis> (one of
    Drama 3's paired tags), everything else as clean() leaves it."""
    text = re.sub(r"(\*\*|\*|__)(.+?)\1", r"<emphasis>\2</emphasis>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------- linting

def words(text):
    return len(TAG.sub(" ", text).split())


def lint(meta, chunks):
    notes = []
    tag_counts = {}
    eleven = meta["engine"] == "elevenlabs"
    if len(meta["speakers"]) > meta["max_voices"]:
        notes.append(("ERROR", 1, f"{len(meta['speakers'])} speakers; {meta['engine']} takes {meta['max_voices']}"))
    for ci, c in enumerate(chunks, 1):
        chars = sum(len(t["voiced"]) for t in c["turns"])
        if chars > meta["hard_max"]:
            notes.append(("ERROR", c["line"], f"a single turn of {chars} chars; a request may carry {meta['hard_max']}. Split the turn."))
        for t in c["turns"]:
            v, ln = t["voiced"], t["line"]
            for tag in TAG.findall(v):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                # Fish reads directions as an actor would ("[smiling, finishing his
                # thought]"), so only ElevenLabs gets the can't-be-heard warning.
                if eleven and NOT_A_SOUND.search(tag):
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
            if eleven and len(TAG.findall(v)) > 2:
                notes.append(("note", ln, "more than two tags in one turn — tags work best sparingly"))
            if not eleven and len(bare.split()) > 6 and not TAG.match(v):
                notes.append(("note", ln, "no direction at the start of the turn — Fish reads best with one"))
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


def fish_key():
    key = os.environ.get("FISH_API_KEY")
    if not key and FISH_KEY_FILE.exists():
        for line in FISH_KEY_FILE.read_text().splitlines():
            if line.startswith("FISH_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit(f"no Fish Audio key: set FISH_API_KEY or put FISH_API_KEY=... in {FISH_KEY_FILE}")
    return key


def fish_call(method, path, body=None, headers=None, timeout=900, tries=3):
    """Fish Audio request; retries a 5xx ("under high load") or a dropped
    connection twice, with a pause, before giving up."""
    for attempt in range(1, tries + 1):
        req = urllib.request.Request(
            FISH_API + path, method=method, data=None if body is None else json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {fish_key()}", "Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            if e.code < 500 or attempt == tries:
                sys.exit(f"Fish Audio {method} {path.split('?')[0]} → HTTP {e.code}: {detail}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == tries:
                sys.exit(f"Fish Audio {method} {path.split('?')[0]} failed: {e}")
        print(f"    (Fish Audio busy or unreachable; retrying in {20 * attempt} s)", flush=True)
        time.sleep(20 * attempt)


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
    if meta["engine"] == "fish":
        # Every chunk carries every voice, so <|speaker:N|> means the same host
        # throughout. Keys starting with _ are for the cache key, not sent: Fish has
        # no seed, so a take is a fresh sample under a new key.
        labels = list(speakers)
        body = {
            "text": "\n".join(f"<|speaker:{labels.index(t['speaker'])}|>{fish_text(t['text'])}" for t in chunk["turns"]),
            "reference_id": [speakers[label]["voice"] for label in labels],
            "format": "mp3", "mp3_bitrate": 128,
            "_model": meta["model"], "_take": int(chunk["take"]),
        }
        if float(meta.get("speed") or 1) != 1:
            body["prosody"] = {"speed": float(meta["speed"])}
        for k in ("temperature", "top_p", "language"):
            if k in meta:
                body[k] = meta[k]
        return body
    body = {
        "inputs": [{"text": t["voiced"], "voice_id": speakers[t["speaker"]]["voice"]} for t in chunk["turns"]],
        "model_id": meta["model"],
        "settings": {"stability": meta["stability"],
                     **({"similarity": meta["similarity"]} if "similarity" in meta else {})},
        "seed": int(meta["seed"]) + int(chunk["take"]),
    }
    if meta.get("language"):
        body["language_code"] = meta["language"]
    return body


def body_chars(body):
    """Characters a request sends (and is billed for)."""
    return len(body["text"]) if "text" in body else sum(len(x["text"]) for x in body["inputs"])


def sidecar(path):
    j = path.with_suffix(".json")
    if not (path.exists() and j.exists()):
        return None
    d = json.loads(j.read_text())
    d.setdefault("created", path.stat().st_mtime)
    return d


def context_for(chunks, paths, i, pending):
    """Continuity for voicing chunk i, so its seams match its neighbours.

    Request stitching: the request ids of the takes before it
    (previous_request_ids, nearest last) and, when retaking a chunk
    mid-script, of the takes after it (next_request_ids, nearest first) —
    at most 3 each, only takes still on disk, under 2 hours old, and not
    about to be re-voiced (`pending`). Where there is no usable id on a
    side, 100 characters of that neighbour's text instead.

    Deliberately not part of the cache key: an edit re-voices its own chunk,
    stitched to whatever its neighbours currently are, and nothing else."""
    def fresh(k):
        if k in pending:
            return None
        d = sidecar(paths[k])
        if d and d.get("request_id") not in (None, "?") and time.time() - d["created"] < STITCH_TTL:
            return d["request_id"]
        return None

    ctx = {}
    prev = []
    for k in range(i - 1, max(-1, i - 4), -1):
        if not (rid := fresh(k)):
            break
        prev.insert(0, rid)
    if prev:
        ctx["previous_request_ids"] = prev
    elif i > 0:
        ctx["previous_text"] = seam(chunks[i - 1]["turns"][-1]["voiced"], tail=True)
    nxt = []
    for k in range(i + 1, min(len(chunks), i + 4)):
        if not (rid := fresh(k)):
            break
        nxt.append(rid)
    if nxt:
        ctx["next_request_ids"] = nxt
    elif i + 1 < len(chunks):
        ctx["future_text"] = seam(chunks[i + 1]["turns"][0]["voiced"], tail=False)
    return ctx


def describe(ctx):
    bits = []
    for key, label in (("previous_request_ids", "after"), ("next_request_ids", "before")):
        if key in ctx:
            bits.append(f"stitched {label} {len(ctx[key])} take(s)")
    for key, label in (("previous_text", "after"), ("future_text", "before")):
        if key in ctx:
            bits.append(f"{label} text")
    return ", ".join(bits) or "no neighbours"


def cache_path(meta, body):
    h = hashlib.sha256(json.dumps([body, meta["output_format"]], sort_keys=True).encode()).hexdigest()[:20]
    return CACHE / f"{h}.mp3"


def voice_chunk_fish(body, dest):
    send = {k: v for k, v in body.items() if not k.startswith("_")}
    audio, headers = fish_call("POST", "/v1/tts", send, headers={"model": body["_model"]})
    if not audio or audio[:1] == b"{":
        sys.exit(f"unexpected response (not audio): {audio[:300]!r}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(audio)
    tmp.replace(dest)
    rid = next((v for k, v in headers.items() if k.lower() in ("x-request-id", "request-id", "x-trace-id")), "?")
    dest.with_suffix(".json").write_text(json.dumps(
        {"request_id": rid, "characters": len(send["text"]), "created": time.time(),
         "headers": {k: v for k, v in headers.items() if k.lower().startswith("x-")}, "body": body}, indent=1))
    return rid, f"{len(send['text'])} chars"


def voice_chunk(meta, body, dest, ctx=None):
    if meta["engine"] == "fish":
        return voice_chunk_fish(body, dest)
    q = urllib.parse.urlencode({"output_format": meta["output_format"]})
    audio, headers = call("POST", f"/v1/text-to-dialogue?{q}", {**body, **(ctx or {})})
    if not audio or audio[:1] == b"{":
        sys.exit(f"unexpected response (not audio): {audio[:300]!r}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(audio)
    tmp.replace(dest)
    rid, cost = headers.get("request-id", "?"), headers.get("character-cost", "?")
    chars = sum(len(x["text"]) for x in body["inputs"])
    dest.with_suffix(".json").write_text(json.dumps(
        {"request_id": rid, "character_cost": cost, "characters": chars, "created": time.time(),
         "context": ctx or {}, "body": body}, indent=1))
    return rid, cost


def ws_request(meta, chunks):
    """The whole script as one Text to Dialogue WebSocket session: every turn in
    order, each starting a new turn, so there are no chunk seams (--- breaks
    are ignored) and no 2,000-character request limit."""
    speakers = meta["speakers"]
    turns = [t for c in chunks for t in c["turns"]]
    query = {"model_id": meta["model"], "output_format": meta["output_format"],
             "seed": int(meta["seed"]) + sum(int(c["take"]) for c in chunks)}
    if meta.get("language"):
        query["language_code"] = meta["language"]
    return {
        "transport": "ws",
        "flush_each_turn": True,
        "query": query,
        "voices": list(dict.fromkeys(speakers[t["speaker"]]["voice"] for t in turns)),
        "voice_settings": {"stability": meta["stability"]},
        # The trailing space tells the server the last word is complete; without
        # it the last word of each turn is held back and voiced on its own.
        "inputs": [{"text": t["voiced"] + " ", "voice_id": speakers[t["speaker"]]["voice"], "new_turn": True}
                   for t in turns],
    }


def voice_ws(req, dest):
    try:
        import websockets
    except ImportError:
        sys.exit("--transport ws needs the websockets package; run under\n"
                 "  ~/.local/bin/uv run --no-project --with websockets --with pyyaml python podcast.py …")
    import asyncio
    import base64

    url = "wss://api.elevenlabs.io/v1/text-to-dialogue/stream-input?" + urllib.parse.urlencode(req["query"])

    async def run():
        audio, turns_done, rid = bytearray(), 0, "?"
        async with websockets.connect(url, additional_headers={"xi-api-key": api_key()},
                                      max_size=None, open_timeout=30) as ws:
            rid = ws.response.headers.get("request-id", "?") if ws.response else "?"
            await ws.send(json.dumps({"voices": req["voices"], "voice_settings": req["voice_settings"]}))
            for item in req["inputs"]:
                await ws.send(json.dumps({"inputs": [item], "flush": True}))
            await ws.send(json.dumps({"close_socket": True}))
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("error"):
                    sys.exit(f"ElevenLabs WebSocket error: {msg}")
                if msg.get("audio"):
                    audio += base64.b64decode(msg["audio"])
                if msg.get("is_final_audio_for_turn"):
                    turns_done += 1
                if msg.get("is_final"):
                    break
        return bytes(audio), turns_done, rid

    audio, turns_done, rid = asyncio.run(run())
    if not audio:
        sys.exit("WebSocket session returned no audio")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.with_suffix(".part").write_bytes(audio)
    dest.with_suffix(".part").replace(dest)
    chars = sum(len(x["text"]) for x in req["inputs"])
    dest.with_suffix(".json").write_text(json.dumps(
        {"request_id": rid, "characters": chars, "turns_finalised": turns_done, "request": req}, indent=1))
    return rid, turns_done


# ---------------------------------------------------------------- audio

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def cap_pauses(src, dest, max_pause, threshold_db=40.0):
    """Write src to dest (WAV) with every pause longer than max_pause seconds cut
    down to max_pause, and the leading and trailing silence removed.

    A pause is a run of 10 ms frames quieter than threshold_db below the clip's
    peak. A long one keeps its first and last max_pause/2 seconds (so breaths and
    word tails survive), joined with a 10 ms crossfade. Shorter pauses are left
    alone, so the rhythm inside a sentence holds."""
    import numpy as np
    sr, frame = 44100, 441
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(pcm, np.float32)
    n = len(a) // frame
    rms = np.sqrt(np.mean(a[: n * frame].reshape(n, frame) ** 2, axis=1) + 1e-12)
    quiet = np.append(20 * np.log10(rms / max(rms.max(), 1e-9)) < -threshold_db, False)
    loud = np.flatnonzero(~quiet[:-1])
    if not len(loud):
        a.tofile(dest)
        return
    first, last = loud[0] * frame, (loud[-1] + 1) * frame
    edge, half, fade = int(0.05 * sr), int(max_pause * sr / 2), int(0.01 * sr)
    pieces, pos, start = [], max(0, first - edge), None
    for i, q in enumerate(quiet):
        if q and start is None:
            start = i
        elif not q and start is not None:
            s, e = start * frame, i * frame
            if first < s and e < last and (e - s) > max_pause * sr:
                pieces.append(a[pos: s + half])
                pos = e - half
            start = None
    pieces.append(a[pos: min(len(a), last + edge)])
    out = pieces[0]
    ramp = np.linspace(0, 1, fade, dtype=np.float32)
    for seg in pieces[1:]:
        out = np.concatenate([out[:-fade], out[-fade:] * (1 - ramp) + seg[:fade] * ramp, seg[fade:]])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s16le", str(dest)], input=out.astype(np.float32).tobytes(), check=True)


def assemble(parts, out, bitrate, title, credit, max_pause=None):
    """Concatenate chunk mp3s with short gaps, normalise to podcast loudness,
    and encode as mono AAC — the same 64k mono / faststart as the NotebookLM
    episodes, so Pages' 1 GB budget holds. With max_pause, each chunk's pauses
    are capped first (cap_pauses) and the chunks joined with max_pause of
    silence, so a seam sounds like any other turn."""
    with tempfile.TemporaryDirectory() as td:
        if max_pause:
            capped = []
            for i, p in enumerate(parts):
                capped.append(Path(td) / f"{i}.wav")
                cap_pauses(p, capped[-1], float(max_pause))
            parts = capped
        gap = float(max_pause) if max_pause else GAP
        inputs, labels = [], []
        for i, p in enumerate(parts):
            inputs += ["-i", str(p)]
            labels.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=mono,apad=pad_dur={gap}[a{i}]")
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
    if meta["engine"] == "fish":
        pause = f"{meta['max_pause']} s" if meta.get("max_pause") else "as voiced"
        print(f"  engine fish  model {meta['model']}  speed {meta.get('speed', 1)}  max pause {pause}  → {meta['output']}")
    else:
        print(f"  model {meta['model']}  stability {meta['stability']}  seed {meta['seed']}  → {meta['output']}")
    for label, (n, w) in per.items():
        spec = meta["speakers"][label]
        share = 100 * w / total_words if total_words else 0
        print(f"  {label:<9} {spec.get('name', ''):<10} {n:>3} turns  {w:>5} words  {share:4.0f}%")
    est = total_words / WPM * 60
    tagged = sum(tags.values())
    bodies = [request_for(meta, chunks, i) for i in range(len(chunks))]
    sent = sum(body_chars(b) for b in bodies)
    print(f"  total     {total_words} words, {sent} characters sent (tags included), ~{fmt_min(est)} at {WPM} wpm")
    print(f"  tags      {tagged} ({100 * tagged / max(1, total_words):.1f} per 100 words): "
          + ", ".join(f"{k}×{v}" if v > 1 else k for k, v in sorted(tags.items(), key=lambda kv: -kv[1])))
    print("  chunks")
    cached_chars = 0
    for i, c in enumerate(chunks, 1):
        body = bodies[i - 1]
        chars = body_chars(body)
        hit = cache_path(meta, body).exists()
        cached_chars += chars if hit else 0
        take = f" take {c['take']}" if c["take"] else ""
        print(f"    {i:>2}. §{c['section']:<2} line {c['line']:>4}  {len(c['turns']):>3} turns  {chars:>5} chars{take}  {'cached' if hit else 'to voice'}")
    print(f"  cost      {sent - cached_chars} characters to voice now ({cached_chars} cached)")
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
    if args.model:
        meta["model"] = args.model
    out = Path(args.out).resolve() if args.out else script.parent / meta["output"]
    title = meta.get("title", out.stem)

    if args.transport == "ws":
        if meta["engine"] != "elevenlabs":
            sys.exit("--transport ws is ElevenLabs only")
        if args.only is not None:
            sys.exit("--only applies to chunks; a WebSocket render is one session")
        req = ws_request(meta, chunks)
        p = CACHE / (hashlib.sha256(json.dumps(req, sort_keys=True).encode()).hexdigest()[:20] + ".mp3")
        if not p.exists() or args.force:
            chars = sum(len(x["text"]) for x in req["inputs"])
            if not args.yes:
                print(f"1 WebSocket session, {chars} characters to voice with {meta['model']}. Re-run with --yes to send.")
                return 2
            print(f"  voicing {len(req['inputs'])} turns over the WebSocket ({chars} chars)…", flush=True)
            rid, turns_done = voice_ws(req, p)
            print(f"    {fmt_min(duration(p))}  request {rid}  {turns_done} turns finalised")
        assemble([p], out, meta["bitrate"], title, meta["credit"])
        print(f"wrote {out}  {fmt_min(duration(out))}  {out.stat().st_size / 1e6:.1f} MB")
        return 0

    which = range(len(chunks)) if args.only is None else [args.only - 1]
    if args.only is not None and not 0 <= args.only - 1 < len(chunks):
        sys.exit(f"--only {args.only}: there are {len(chunks)} chunks")

    paths = [cache_path(meta, request_for(meta, chunks, i)) for i in range(len(chunks))]
    plan = []
    for i in which:
        body = request_for(meta, chunks, i)
        plan.append((i, body, paths[i], paths[i].exists() and not args.force))
    todo = [(i, b, p) for i, b, p, hit in plan if not hit]
    pending = {i for i, _, _ in todo}
    chars = sum(body_chars(b) for _, b, _ in todo)
    if todo and not args.yes:
        print(f"{len(todo)} chunk(s), {chars} characters to voice with {meta['model']}. Re-run with --yes to send.")
        return 2

    for i, body, p in todo:  # in script order, so each can stitch to the one before
        n = body_chars(body)
        ctx = context_for(chunks, paths, i, pending) if meta.get("stitch") else {}
        print(f"  voicing chunk {i + 1} ({n} chars; {describe(ctx)})…", flush=True)
        rid, cost = voice_chunk(meta, body, p, ctx)
        pending.discard(i)
        got, want = duration(p), sum(words(t["voiced"]) for t in chunks[i]["turns"]) / WPM * 60
        flag = "  ← much shorter than its text: truncated? retake it" if got < 0.6 * want else ""
        print(f"    {fmt_min(got)}  request {rid}  cost {cost}{flag}")

    if args.only is not None:
        p = plan[0][2]
        preview = script.parent / f"{Path(meta['output']).stem}.chunk{args.only}.mp3"
        print(f"chunk {args.only}: {p}  ({fmt_min(duration(p))})")
        if args.copy:
            if meta.get("max_pause"):
                with tempfile.TemporaryDirectory() as td:
                    cap_pauses(p, Path(td) / "c.wav", float(meta["max_pause"]))
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(Path(td) / "c.wav"),
                                    "-b:a", "128k", str(preview)], check=True)
            else:
                shutil.copy(p, preview)
            print(f"copied to {preview}")
        return 0

    assemble([p for _, _, p, _ in plan], out, meta["bitrate"], title, meta["credit"], meta.get("max_pause"))
    print(f"wrote {out}  {fmt_min(duration(out))}  {out.stat().st_size / 1e6:.1f} MB")
    return 0


WHISPER = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
NUMBERS = {w: n for n, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen".split())}
NUMBERS.update({w: 10 * (n + 2) for n, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())})
ORDINALS = {w: str(n + 1) for n, w in enumerate("first second third fourth fifth sixth seventh eighth ninth tenth".split())}


def norm_words(text):
    """Lower-case words for comparison; ordinals as digits on both sides, since
    Whisper writes "First Samuel" as "1 Samuel"."""
    out = re.findall(r"[a-z0-9']+", TAG.sub(" ", text).lower().replace("’", "'"))
    return [ORDINALS.get(w, w) for w in out]


def as_number(tokens):
    """'two hundred and fifty' -> 250; ['250'] -> 250; anything else -> None."""
    if len(tokens) == 1 and tokens[0].isdigit():
        return int(tokens[0])
    total = cur = 0
    for w in tokens:
        if w in NUMBERS:
            cur += NUMBERS[w]
        elif w == "hundred":
            cur = max(cur, 1) * 100
        elif w == "thousand":
            total, cur = total + max(cur, 1) * 1000, 0
        elif w == "and" and (cur or total):
            continue
        elif w.isdigit():
            cur += int(w)
        else:
            return None
    return total + cur if tokens else None


def cmd_verify(args):
    try:
        import numpy as np
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("verify needs faster-whisper; run under\n"
                 "  ~/.local/bin/uv run --no-project --with faster-whisper --with pyyaml python podcast.py verify …")
    import difflib

    meta, chunks = parse(args.script)
    script = Path(args.script).resolve()
    audio_path = Path(args.audio).resolve() if args.audio else script.parent / meta["output"]
    want = [(w, t["line"], ci) for ci, c in enumerate(chunks, 1) for t in c["turns"] for w in norm_words(t["voiced"])]

    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio_path), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    names = ", ".join(sorted({w for c in chunks for t in c["turns"] for w in re.findall(r"\b[A-Z][a-z]{3,}\b", t["voiced"])}))
    model = WhisperModel(WHISPER, device="cpu", compute_type="int8", cpu_threads=max(1, (os.cpu_count() or 4) - 4))
    segs, info = model.transcribe(audio, language="en", word_timestamps=True, vad_filter=True, beam_size=5,
                                  initial_prompt=names[:600])
    heard = [(x, w.start) for seg in segs for w in (seg.words or []) for x in norm_words(w.word)]

    sm = difflib.SequenceMatcher(a=[w for w, _, _ in want], b=[h for h, _ in heard], autojunk=False)
    problems = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        a, b = [w for w, _, _ in want[i1:i2]], [h for h, _ in heard[j1:j2]]
        if a and b and as_number(a) is not None and as_number(a) == as_number(b):
            continue
        _, line, ci = want[min(i1, len(want) - 1)]
        at = heard[min(j1, len(heard) - 1)][1] if heard else 0.0
        problems.append((ci, line, at, op, " ".join(a), " ".join(b)))

    est = sum(words(t["voiced"]) for c in chunks for t in c["turns"]) / WPM * 60
    print(f"{audio_path.name}: {fmt_min(info.duration)} (script estimate {fmt_min(est)}), "
          f"{len(want)} words in the script, {len(heard)} heard, {len(problems)} differences")
    for ci, line, at, op, a, b in problems:
        what = {"delete": "missing", "insert": "extra", "replace": "differs"}[op]
        print(f"  chunk {ci:>2}  line {line:>4}  at {fmt_min(at)}  {what:<7}  script: {a!r}  heard: {b!r}")
    if problems:
        print("Whisper mishears too (names, homophones): listen at the time given before retaking.\n"
              "A run of missing words at the end of a chunk means the chunk was cut off: retake it.")
    return 0


def cmd_voices(args):
    if args.engine == "fish":
        q = {"page_size": 40, "sort_by": "task_count", "language": "en"}
        if args.search:
            q["title"] = args.search
        data, _ = fish_call("GET", "/model?" + urllib.parse.urlencode(q), timeout=60)
        for v in json.loads(data).get("items", []):
            desc = (v.get("description") or "").replace("\n", " ")[:70]
            print(f"{v['_id']}  {v.get('title', '')[:24]:<24} uses={v.get('task_count', 0):>8}  "
                  f"{','.join(v.get('tags', []))[:40]:<40} {desc}")
        return 0
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
    if args.engine == "fish":
        data, _ = fish_call("GET", "/wallet/self/api-credit", timeout=60)
        d = json.loads(data)
        print(f"Fish Audio API credit: {d.get('credit', d)}")
        return 0
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
    r.add_argument("--transport", choices=["rest", "ws"], default="rest",
                   help="rest: one request per chunk (default); ws: whole script in one WebSocket session")
    r.add_argument("--model", help="override the script's model")
    r.add_argument("--out", help="write here instead of the script's output")
    vf = sub.add_parser("verify")
    vf.add_argument("script")
    vf.add_argument("audio", nargs="?", help="default: the script's output")
    v = sub.add_parser("voices")
    v.add_argument("search", nargs="?")
    v.add_argument("--engine", choices=list(ENGINES), default="elevenlabs")
    qa = sub.add_parser("quota")
    qa.add_argument("--engine", choices=list(ENGINES), default="elevenlabs")
    args = ap.parse_args()
    try:
        return {"check": cmd_check, "render": cmd_render, "verify": cmd_verify,
                "voices": cmd_voices, "quota": cmd_quota}[args.cmd](args)
    except ScriptError as e:
        print(f"script error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
