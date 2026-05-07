---
name: speech-to-text
description: "Use this skill whenever the user wants to transcribe audio to text, convert speech to text, or get a transcript from an audio or video file. Triggers include: any mention of 'transcribe', 'transcription', 'speech to text', 'STT', 'convert audio to text', 'what does this audio say', 'get transcript', 'subtitle generation', or requests to extract spoken words from a file. Also use when the user wants speaker identification from audio, timestamps for captions, or multilingual transcription."
permissions:
  - network
  - filesystem
metadata: {"openclaw": {"primaryEnv": "NOIZ_API_KEY"}}
---

# speech-to-text

Transcribe any audio file to text. Supports multilingual auto-detection, timestamps, and speaker labels.

## Triggers

- transcribe / transcript / transcription
- speech to text / STT / audio to text
- what does this audio say / convert audio
- 转录 / 语音转文字 / 识别音频

## Quick Start

```bash
# Transcribe with auto language detection
python3 skills/speech-to-text/scripts/stt.py audio.mp3

# Specify language explicitly
python3 skills/speech-to-text/scripts/stt.py interview.wav --language en

# Save transcript to file
python3 skills/speech-to-text/scripts/stt.py podcast.m4a -o transcript.txt

# Output full JSON (with timestamps and speaker labels)
python3 skills/speech-to-text/scripts/stt.py meeting.wav --json -o result.json
```

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `file` | required | Audio file to transcribe (mp3, wav, m4a, ogg, flac, aac, webm). Max 50 MB, max 10 min. |
| `--language` / `-l` | auto-detect | BCP-47 language code (e.g. `en`, `zh`, `ja`). Omit to auto-detect. |
| `--output` / `-o` | stdout | Path to save transcript text (or JSON if `--json` is set). |
| `--json` | off | Output full JSON response with timestamps and speaker labels. |
| `--api-key` | from env/config | Noiz API key (overrides stored key). |

## Output Format

Without `--json`, only the transcript text is printed:

```
Hello, welcome to today's podcast. We have a special guest joining us...
```

With `--json`, the full structured response is printed:

```json
{
  "language": "en",
  "transcript": "Hello, welcome to today's podcast...",
  "duration": 42.5,
  "segments": [
    {"text": "Hello, welcome to today's podcast.", "start": 0.0, "end": 3.2, "spk": 0},
    {"text": "We have a special guest joining us.", "start": 3.5, "end": 6.1, "spk": 0}
  ]
}
```

## Supported Languages

Common codes: `en` (English), `zh` (Chinese), `ja` (Japanese), `ko` (Korean), `es` (Spanish), `fr` (French), `de` (German), `pt` (Portuguese), `ru` (Russian), `ar` (Arabic). Omit `--language` to auto-detect.

## Configuration

```bash
# Save your API key once
python3 skills/speech-to-text/scripts/stt.py config --set-api-key YOUR_KEY

# Or set via environment variable
export NOIZ_API_KEY=YOUR_KEY
```

Get your API key at [developers.noiz.ai](https://developers.noiz.ai/api-keys).

## Pricing

Billed at **$0.0006 per second** of audio. A 10-minute file costs ~$0.36. New accounts include 10,000 free TTS characters; STT is billed separately.

## Security & data disclosure

- **Credential storage**: API key is saved to `~/.config/noiz/api_key` (permissions `0600`). `NOIZ_API_KEY` env var is also supported.
- **Network calls**: The audio file is uploaded to `https://noiz.ai/v1/speech-to-text` for transcription. No data is sent until you run the command.
- **File limits**: Max 50 MB per file, max 10 minutes (600 seconds) of audio.

## Requirements

- `requests` package: `pip install requests`
- Get your API key at [developers.noiz.ai](https://developers.noiz.ai/api-keys)
