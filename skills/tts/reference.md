# TTS Reference

Detailed backend comparison, script arguments, voice lists, and API reference.

## Backend Comparison

| | Kokoro | Noiz |
|---|---|---|
| **Type** | Local CLI | Cloud API |
| **API key** | Not needed | Required (`tts.sh config --set-api-key`) |
| **Install** | Already installed on system | Auto (on first `speak`) |
| **Voice cloning** | No | Yes (reference audio) |
| **Emotion control** | No | Yes (`emo` + `/emotion-enhance`) |
| **Duration forcing** | No (ffmpeg atempo) | Yes (server-side) |
| **Voice blending** | Yes (`"v1:60,v2:40"`) | No |
| **Native file input** | EPUB, PDF, TXT | No (agent extracts text) |
| **Voices** | 40+ built-in (en/zh/ja/fr/it) | Custom cloned + built-in |
| **Streaming** | Yes (`--stream`) | No |
| **Max text/request** | No hard limit | 5000 chars |

## tts.sh Subcommands

### `tts.sh config`

| Flag | Required | Notes |
|------|----------|-------|
| `--set-api-key` | no | Save Noiz API key to `~/.noiz_api_key` |

Without flags, prints current key status. If no key is found, prints setup instructions.

### `tts.sh speak`

| Flag | Short | Required | Notes |
|------|-------|----------|-------|
| `--text` | `-t` | one of two | Text string |
| `--text-file` | `-f` | one of two | Text file path |
| `--voice` | `-v` | kokoro | Kokoro voice name |
| `--voice-id` | | noiz | Noiz voice ID (omit to see 5 available voices) |
| `--output` | `-o` | yes | Output audio path |
| `--format` | | no (wav) | `wav` or `mp3` |
| `--lang` | | no | Language code (kokoro: `cmn`, `en-us`, etc.; noiz: `zh`, `en`, etc.) |
| `--speed` | | no (1.0) | Speed multiplier |
| `--backend` | | no (auto) | `kokoro` or `noiz` |
| `--emo` | | no | Noiz: emotion JSON `'{"Joy":0.5}'` |
| `--auto-emotion` | | no | Noiz: call `/emotion-enhance` |
| `--ref-audio` | | no | Noiz: reference audio for cloning |
| `--similarity-enh` | | no | Noiz: enhance voice similarity |
| `--save-voice` | | no | Noiz: save cloned voice |

### `tts.sh render`

| Flag | Short | Required | Notes |
|------|-------|----------|-------|
| `--srt` | | yes | Input SRT file |
| `--voice-map` | | yes | Voice-map JSON |
| `--output` | `-o` | yes | Output audio path |
| `--backend` | | no (auto) | `kokoro` or `noiz` |
| `--auto-emotion` | | no | Noiz only |
| `--output-format` | | no (wav) | Per-segment format |
| `--work-dir` | | no (.tmp/tts) | Temp directory |

Any unknown flags are passed through to `render_timeline.py`.

### `tts.sh to-srt`

| Flag | Short | Required | Notes |
|------|-------|----------|-------|
| `--input` | `-i` | yes | Input text file |
| `--output` | `-o` | yes | Output SRT file |
| `--cps` | | no (4.0) | Characters per second (4 for Chinese, ~15 for English) |
| `--gap` | | no (300) | Gap between segments in ms |

## Voice Map Format

JSON with `default` (applied to all segments) and optional `segments` overrides.

`segments` keys: single index `"3"` or range `"5-8"`. Later keys override earlier ones.

### Kokoro fields

| Field | Notes |
|-------|-------|
| `voice` | Kokoro voice name (e.g. `zf_xiaoni`, `af_sarah`) |
| `lang` | Language code: `cmn`, `en-us`, `en-gb`, `ja`, `fr-fr`, `it` |
| `speed` | Speed multiplier |

### Noiz fields

| Field | Notes |
|-------|-------|
| `voice_id` | Noiz voice ID |
| `reference_audio` | Local audio file path for cloning |
| `emo` | Emotion dict: `{"Joy": 0.5, "Sadness": 0.2}` |
| `target_lang` | Language code: `zh`, `en`, `zh+en` |
| `similarity_enh` | Boolean — enhance voice similarity |
| `save_voice` | Boolean — save cloned voice for reuse |
| `quality_preset` | Integer (default 3) |
| `speed` | Speed multiplier |

## Kokoro Voices

| Language | Voices |
|----------|--------|
| 🇺🇸 en-us female | af_alloy, af_aoede, af_bella, af_heart, af_jessica, af_kore, af_nicole, af_nova, af_river, af_sarah, af_sky |
| 🇺🇸 en-us male | am_adam, am_echo, am_eric, am_fenrir, am_liam, am_michael, am_onyx, am_puck |
| 🇬🇧 en-gb | bf_alice, bf_emma, bf_isabella, bf_lily, bm_daniel, bm_fable, bm_george, bm_lewis |
| 🇨🇳 cmn | zf_xiaobei, zf_xiaoni, zf_xiaoxiao, zf_xiaoyi, zm_yunjian, zm_yunxi, zm_yunxia, zm_yunyang |
| 🇯🇵 ja | jf_alpha, jf_gongitsune, jf_nezumi, jf_tebukuro, jm_kumo |
| 🇫🇷 fr-fr | ff_siwis |
| 🇮🇹 it | if_sara, im_nicola |

Run `kokoro-tts --help-voices` for the latest list.

## Noiz API Reference

Base URL: `https://noiz.ai/v1` — Auth: `Authorization: YOUR_API_KEY` header.

Full API documentation: [root SKILL.md](../../SKILL.md).

Key endpoints:

- `POST /text-to-speech` — TTS with voice_id or file, emo, speed, duration
- `POST /emotion-enhance` — auto-annotate text with emotion tags
- `POST /voices` — clone a voice from file or URL
- `GET /voices` — list available voices
- `DELETE /voices/{id}` — delete a voice
