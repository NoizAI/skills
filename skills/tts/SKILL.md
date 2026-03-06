---
name: tts
description: "Use this skill whenever the user wants to convert text into speech, generate audio from text, or produce voiceovers. Triggers include: any mention of 'TTS', 'text to speech', 'speak', 'say', 'voice', 'read aloud', 'audio narration', 'voiceover', 'dubbing', or requests to turn written content into spoken audio. Also use when converting EPUB/PDF/SRT/articles to audio, cloning voices from reference audio, controlling emotion or speed in speech, aligning speech to subtitle timelines, or producing per-segment voice-mapped audio. If the user asks for an 'audiobook', 'podcast narration', 'voice clone', 'dubbed audio', or similar deliverable as a .wav/.mp3 audio file, use this skill. Do NOT use for music generation, sound effects, audio editing unrelated to speech, or general coding tasks unrelated to TTS."
---

# tts

Convert any text into speech audio. Supports two backends (Kokoro local, Noiz cloud), two modes (simple or timeline-accurate), and per-segment voice control.

## Triggers

- text to speech / tts / speak / say
- voice clone / dubbing 
- epub to audio / srt to audio / convert to audio
- 语音 / 说 / 讲 / 说话


## Simple Mode — text to audio

```bash
# speak (auto-detected when installed)
bash skills/tts/scripts/tts.sh speak -t "Hello world" # add -o path if you need to store result for later usage
bash skills/tts/scripts/tts.sh speak -f article.txt -o out.mp3

# Voice cloning
# Use your own reference audio: local file path or URL.
bash skills/tts/scripts/tts.sh speak -t "Hello" --ref-audio ./ref.wav
bash skills/tts/scripts/tts.sh speak -t "Hello" --ref-audio https://example.com/my_voice.wav -o clone.wav

# Telegram — sends opus via sendVoice
bash skills/tts/scripts/tts.sh speak_and_send_telegram \
  -t "Hello"

# Discord — 3-step upload + voice message (flags=8192)
bash skills/tts/scripts/tts.sh speak_and_send_discord \
  -t "Hello"

# Feishu — uploads opus, sends msg_type=audio
bash skills/tts/scripts/tts.sh speak_and_send_feishu \
  -t "你好呀"

```

All three senders read credentials from env variables first.

| Platform | Env variables | CLI Params | 
|----------|--------------|--------------|
| Feishu   | `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_CHAT_ID`, `FEISHU_TENANT_ACCESS_TOKEN` |  `chat-id` `app-id` `app-secret` |
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | `chat-id` `bot-token` |
| Discord  | `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID` | `channel-id` `bot-token` |

## Timeline Mode — SRT to time-aligned audio

For precise per-segment timing (dubbing, subtitles, video narration).

### Step 1: Get or create an SRT

If the user doesn't have one, generate from text:

```bash
bash skills/tts/scripts/tts.sh to-srt -i article.txt -o article.srt
bash skills/tts/scripts/tts.sh to-srt -i article.txt -o article.srt --cps 15 --gap 500
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
bash skills/tts/scripts/tts.sh render --srt input.srt --voice-map vm.json --ref-audio-track original_video.mp4 -o output.wav
```

See `examples/` for full samples.

### Step 3: Render

```bash
bash skills/tts/scripts/tts.sh render --srt input.srt --voice-map vm.json -o output.wav
bash skills/tts/scripts/tts.sh render --srt input.srt --voice-map vm.json --backend noiz --auto-emotion -o output.wav
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

## Requirements

- `ffmpeg` in PATH (timeline mode only)
- Noiz: get your API key at [developers.noiz.ai/api-keys](https://developers.noiz.ai/api-keys), then run `bash skills/tts/scripts/tts.sh config --set-api-key YOUR_KEY`
- Kokoro: if already installed, pass `--backend kokoro` to use the local backend

### Noiz API authentication

Use **only** the base64-encoded API key as `Authorization`—no prefix (e.g. no `APIKEY ` or `Bearer `). Any prefix causes 401.

For backend details and full argument reference, see [reference.md](reference.md).
