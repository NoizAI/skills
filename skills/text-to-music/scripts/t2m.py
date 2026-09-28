#!/usr/bin/env python3
"""Generate songs and covers from text and lyrics using the Noiz API.

Usage:
    python3 t2m.py "upbeat indie pop, bright guitars" --lyrics-prompt "a song about summer road trips"
    python3 t2m.py "lo-fi hip hop, mellow" --lyrics-file song.txt --duration 120 -o chill.mp3
    python3 t2m.py cover original.mp3 --style "jazz, female vocal" --recognize-lyrics -o cover.mp3
    python3 t2m.py lyrics original.mp3 -o lyrics.txt
    python3 t2m.py status <gen_product_id> [<gen_product_id> ...] -o song.mp3
    python3 t2m.py status --cover <task_id> -o cover.mp3
    python3 t2m.py config --set-api-key YOUR_KEY
"""
import argparse
import mimetypes
import os
import sys
import time
from pathlib import Path

NOIZ_KEY_FILE = Path.home() / ".config" / "noiz" / "api_key"
API_BASE = "https://noiz.ai/v1"

MAX_PROMPT_LEN = 1500
MAX_LYRICS_LEN = 5000
MAX_TITLE_LEN = 80
MAX_TAGS_LEN = 50
MAX_VOCAL_TIMBRE_LEN = 50
MAX_LYRICS_FILE_BYTES = 64 * 1024
MAX_REF_AUDIO_BYTES = 20 * 1024 * 1024
MAX_COVER_SOURCE_BYTES = 100 * 1024 * 1024
AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
TERMINAL_STATUSES = {"succeeded", "failed"}


def load_api_key(override: str = None) -> str:
    if override:
        return override.strip()
    env = os.environ.get("NOIZ_API_KEY", "").strip()
    if env:
        return env
    if NOIZ_KEY_FILE.exists():
        key = NOIZ_KEY_FILE.read_text(encoding="utf-8").strip()
        if key:
            return key
    return ""


def save_api_key(key: str) -> None:
    NOIZ_KEY_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    NOIZ_KEY_FILE.write_text(key.strip(), encoding="utf-8")
    os.chmod(str(NOIZ_KEY_FILE), 0o600)
    print(f"[config] API key saved to {NOIZ_KEY_FILE}")


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def import_requests():
    try:
        import requests
    except ImportError:
        fail("'requests' package is required. Run: uv pip install requests")
    return requests


def require_api_key(override: str = None) -> str:
    key = load_api_key(override)
    if not key:
        fail(
            "No API key found.\n"
            "  Set one with: python3 t2m.py config --set-api-key YOUR_KEY\n"
            "  Or: export NOIZ_API_KEY=YOUR_KEY\n"
            "  Get a key at: https://developers.noiz.ai/api-keys"
        )
    return key


def parse_body(resp) -> dict:
    try:
        body = resp.json()
    except ValueError:
        fail(f"API returned HTTP {resp.status_code}: {resp.text[:500]}")
    code = body.get("code", -1)
    message = body.get("message", "")
    if code == 0:
        return body.get("data") or {}
    if code == 401 or resp.status_code == 401:
        fail("Invalid or missing API key.")
    if code == 402:
        fail(f"Insufficient credits or no payment method on file: {message}")
    if code == 404:
        fail(f"Job not found: {message}")
    if code == 429:
        fail(f"Rate limit exceeded, wait a minute and retry: {message}")
    if code == 503:
        fail(f"Service temporarily unavailable, try again later: {message}")
    fail(f"API error code={code} message={message}")


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def check_audio_file(value: str, max_bytes: int, label: str) -> None:
    if is_url(value):
        return
    path = Path(value)
    if not path.is_file():
        fail(f"{label} not found: {path}")
    if path.suffix.lower() not in AUDIO_FORMATS:
        fail(f"unsupported {label} format '{path.suffix}'. Supported: {', '.join(sorted(AUDIO_FORMATS))}")
    if path.stat().st_size > max_bytes:
        fail(f"{label} too large (max {max_bytes // (1024 * 1024)} MB)")


def read_lyrics_file(value: str) -> str:
    path = Path(value)
    if not path.is_file():
        fail(f"lyrics file not found: {path}")
    if path.stat().st_size > MAX_LYRICS_FILE_BYTES:
        fail(f"lyrics file too large (max {MAX_LYRICS_FILE_BYTES // 1024} KB)")
    try:
        text = path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        fail("lyrics file must be UTF-8 text")
    if not text:
        fail("lyrics file is empty")
    return text


def check_common(args) -> None:
    if args.lyrics and len(args.lyrics) > MAX_LYRICS_LEN:
        fail(f"lyrics exceed {MAX_LYRICS_LEN} characters")
    if args.title and len(args.title) > MAX_TITLE_LEN:
        fail(f"title exceeds {MAX_TITLE_LEN} characters")
    if args.vocal_timbre and len(args.vocal_timbre) > MAX_VOCAL_TIMBRE_LEN:
        fail(f"vocal timbre exceeds {MAX_VOCAL_TIMBRE_LEN} characters")


def audio_upload(path: str) -> tuple:
    mime = mimetypes.guess_type(path)[0] or "audio/mpeg"
    return (Path(path).name, open(path, "rb"), mime)


def post(endpoint: str, key: str, data: dict, files: dict = None, timeout: float = 180) -> dict:
    requests = import_requests()
    try:
        resp = requests.post(
            f"{API_BASE}{endpoint}",
            headers={"Authorization": key},
            data=data,
            files=files or None,
            timeout=timeout,
        )
    finally:
        for f in (files or {}).values():
            f[1].close()
    return parse_body(resp)


def get(endpoint: str, key: str) -> dict:
    requests = import_requests()
    resp = requests.get(f"{API_BASE}{endpoint}", headers={"Authorization": key}, timeout=60)
    return parse_body(resp)


# ── Text-to-music ────────────────────────────────────────────────────

def validate_generate(args) -> None:
    lyric_sources = [s for s in (args.lyrics, args.lyrics_file, args.lyrics_prompt) if s]
    if not lyric_sources:
        fail("provide one of --lyrics, --lyrics-file or --lyrics-prompt")
    if len(lyric_sources) > 1:
        fail("--lyrics, --lyrics-file and --lyrics-prompt are mutually exclusive")
    if len(args.prompt) > MAX_PROMPT_LEN:
        fail(f"prompt exceeds {MAX_PROMPT_LEN} characters")
    if args.lyrics_prompt and len(args.lyrics_prompt) > MAX_LYRICS_LEN:
        fail(f"lyrics prompt exceeds {MAX_LYRICS_LEN} characters")
    if args.tags and len(args.tags) > MAX_TAGS_LEN:
        fail(f"tags exceed {MAX_TAGS_LEN} characters")
    check_common(args)
    if args.lyrics_file:
        read_lyrics_file(args.lyrics_file)
    if args.ref_audio:
        check_audio_file(args.ref_audio, MAX_REF_AUDIO_BYTES, "reference audio")


def submit_generate(args, key: str) -> list:
    data = {"prompt": args.prompt}
    optional_fields = {
        "lyrics": read_lyrics_file(args.lyrics_file) if args.lyrics_file else args.lyrics,
        "lyrics_prompt": args.lyrics_prompt,
        "title": args.title,
        "tags": args.tags,
        "negative_tags": args.negative_tags,
        "vocal_gender": args.vocal_gender,
        "vocal_timbre": args.vocal_timbre,
        "target_duration": str(args.duration) if args.duration else None,
    }
    data.update({k: v for k, v in optional_fields.items() if v})
    files = {}
    if args.ref_audio:
        if is_url(args.ref_audio):
            data["reference_audio_url"] = args.ref_audio
        else:
            files["reference_audio_file"] = audio_upload(args.ref_audio)

    body = post("/text-to-music", key, data, files)
    ids = [r["gen_product_id"] for r in body.get("results", []) if r.get("gen_product_id")]
    if not ids:
        fail(f"Submission returned no jobs: {body.get('errors') or body}")
    return ids


def fetch_generate(ids: list, key: str):
    return [get(f"/text-to-music/{gid}", key) for gid in ids], None


# ── Cover ────────────────────────────────────────────────────────────

def source_fields(source: str) -> tuple:
    if is_url(source):
        return {"source_audio_url": source}, {}
    return {}, {"source_audio_file": audio_upload(source)}


def recognize_lyrics(source: str, key: str) -> str:
    print("Recognizing lyrics from source (100 credits if vocals are found)...", file=sys.stderr)
    data, files = source_fields(source)
    body = post("/text-to-music/cover/recognize-lyrics", key, data, files, timeout=300)
    lyrics = (body.get("lyrics") or "").strip()
    if not body.get("has_vocals") or not lyrics:
        fail("No vocals detected in the source audio (no credits charged). "
             "Pass lyrics with --lyrics or --lyrics-file instead.")
    return lyrics


def validate_cover(args) -> None:
    lyric_sources = [s for s in (args.lyrics, args.lyrics_file, args.recognize_lyrics) if s]
    if not lyric_sources:
        fail("provide one of --lyrics, --lyrics-file or --recognize-lyrics")
    if len(lyric_sources) > 1:
        fail("--lyrics, --lyrics-file and --recognize-lyrics are mutually exclusive")
    if not args.prompt and not args.style:
        fail("provide --prompt and/or --style to describe the cover's sound")
    if args.prompt and len(args.prompt) > MAX_PROMPT_LEN:
        fail(f"prompt exceeds {MAX_PROMPT_LEN} characters")
    if args.style and len(args.style) > MAX_TAGS_LEN:
        fail(f"style exceeds {MAX_TAGS_LEN} characters")
    check_common(args)
    if args.lyrics_file:
        read_lyrics_file(args.lyrics_file)
    check_audio_file(args.source, MAX_COVER_SOURCE_BYTES, "source audio")


def submit_cover(args, key: str, lyrics: str) -> str:
    data, files = source_fields(args.source)
    data["lyrics"] = lyrics
    data["melody_adherence"] = args.adherence
    optional_fields = {
        "music_description": args.prompt,
        "style": args.style,
        "title": args.title,
        "vocal_gender": args.vocal_gender,
        "vocal_timbre": args.vocal_timbre,
    }
    data.update({k: v for k, v in optional_fields.items() if v})
    body = post("/text-to-music/cover", key, data, files, timeout=300)
    task_id = body.get("task_id")
    if not task_id:
        fail(f"Submission returned no task: {body}")
    return task_id


def fetch_cover(task_id: str, key: str):
    body = get(f"/text-to-music/cover/{task_id}", key)
    return body.get("results") or [], body.get("stage")


# ── Polling & download ───────────────────────────────────────────────

def wait_for(fetch, resume_cmd: str, interval: float, timeout: float) -> list:
    deadline = time.time() + timeout
    while True:
        items, stage = fetch()
        progress = ", ".join(
            f"v{i + 1}={item.get('status')}" + (f" {item['progress']}" if item.get("progress") else "")
            for i, item in enumerate(items)
        )
        stage_label = f" stage={stage}" if stage else ""
        print(f"  [{time.strftime('%H:%M:%S')}]{stage_label} {progress}", file=sys.stderr)
        if items and all(item.get("status") in TERMINAL_STATUSES for item in items):
            return items
        if time.time() >= deadline:
            print(f"error: Timed out after {int(timeout)}s. Resume later with:\n  {resume_cmd}",
                  file=sys.stderr)
            sys.exit(2)
        time.sleep(interval)


def variant_path(out_path: Path, index: int, total: int) -> Path:
    if total == 1:
        return out_path
    return out_path.with_name(f"{out_path.stem}_v{index + 1}{out_path.suffix or '.mp3'}")


def download_results(items: list, out_path: Path) -> int:
    requests = import_requests()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    saved = 0
    lyrics_written = False
    for i, item in enumerate(items):
        if item.get("status") != "succeeded" or not item.get("audio_url"):
            print(f"✗ v{i + 1} failed: {item.get('error_message') or item.get('status')}", file=sys.stderr)
            continue
        audio_resp = requests.get(item["audio_url"], timeout=120)
        if audio_resp.status_code != 200:
            print(f"✗ v{i + 1} download failed: HTTP {audio_resp.status_code}", file=sys.stderr)
            continue
        path = variant_path(out_path, i, len(items))
        path.write_bytes(audio_resp.content)
        saved += 1
        size_kb = len(audio_resp.content) / 1024
        title = item.get("title") or ""
        print(f"✓ Saved v{i + 1} to {path} ({item.get('duration')}s, {size_kb:.0f} KB) {title}".rstrip())
        print(f"  URL (valid ~24h): {item['audio_url']}")
        if item.get("lyrics_generated") and not lyrics_written:
            lyrics_path = out_path.with_name(f"{out_path.stem}_lyrics.txt")
            lyrics_path.write_text(item["lyrics_generated"], encoding="utf-8")
            print(f"  Lyrics saved to {lyrics_path}")
            lyrics_written = True

    billed = next((item for item in items if item.get("credit_cost")), None)
    if billed:
        print(f"  Cost: {billed['credit_cost']} credits for the job (billing: {billed.get('api_billing')})")
    return saved


def finish(fetch, resume_cmd: str, args) -> None:
    items = wait_for(fetch, resume_cmd, args.poll_interval, args.timeout)
    if download_results(items, Path(args.output)) == 0:
        sys.exit(1)


# ── CLI ──────────────────────────────────────────────────────────────

def add_output_args(p, default_output: str) -> None:
    p.add_argument("--output", "-o", default=default_output,
                   help=f"Output path; variants are saved as <stem>_v1.mp3, <stem>_v2.mp3 "
                        f"(default: {default_output})")
    p.add_argument("--poll-interval", type=float, default=10,
                   help="Seconds between status checks (default: 10)")
    p.add_argument("--timeout", type=float, default=1800,
                   help="Max seconds to wait for generation (default: 1800)")
    p.add_argument("--api-key", default=None, help="Noiz API key (overrides stored key)")


def add_vocal_args(p) -> None:
    p.add_argument("--title", default=None, help="Song title (≤80 chars)")
    p.add_argument("--vocal-gender", choices=["Male", "Female"], default=None)
    p.add_argument("--vocal-timbre", default=None,
                   help="Free-form vocal description, e.g. 'husky warm alto' (≤50 chars)")


def cmd_config(argv) -> None:
    p = argparse.ArgumentParser(prog="t2m.py config", description="Configure API key")
    p.add_argument("--set-api-key", metavar="KEY", help="Save API key to ~/.config/noiz/api_key")
    args = p.parse_args(argv)
    if args.set_api_key:
        save_api_key(args.set_api_key)
    else:
        p.print_help()


def cmd_status(argv) -> None:
    p = argparse.ArgumentParser(prog="t2m.py status",
                                description="Check (and download) previously submitted jobs")
    p.add_argument("ids", nargs="+", help="gen_product_id(s), or a cover task_id with --cover")
    p.add_argument("--cover", action="store_true", help="The id is a cover task_id")
    p.add_argument("--no-wait", action="store_true", help="Print current status once without waiting")
    add_output_args(p, "song.mp3")
    args = p.parse_args(argv)
    key = require_api_key(args.api_key)

    if args.cover:
        task_id = args.ids[0]
        fetch = lambda: fetch_cover(task_id, key)
        resume = f"python3 t2m.py status --cover {task_id}"
    else:
        fetch = lambda: fetch_generate(args.ids, key)
        resume = f"python3 t2m.py status {' '.join(args.ids)}"

    if args.no_wait:
        items, stage = fetch()
        if stage:
            print(f"stage: {stage}")
        for i, item in enumerate(items):
            print(f"v{i + 1} {item.get('gen_product_id')}: {item.get('status')} "
                  f"{item.get('progress') or ''}".rstrip())
        return
    finish(fetch, resume, args)


def cmd_lyrics(argv) -> None:
    p = argparse.ArgumentParser(prog="t2m.py lyrics",
                                description="Recognize lyrics from a song (100 credits if vocals are found)")
    p.add_argument("source", help="Song as local file (≤100 MB) or public URL")
    p.add_argument("--output", "-o", default=None, help="Save lyrics to this file (default: print)")
    p.add_argument("--api-key", default=None, help="Noiz API key (overrides stored key)")
    args = p.parse_args(argv)
    check_audio_file(args.source, MAX_COVER_SOURCE_BYTES, "source audio")
    lyrics = recognize_lyrics(args.source, require_api_key(args.api_key))
    if args.output:
        Path(args.output).write_text(lyrics + "\n", encoding="utf-8")
        print(f"✓ Lyrics saved to {args.output}")
    else:
        print(lyrics)


def cmd_cover(argv) -> None:
    p = argparse.ArgumentParser(
        prog="t2m.py cover",
        description="Cover an existing song in a new style (keeps the melody, re-sings with new arrangement)",
    )
    p.add_argument("source", help="Original song as local file (≤100 MB) or public URL")
    p.add_argument("--prompt", "-p", default=None, help="Description of the cover's sound (≤1500 chars)")
    p.add_argument("--style", "-s", default=None, help="Short style tags, e.g. 'jazz, female vocal' (≤50 chars)")
    p.add_argument("--adherence", choices=["high", "main_melody"], default="high",
                   help="high = follow the original closely; main_melody = keep only the main melody "
                        "(default: high)")
    lyr = p.add_argument_group("lyrics (exactly one required)")
    lyr.add_argument("--lyrics", "-l", default=None, help="Lyrics to sing")
    lyr.add_argument("--lyrics-file", default=None, help="UTF-8 .txt file with lyrics (≤64 KB)")
    lyr.add_argument("--recognize-lyrics", action="store_true",
                     help="Transcribe lyrics from the source first (100 credits if vocals are found)")
    add_vocal_args(p)
    p.add_argument("--no-wait", action="store_true", help="Submit and print the task id, then exit")
    add_output_args(p, "cover.mp3")
    args = p.parse_args(argv)

    validate_cover(args)
    key = require_api_key(args.api_key)
    if args.recognize_lyrics:
        lyrics = recognize_lyrics(args.source, key)
        print(f"  Recognized {len(lyrics)} characters of lyrics", file=sys.stderr)
    elif args.lyrics_file:
        lyrics = read_lyrics_file(args.lyrics_file)
    else:
        lyrics = args.lyrics

    task_id = submit_cover(args, key, lyrics)
    resume = f"python3 t2m.py status --cover {task_id} -o {args.output}"
    print(f"Submitted cover task: {task_id}", file=sys.stderr)
    if args.no_wait:
        print(f"Check later with: {resume}")
        return
    print("Generating cover (usually several minutes)...", file=sys.stderr)
    finish(lambda: fetch_cover(task_id, key), resume, args)


def cmd_generate(argv) -> None:
    p = argparse.ArgumentParser(
        prog="t2m.py",
        description="Generate songs from text using the Noiz text-to-music API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  cover <source> ...          Cover an existing song in a new style (see: t2m.py cover -h)
  lyrics <source>             Recognize lyrics from a song
  status <id> [<id> ...]      Check / download jobs (--cover for a cover task_id)
  config --set-api-key KEY    Save API key

Examples:
  python3 t2m.py "upbeat indie pop, bright guitars" --lyrics-prompt "a song about summer road trips"
  python3 t2m.py "lo-fi hip hop, mellow" --lyrics-file song.txt --duration 120 -o chill.mp3
  python3 t2m.py cover original.mp3 --style "jazz, female vocal" --recognize-lyrics
  python3 t2m.py status <id_v1> <id_v2> -o song.mp3
        """,
    )
    p.add_argument("prompt", nargs="?", help="Music description: genre, mood, instruments, tempo")
    lyr = p.add_argument_group("lyrics (exactly one required)")
    lyr.add_argument("--lyrics", "-l", default=None,
                     help="Lyrics text, optionally with [Verse]/[Chorus] section markers")
    lyr.add_argument("--lyrics-file", default=None, help="UTF-8 .txt file containing lyrics (≤64 KB)")
    lyr.add_argument("--lyrics-prompt", default=None, help="Let the server write lyrics from this theme")
    p.add_argument("--tags", default=None, help="Style tags, comma-separated (≤50 chars)")
    p.add_argument("--negative-tags", default=None, help="Styles to avoid, comma-separated")
    add_vocal_args(p)
    p.add_argument("--duration", "-d", type=int, choices=[60, 120, 180], default=None,
                   help="Target length hint in seconds. Omit to let the model decide.")
    p.add_argument("--ref-audio", default=None, help="Reference song as local file (≤20 MB) or public URL")
    p.add_argument("--no-wait", action="store_true",
                   help="Submit and print job IDs without waiting for the result")
    add_output_args(p, "song.mp3")
    args = p.parse_args(argv)

    if not args.prompt:
        p.print_help()
        sys.exit(1)

    validate_generate(args)
    key = require_api_key(args.api_key)
    ids = submit_generate(args, key)
    resume = f"python3 t2m.py status {' '.join(ids)} -o {args.output}"
    print(f"Submitted {len(ids)} variants: {' '.join(ids)}", file=sys.stderr)
    if args.no_wait:
        print(f"Check later with: {resume}")
        return
    print("Generating (usually a few minutes)...", file=sys.stderr)
    finish(lambda: fetch_generate(ids, key), resume, args)


SUBCOMMANDS = {"config": cmd_config, "status": cmd_status, "lyrics": cmd_lyrics, "cover": cmd_cover}


def main():
    # Subcommands are dispatched by hand: an argparse subparser would swallow
    # the free-text prompt as an invalid subcommand name.
    argv = sys.argv[1:]
    if argv and argv[0] in SUBCOMMANDS:
        SUBCOMMANDS[argv[0]](argv[1:])
    else:
        cmd_generate(argv)


if __name__ == "__main__":
    main()
