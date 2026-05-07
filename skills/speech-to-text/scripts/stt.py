#!/usr/bin/env python3
"""Transcribe audio files to text using the Noiz speech-to-text API.

Usage:
    python3 stt.py audio.mp3
    python3 stt.py interview.wav --language en -o transcript.txt
    python3 stt.py meeting.wav --json -o result.json
    python3 stt.py config --set-api-key YOUR_KEY
"""
import argparse
import json
import os
import sys
from pathlib import Path

NOIZ_KEY_FILE = Path.home() / ".config" / "noiz" / "api_key"
API_BASE = "https://noiz.ai/v1"

SUPPORTED_FORMATS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".webm"}
MAX_FILE_SIZE_MB = 50


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


def transcribe(audio_path: Path, language: str = None, api_key: str = None,
               out_path: Path = None, output_json: bool = False) -> dict:
    try:
        import requests
    except ImportError:
        print("error: 'requests' package is required. Run: pip install requests", file=sys.stderr)
        sys.exit(1)

    # Validate file
    if not audio_path.exists():
        print(f"error: File not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    suffix = audio_path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        print(
            f"error: Unsupported file format '{suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
            file=sys.stderr,
        )
        sys.exit(1)

    size_mb = audio_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        print(f"error: File too large ({size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB.", file=sys.stderr)
        sys.exit(1)

    key = load_api_key(api_key)
    if not key:
        print(
            "error: No API key found.\n"
            "  Set one with: python3 stt.py config --set-api-key YOUR_KEY\n"
            "  Or: export NOIZ_API_KEY=YOUR_KEY\n"
            "  Get a key at: https://developers.noiz.ai/api-keys",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Transcribing {audio_path.name} ({size_mb:.1f} MB)...", file=sys.stderr)

    with open(audio_path, "rb") as f:
        files = {"file": (audio_path.name, f)}
        data = {}
        if language:
            data["language"] = language

        resp = requests.post(
            f"{API_BASE}/speech-to-text",
            headers={"Authorization": key},
            files=files,
            data=data,
            timeout=300,
        )

    if resp.status_code != 200:
        print(f"error: API returned HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    body = resp.json()
    code = body.get("code", -1)
    if code == 429:
        print("error: Rate limit exceeded. Please wait and retry.", file=sys.stderr)
        sys.exit(1)
    if code == 401:
        print("error: Invalid or missing API key.", file=sys.stderr)
        sys.exit(1)
    if code != 0:
        print(f"error: API error code={code} message={body.get('message', '')}", file=sys.stderr)
        sys.exit(1)

    result = body.get("data", {})
    transcript = result.get("transcript", "")
    duration = result.get("duration", 0)
    detected_lang = result.get("language", "unknown")

    print(f"  Language: {detected_lang} | Duration: {duration:.1f}s", file=sys.stderr)

    if output_json:
        output_str = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output_str = transcript

    if out_path:
        out_path.write_text(output_str, encoding="utf-8")
        print(f"  Saved to {out_path}", file=sys.stderr)
    else:
        print(output_str)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio to text using the Noiz API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 stt.py audio.mp3
  python3 stt.py interview.wav --language en
  python3 stt.py podcast.m4a -o transcript.txt
  python3 stt.py meeting.wav --json -o result.json
  python3 stt.py config --set-api-key YOUR_KEY
        """,
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    # config subcommand
    cfg = subparsers.add_parser("config", help="Configure API key")
    cfg.add_argument("--set-api-key", metavar="KEY", help="Save API key to ~/.config/noiz/api_key")

    # transcribe (default)
    parser.add_argument("file", nargs="?", help="Audio file to transcribe")
    parser.add_argument("--language", "-l", default=None,
                        help="Language code (e.g. en, zh, ja). Omit to auto-detect.")
    parser.add_argument("--output", "-o", default=None,
                        help="Output file path (default: print to stdout)")
    parser.add_argument("--json", dest="output_json", action="store_true",
                        help="Output full JSON with timestamps and speaker labels")
    parser.add_argument("--api-key", default=None, help="Noiz API key (overrides stored key)")

    args = parser.parse_args()

    if args.subcommand == "config":
        if args.set_api_key:
            save_api_key(args.set_api_key)
        else:
            cfg.print_help()
        return

    if not args.file:
        parser.print_help()
        sys.exit(1)

    out_path = Path(args.output) if args.output else None
    transcribe(
        audio_path=Path(args.file),
        language=args.language,
        api_key=args.api_key,
        out_path=out_path,
        output_json=args.output_json,
    )


if __name__ == "__main__":
    main()
