#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TTS_SH="$SCRIPT_DIR/../../tts/scripts/tts.sh"

usage() {
  cat <<'EOF'
Usage: companion_speak.sh [--preset MODE] [options]

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
  --format FORMAT        wav or mp3 (default: wav)
  --auto-emotion         Let Noiz auto-detect emotion from text
  --similarity-enh       Enhance voice similarity (Noiz cloning)
  -h, --help             Show this help

Examples:
  companion_speak.sh --preset goodnight -t "Sweet dreams~" -o night.wav
  companion_speak.sh --preset comfort -t "I'm here for you." --backend noiz --voice-id abc -o comfort.mp3
  companion_speak.sh -t "Haha nice!" --emo '{"Joy":0.8}' --speed 1.1 -o reply.wav
EOF
  exit "${1:-0}"
}

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

# ── Parse arguments ──────────────────────────────────────────────────

preset="" text="" text_file="" output="" emo="" speed="" voice="" voice_id=""
backend="" lang="" format="" ref_audio="" auto_emotion=false similarity_enh=false

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
    --format)          format="$2"; shift 2 ;;
    --auto-emotion)    auto_emotion=true; shift ;;
    --similarity-enh)  similarity_enh=true; shift ;;
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

if ! [[ -f "$TTS_SH" ]]; then
  echo "Error: tts skill not found at $TTS_SH" >&2
  echo "Make sure the tts skill is installed alongside characteristic-voice." >&2
  exit 1
fi

# ── Apply preset defaults (explicit flags take precedence) ───────────

if [[ -n "$preset" ]]; then
  _preset_emo="" _preset_speed=""
  resolve_preset "$preset"
  [[ -z "$emo" ]]   && emo="$_preset_emo"
  [[ -z "$speed" ]] && speed="$_preset_speed"
fi

# ── Build tts.sh speak command ───────────────────────────────────────

cmd=(bash "$TTS_SH" speak)

[[ -n "$text" ]]      && cmd+=(-t "$text")
[[ -n "$text_file" ]] && cmd+=(-f "$text_file")
cmd+=(-o "$output")

[[ -n "$voice" ]]     && cmd+=(-v "$voice")
[[ -n "$voice_id" ]]  && cmd+=(--voice-id "$voice_id")
[[ -n "$ref_audio" ]] && cmd+=(--ref-audio "$ref_audio")
[[ -n "$emo" ]]       && cmd+=(--emo "$emo")
[[ -n "$speed" ]]     && cmd+=(--speed "$speed")
[[ -n "$backend" ]]   && cmd+=(--backend "$backend")
[[ -n "$lang" ]]      && cmd+=(--lang "$lang")
[[ -n "$format" ]]    && cmd+=(--format "$format")
$auto_emotion         && cmd+=(--auto-emotion)
$similarity_enh       && cmd+=(--similarity-enh)

"${cmd[@]}"
