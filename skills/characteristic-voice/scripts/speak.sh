#!/usr/bin/env bash
set -euo pipefail

NOIZ_KEY_FILE="$HOME/.config/noiz/api_key"
NOIZ_BASE_URL="https://noiz.ai/v1"

usage() {
  cat <<'EOF'
Usage:
  speak.sh [--preset MODE] [options]   — speak with companion presets
  speak.sh config [--set-api-key KEY]  — check / set NOIZ_API_KEY

Presets (auto-set emotion + speed; explicit flags override):
  goodnight    gentle, warm, sleepy       (speed 0.85)
  morning      warm, cheerful             (speed 1.0)
  comfort      soft, unhurried            (speed 0.8)
  celebrate    excited, proud             (speed 1.1)
  chat         relaxed, natural           (speed 1.0)

Options:
  -t, --text TEXT        Text to speak
  -f, --text-file FILE   Text file to speak
  -o, --output FILE      Output audio file (required)
  --preset PRESET        One of the presets above
  --emo JSON             Override emotion, e.g. '{"Joy":0.5}'
  --speed NUM            Override speed multiplier
  -v, --voice VOICE      Kokoro voice name
  --voice-id ID          Noiz voice ID
  --ref-audio FILE       Reference audio for voice cloning (Noiz)
  --backend BACKEND      Force backend: kokoro | noiz
  --lang LANG            Language code
  -h, --help             Show this help

Examples:
  speak.sh config --set-api-key YOUR_KEY
  speak.sh --preset goodnight -t "Sweet dreams~" -o night.wav
  speak.sh --preset comfort -t "I'm here for you." --backend noiz --voice-id abc -o comfort.mp3
  speak.sh -t "Haha nice!" --emo '{"Joy":0.8}' --speed 1.1 -o reply.wav
EOF
  exit "${1:-0}"
}

# ── Presets ───────────────────────────────────────────────────────────

resolve_preset() {
  case "$1" in
    goodnight)  _preset_emo='{"Joy":0.2,"Tenderness":0.7}';  _preset_speed="0.85" ;;
    morning)    _preset_emo='{"Joy":0.6,"Tenderness":0.3}';  _preset_speed="1.0"  ;;
    comfort)    _preset_emo='{"Tenderness":0.8,"Sadness":0.3}'; _preset_speed="0.8" ;;
    celebrate)  _preset_emo='{"Joy":0.9,"Excitement":0.7}';  _preset_speed="1.1"  ;;
    chat)       _preset_emo='{"Joy":0.4,"Tenderness":0.2}';  _preset_speed="1.0"  ;;
    *) echo "Error: unknown preset '$1'. Use: goodnight, morning, comfort, celebrate, chat" >&2; exit 1 ;;
  esac
}

# ── API key ───────────────────────────────────────────────────────────

load_api_key() {
  if [[ -n "${NOIZ_API_KEY:-}" ]]; then
    NOIZ_API_KEY="$(normalize_api_key_base64 "$NOIZ_API_KEY")"
    export NOIZ_API_KEY
    return 0
  fi
  if [[ -f "$NOIZ_KEY_FILE" ]]; then
    NOIZ_API_KEY="$(tr -d '[:space:]' < "$NOIZ_KEY_FILE")"
    NOIZ_API_KEY="$(normalize_api_key_base64 "$NOIZ_API_KEY")"
    export NOIZ_API_KEY
    [[ -n "$NOIZ_API_KEY" ]] && return 0
  fi
  return 1
}

save_api_key() {
  local normalized
  normalized="$(normalize_api_key_base64 "$1")"
  printf '%s' "$normalized" > "$NOIZ_KEY_FILE"
  chmod 600 "$NOIZ_KEY_FILE"
}

normalize_api_key_base64() {
  local raw="$1"
  python3 - "$raw" <<'PY'
import base64
import binascii
import sys

value = sys.argv[1].strip()
if not value:
    print("", end="")
    raise SystemExit(0)

def is_base64(v: str) -> bool:
    padded = v + ("=" * (-len(v) % 4))
    try:
        decoded = base64.b64decode(padded, validate=True)
    except binascii.Error:
        return False
    if not decoded:
        return False
    canonical = base64.b64encode(decoded).decode("ascii").rstrip("=")
    return canonical == v.rstrip("=")

if is_base64(value):
    print(value, end="")
else:
    print(base64.b64encode(value.encode("utf-8")).decode("ascii"), end="")
PY
}

cmd_config() {
  local set_key=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --set-api-key) set_key="$2"; shift 2 ;;
      -h|--help) echo "Usage: speak.sh config [--set-api-key KEY]"; exit 0 ;;
      *) echo "Unknown option: $1"; exit 1 ;;
    esac
  done

  if [[ -n "$set_key" ]]; then
    save_api_key "$set_key"
    echo "API key saved to $NOIZ_KEY_FILE"
    return 0
  fi

  if load_api_key; then
    local masked="${NOIZ_API_KEY:0:4}****${NOIZ_API_KEY: -4}"
    echo "NOIZ_API_KEY is configured: $masked"
  else
    cat <<GUIDE
NOIZ_API_KEY is not configured.

Option A — Noiz (recommended):
  1. Get your API key from https://developers.noiz.ai/api-keys
  2. Run:
     bash skills/characteristic-voice/scripts/speak.sh config --set-api-key YOUR_KEY
  The key will be saved to $NOIZ_KEY_FILE and loaded automatically.

Option B — Kokoro (offline, local):
  uv tool install kokoro-tts
GUIDE
  fi
}

# ── Dispatch config before main argument parsing ──────────────────────

if [[ "${1:-}" == "config" ]]; then
  shift
  cmd_config "$@"
  exit 0
fi

# ── Backend detection ─────────────────────────────────────────────────

detect_backend() {
  local explicit="${1:-}"
  if [[ -n "$explicit" ]]; then
    echo "$explicit"
    return
  fi
  if load_api_key; then
    echo "noiz"
  elif command -v kokoro-tts &>/dev/null && kokoro-tts --help-voices &>/dev/null; then
    echo "kokoro"
  else
    echo ""
  fi
}

# ── Noiz helpers ──────────────────────────────────────────────────────

noiz_auto_select_voice() {
  local api_key="$1"
  local resp
  resp="$(curl -sS -H "Authorization: ${api_key}" \
    "${NOIZ_BASE_URL}/voices?voice_type=built-in&keyword=%E4%B8%AD%E6%96%87&skip=0&limit=10" 2>/dev/null)" || true
  if [[ -z "$resp" ]]; then
    return 1
  fi
  echo "$resp" | python3 -c "
import sys, json
try:
    voices = json.load(sys.stdin).get('data', {}).get('voices', [])
    for v in voices:
        if '女性' in (v.get('labels') or ''):
            print(v['voice_id']); break
    else:
        if voices: print(voices[0]['voice_id'])
except Exception:
    pass
" 2>/dev/null
}

noiz_tts() {
  local api_key="$1" text="$2" voice_id="$3" output="$4"
  local speed="$5" emo="$6" lang="$7" ref_audio="$8"

  local curl_args=(curl -sS -X POST
    -H "Authorization: ${api_key}"
    -o "$output"
    -w "%{http_code}"
    -F "text=$text"
    -F "output_format=wav"
    -F "speed=$speed"
  )

  [[ -n "$voice_id" ]]       && curl_args+=(-F "voice_id=$voice_id")
  [[ -n "$emo" ]]            && curl_args+=(-F "emo=$emo")
  [[ -n "$lang" ]]           && curl_args+=(-F "target_lang=$lang")
  [[ -n "$ref_audio" ]]      && curl_args+=(-F "file=@$ref_audio")

  local status
  status="$("${curl_args[@]}" "${NOIZ_BASE_URL}/text-to-speech" 2>/dev/null)"

  if [[ "$status" != "200" ]]; then
    echo "Error: Noiz API returned HTTP $status" >&2
    [[ -f "$output" ]] && head -c 500 "$output" >&2 && echo >&2
    rm -f "$output"
    return 1
  fi
}

# ── Parse arguments ──────────────────────────────────────────────────

preset="" text="" text_file="" output="" emo="" speed="" voice="" voice_id=""
backend="" lang="" format="wav" ref_audio=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --preset)          preset="$2"; shift 2 ;;
    -t|--text)         text="$2"; shift 2 ;;
    -f|--text-file)    text_file="$2"; shift 2 ;;
    -o|--output)       output="$2"; shift 2 ;;
    --emo)             emo="$2"; shift 2 ;;
    --speed)           speed="$2"; shift 2 ;;
    -v|--voice)        voice="$2"; shift 2 ;;
    --voice-id)        voice_id="$2"; shift 2 ;;
    --ref-audio)       ref_audio="$2"; shift 2 ;;
    --backend)         backend="$2"; shift 2 ;;
    --lang)            lang="$2"; shift 2 ;;
    -h|--help)         usage 0 ;;
    *) echo "Unknown option: $1" >&2; usage 1 ;;
  esac
done

if [[ -z "$output" ]]; then
  echo "Error: --output (-o) is required." >&2; exit 1
fi
if [[ -z "$text" && -z "$text_file" ]]; then
  echo "Error: --text (-t) or --text-file (-f) is required." >&2; exit 1
fi

# ── Apply preset defaults (explicit flags take precedence) ───────────

if [[ -n "$preset" ]]; then
  _preset_emo="" _preset_speed=""
  resolve_preset "$preset"
  [[ -z "$emo" ]]   && emo="$_preset_emo"
  [[ -z "$speed" ]] && speed="$_preset_speed"
fi
[[ -z "$speed" ]] && speed="1.0"

# ── Detect backend ───────────────────────────────────────────────────

detected="$(detect_backend "$backend")"

if [[ -z "$detected" ]]; then
  echo "Error: no TTS backend available." >&2
  echo "" >&2
  echo "  Option A — Noiz (recommended):" >&2
  echo "    1. Get your API key from https://developers.noiz.ai/api-keys" >&2
  echo "    2. Run: bash skills/characteristic-voice/scripts/speak.sh config --set-api-key YOUR_KEY" >&2
  echo "" >&2
  echo "  Option B — Kokoro (offline, local):" >&2
  echo "    uv tool install kokoro-tts" >&2
  exit 1
fi

# ── Resolve text ─────────────────────────────────────────────────────

if [[ -n "$text_file" && -z "$text" ]]; then
  text="$(<"$text_file")"
fi

# ── Kokoro backend ───────────────────────────────────────────────────

if [[ "$detected" == "kokoro" ]]; then
  input_path="$(mktemp /tmp/tts_input_XXXXXX.txt)"
  printf '%s' "$text" > "$input_path"

  cmd=(kokoro-tts "$input_path" "$output" --format "$format")
  [[ -n "$voice" ]] && cmd+=(--voice "$voice")
  [[ -n "$lang" ]]  && cmd+=(--lang "$lang")
  cmd+=(--speed "$speed")

  "${cmd[@]}"
  rm -f "$input_path"
  exit 0
fi

# ── Noiz backend ─────────────────────────────────────────────────────

load_api_key || true
api_key="${NOIZ_API_KEY:-}"
if [[ -z "$api_key" ]]; then
  echo "Error: NOIZ_API_KEY not configured." >&2
  echo "  Get your key at https://developers.noiz.ai/api-keys" >&2
  echo "  Then run: bash skills/characteristic-voice/scripts/speak.sh config --set-api-key YOUR_KEY" >&2
  exit 1
fi

if [[ -z "$voice_id" && -z "$ref_audio" ]]; then
  echo "[noiz] Auto-selecting voice..." >&2
  voice_id="$(noiz_auto_select_voice "$api_key" || true)"
  if [[ -z "$voice_id" ]]; then
    echo "Error: failed to auto-select a voice. Please pass --voice-id or --ref-audio." >&2
    exit 1
  fi
  echo "[noiz] Using voice_id: $voice_id" >&2
fi

noiz_tts "$api_key" "$text" "$voice_id" "$output" \
  "$speed" "$emo" "$lang" "$ref_audio"

echo "Done. Output: $output" >&2
