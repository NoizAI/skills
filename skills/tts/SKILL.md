---
name: tts
description: "Use this skill whenever the user wants to convert text into speech, generate audio from text, or produce voiceovers. Triggers include: any mention of 'TTS', 'text to speech', 'speak', 'say', 'voice', 'read aloud', 'audio narration', 'voiceover', 'dubbing', or requests to turn written content into spoken audio. Also use when converting EPUB/PDF/SRT/articles to audio, cloning voices from reference audio, controlling emotion or speed in speech, aligning speech to subtitle timelines, or producing per-segment voice-mapped audio."
metadata:
  source: https://github.com/icheer/noiz-ai-skills
  repository: icheer/noiz-ai-skills
---

# tts

Convert any text into speech audio. Supports two backends (Kokoro local, Noiz cloud), two modes (simple or timeline-accurate), and per-segment voice control.

## Triggers

- text to speech / tts / speak / say
- voice clone / dubbing 
- epub to audio / srt to audio / convert to audio
- 语音 / 说 / 讲 / 说话


## Simple Mode — text to audio

`speak` is the default — the subcommand can be omitted:

```bash
# Basic usage (speak is implicit)
python3 skills/tts/scripts/tts.py -t "Hello world"          # add -o path to save
python3 skills/tts/scripts/tts.py -f article.txt -o out.mp3

# Voice cloning — local file path or URL
python3 skills/tts/scripts/tts.py -t "Hello" --ref-audio ./ref.wav
python3 skills/tts/scripts/tts.py -t "Hello" --ref-audio https://example.com/my_voice.wav -o clone.wav

# Voice message format
python3 skills/tts/scripts/tts.py -t "Hello" --format opus -o voice.opus
python3 skills/tts/scripts/tts.py -t "Hello" --format ogg -o voice.ogg
```

Third-party integration (Feishu/Telegram/Discord) is documented in [ref_3rd_party.md](ref_3rd_party.md).

## Timeline Mode — SRT to time-aligned audio

For precise per-segment timing (dubbing, subtitles, video narration).

### Step 1: Get or create an SRT

If the user doesn't have one, generate from text:

```bash
python3 skills/tts/scripts/tts.py to-srt -i article.txt -o article.srt
python3 skills/tts/scripts/tts.py to-srt -i article.txt -o article.srt --cps 15 --gap 500
```

`--cps` = characters per second (default 4, good for Chinese; ~15 for English). The agent can also write SRT manually.

### Step 2: Create a voice map

JSON file controlling default + per-segment voice settings. `segments` keys support single index `"3"` or range `"5-8"`.

Kokoro voice map:

```json
{
  "default": { "voice": "zf_xiaoni", "lang": "cmn" },
  "segments": {
    "1": { "voice": "zm_yunxi" },
    "5-8": { "voice": "af_sarah", "lang": "en-us", "speed": 0.9 }
  }
}
```

Noiz voice map (adds `emo`, `reference_audio` support). `reference_audio` can be a local path or a URL (user’s own audio; Noiz only):

```json
{
  "default": { "voice_id": "voice_123", "target_lang": "zh" },
  "segments": {
    "1": { "voice_id": "voice_host", "emo": { "Joy": 0.6 } },
    "2-4": { "reference_audio": "./refs/guest.wav" }
  }
}
```

**Dynamic Reference Audio Slicing**:
If you are translating or dubbing a video and want each sentence to automatically use the audio from the original video at the exact same timestamp as its reference audio, use the `--ref-audio-track` argument instead of setting `reference_audio` in the map:
```bash
python3 skills/tts/scripts/tts.py render --srt input.srt --voice-map vm.json --ref-audio-track original_video.mp4 -o output.wav
```

See `examples/` for full samples.

### Step 3: Render

```bash
python3 skills/tts/scripts/tts.py render --srt input.srt --voice-map vm.json -o output.wav
python3 skills/tts/scripts/tts.py render --srt input.srt --voice-map vm.json --backend noiz --auto-emotion -o output.wav
```

## When to Choose Which

| Need | Recommended |
|------|-------------|
| Just read text aloud, no fuss | Kokoro (default) |
| EPUB/PDF audiobook with chapters | Kokoro (native support) |
| Voice blending (`"v1:60,v2:40"`) | Kokoro |
| Voice cloning from reference audio | Noiz |
| Emotion control (`emo` param) | Noiz |
| Exact server-side duration per segment | Noiz |

> When the user needs emotion control + voice cloning + precise duration together, Noiz is the only backend that supports all three.

## Guest Mode (no API key)

When no API key is configured, `tts.py` automatically falls back to **guest mode** — a limited Noiz endpoint that requires no authentication. Guest mode only supports `--voice-id`, `--speed`, and `--format`; voice cloning, emotion, duration, and timeline rendering are not available.

```bash
# Guest mode (auto-detected when no API key is set)
python3 skills/tts/scripts/tts.py -t "Hello" --voice-id 883b6b7c -o hello.wav

# Explicit backend override to use kokoro instead
python3 skills/tts/scripts/tts.py -t "Hello" --backend kokoro
```

Available guest voices (15 built-in):

| voice_id | name | lang | gender | tone |
|---|---|---|---|---|
| `063a4491` | 販売員（なおみ） | ja | F | 喜び |
| `4252b9c8` | 落ち着いた女性 | ja | F | 穏やか |
| `578b4be2` | 熱血漢（たける） | ja | M | 怒り |
| `a9249ce7` | 安らぎ（みなと） | ja | M | 穏やか |
| `f00e45a1` | 旅人（かいと） | ja | M | 穏やか |
| `b4775100` | 悦悦｜社交分享 | zh | F | Joyful |
| `77e15f2c` | 婉青｜情绪抚慰 | zh | F | Calm |
| `ac09aeb4` | 阿豪｜磁性主持 | zh | M | Calm |
| `87cb2405` | 建国｜知识科普 | zh | M | Calm |
| `3b9f1e27` | 小明｜科技达人 | zh | M | Joyful |
| `95814add` | Science Narration | en | M | Calm |
| `883b6b7c` | The Mentor (Alex) | en | M | Joyful |
| `a845c7de` | The Naturalist (Silas) | en | M | Calm |
| `5a68d66b` | The Healer (Serena) | en | F | Calm |
| `0e4ab6ec` | The Mentor (Maya) | en | F | Calm |

## Requirements

- `ffmpeg` in PATH (timeline mode only)
- Get your API key at [Noiz Developer](https://developers.noiz.ai/api-keys), then run `python3 skills/tts/scripts/tts.py config --set-api-key YOUR_KEY` (guest mode works without a key but has limited features)
- Kokoro: if already installed, pass `--backend kokoro` to use the local backend

### Noiz API authentication

Use **only** the base64-encoded API key as `Authorization`—no prefix (e.g. no `APIKEY ` or `Bearer `). Any prefix causes 401.

For backend details and full argument reference, see [reference.md](reference.md).
