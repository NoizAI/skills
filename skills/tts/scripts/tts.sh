#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  cat <<'EOF'
Usage:
  tts.sh speak  [options]   — text to audio (simple mode)
  tts.sh render [options]   — SRT to timeline-accurate audio
  tts.sh to-srt [options]   — text file to SRT with auto timings
  tts.sh setup  [backend]   — install dependencies for a backend

Examples:
  tts.sh speak -t "Hello" -v af_sarah -o hello.wav
  tts.sh speak -f article.txt -v zf_xiaoni --lang cmn -o out.mp3
  tts.sh speak -t "Hi" --backend noiz --voice-id abc -o hi.wav
  tts.sh render --srt input.srt --voice-map vm.json -o output.wav
  tts.sh render --srt input.srt --voice-map vm.json --backend noiz -o output.wav
  tts.sh to-srt -i article.txt -o article.srt
  tts.sh to-srt -i article.txt -o article.srt --cps 15 --gap 500
  tts.sh setup kokoro
  tts.sh setup noiz
EOF
  exit "${1:-0}"
}

# ── Auto-detect backend ──────────────────────────────────────────────

detect_backend() {
  local explicit="${1:-}"
  if [[ -n "$explicit" ]]; then
    echo "$explicit"
    return
  fi
  if [[ -n "${NOIZ_API_KEY:-}" ]]; then
    echo "noiz"
  elif command -v kokoro-tts &>/dev/null; then
    echo "kokoro"
  else
    echo ""
  fi
}

# ── setup ─────────────────────────────────────────────────────────────

cmd_setup() {
  local backend="${1:-}"
  case "$backend" in
    kokoro)
      echo "Installing kokoro-tts..."
      uv tool install kokoro-tts
      echo "Downloading model files..."
      wget -nc https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin || true
      wget -nc https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx || true
      echo "Done. Kokoro ready."
      ;;
    noiz)
      echo "Installing requests..."
      uv pip install requests
      echo "Done. Set NOIZ_API_KEY env var to use Noiz backend."
      ;;
    *)
      echo "Usage: tts.sh setup kokoro|noiz"
      exit 1
      ;;
  esac
}

# ── speak (simple mode) ──────────────────────────────────────────────

cmd_speak() {
  local text="" text_file="" voice="" voice_id="" output="" format="wav"
  local lang="" speed="" emo="" backend_flag="" ref_audio=""
  local auto_emotion=false similarity_enh=false save_voice=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -t|--text)       text="$2"; shift 2 ;;
      -f|--text-file)  text_file="$2"; shift 2 ;;
      -v|--voice)      voice="$2"; shift 2 ;;
      --voice-id)      voice_id="$2"; shift 2 ;;
      -o|--output)     output="$2"; shift 2 ;;
      --format)        format="$2"; shift 2 ;;
      --lang)          lang="$2"; shift 2 ;;
      --speed)         speed="$2"; shift 2 ;;
      --emo)           emo="$2"; shift 2 ;;
      --backend)       backend_flag="$2"; shift 2 ;;
      --ref-audio)     ref_audio="$2"; shift 2 ;;
      --auto-emotion)  auto_emotion=true; shift ;;
      --similarity-enh) similarity_enh=true; shift ;;
      --save-voice)    save_voice=true; shift ;;
      -h|--help)       usage 0 ;;
      *) echo "Unknown option: $1"; usage 1 ;;
    esac
  done

  if [[ -z "$output" ]]; then
    echo "Error: --output (-o) is required." >&2; exit 1
  fi
  if [[ -z "$text" && -z "$text_file" ]]; then
    echo "Error: --text (-t) or --text-file (-f) is required." >&2; exit 1
  fi

  local backend
  backend="$(detect_backend "$backend_flag")"

  if [[ -z "$backend" ]]; then
    echo "Error: no backend available. Run 'tts.sh setup kokoro' or 'tts.sh setup noiz'." >&2
    exit 1
  fi

  if [[ "$backend" == "kokoro" ]]; then
    # Write text to temp file if passed as string
    local input_path="$text_file"
    if [[ -n "$text" ]]; then
      input_path="$(mktemp /tmp/tts_input.XXXXXX.txt)"
      printf '%s' "$text" > "$input_path"
    fi

    local cmd=(kokoro-tts "$input_path" "$output" --format "$format")
    [[ -n "$voice" ]] && cmd+=(--voice "$voice")
    [[ -n "$lang" ]]  && cmd+=(--lang "$lang")
    [[ -n "$speed" ]] && cmd+=(--speed "$speed")

    "${cmd[@]}"

    [[ -n "$text" ]] && rm -f "$input_path"
  else
    # Noiz backend
    local api_key="${NOIZ_API_KEY:-}"
    if [[ -z "$api_key" ]]; then
      echo "Error: NOIZ_API_KEY not set." >&2; exit 1
    fi

    local cmd=(python3 "$SCRIPT_DIR/noiz_tts.py" --api-key "$api_key" --output "$output" --output-format "$format")

    if [[ -n "$text" ]]; then
      cmd+=(--text "$text")
    else
      cmd+=(--text-file "$text_file")
    fi

    [[ -n "$voice_id" ]]  && cmd+=(--voice-id "$voice_id")
    [[ -n "$ref_audio" ]] && cmd+=(--reference-audio "$ref_audio")
    [[ -n "$speed" ]]     && cmd+=(--speed "$speed")
    [[ -n "$emo" ]]       && cmd+=(--emo "$emo")
    [[ -n "$lang" ]]      && cmd+=(--target-lang "$lang")
    $auto_emotion         && cmd+=(--auto-emotion)
    $similarity_enh       && cmd+=(--similarity-enh)
    $save_voice           && cmd+=(--save-voice)

    "${cmd[@]}"
  fi
}

# ── render (timeline mode) ───────────────────────────────────────────

cmd_render() {
  local srt="" voice_map="" output="" backend_flag="" extra_args=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --srt)        srt="$2"; shift 2 ;;
      --voice-map)  voice_map="$2"; shift 2 ;;
      -o|--output)  output="$2"; shift 2 ;;
      --backend)    backend_flag="$2"; shift 2 ;;
      -h|--help)    usage 0 ;;
      *)            extra_args+=("$1"); shift ;;
    esac
  done

  if [[ -z "$srt" || -z "$voice_map" || -z "$output" ]]; then
    echo "Error: --srt, --voice-map, and --output (-o) are all required." >&2; exit 1
  fi

  local backend
  backend="$(detect_backend "$backend_flag")"
  if [[ -z "$backend" ]]; then
    echo "Error: no backend available. Run 'tts.sh setup kokoro' or 'tts.sh setup noiz'." >&2
    exit 1
  fi

  local cmd=(python3 "$SCRIPT_DIR/render_timeline.py"
    --srt "$srt" --voice-map "$voice_map" --output "$output" --backend "$backend")

  if [[ "$backend" == "noiz" ]]; then
    local api_key="${NOIZ_API_KEY:-}"
    if [[ -z "$api_key" ]]; then
      echo "Error: NOIZ_API_KEY not set." >&2; exit 1
    fi
    cmd+=(--api-key "$api_key")
  fi

  cmd+=("${extra_args[@]}")
  "${cmd[@]}"
}

# ── to-srt ────────────────────────────────────────────────────────────

cmd_to_srt() {
  local input="" output="" cps="" gap=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -i|--input)   input="$2"; shift 2 ;;
      -o|--output)  output="$2"; shift 2 ;;
      --cps)        cps="$2"; shift 2 ;;
      --gap)        gap="$2"; shift 2 ;;
      -h|--help)    usage 0 ;;
      *) echo "Unknown option: $1"; usage 1 ;;
    esac
  done

  if [[ -z "$input" || -z "$output" ]]; then
    echo "Error: --input (-i) and --output (-o) are required." >&2; exit 1
  fi

  local cmd=(python3 "$SCRIPT_DIR/text_to_srt.py" --input "$input" --output "$output")
  [[ -n "$cps" ]] && cmd+=(--chars-per-second "$cps")
  [[ -n "$gap" ]] && cmd+=(--gap-ms "$gap")

  "${cmd[@]}"
}

# ── dispatch ──────────────────────────────────────────────────────────

case "${1:-}" in
  speak)   shift; cmd_speak "$@" ;;
  render)  shift; cmd_render "$@" ;;
  to-srt)  shift; cmd_to_srt "$@" ;;
  setup)   shift; cmd_setup "$@" ;;
  -h|--help|"") usage 0 ;;
  *) echo "Unknown command: $1"; usage 1 ;;
esac
