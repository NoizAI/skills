# Unmute your intelligent bot
<img width="1760" height="608" alt="banner" src="https://github.com/user-attachments/assets/79efa5ae-e056-426c-ae67-362dd0f44963" />

English | [简体中文](./README.zh-CN.md)

Central repository for managing Skills to "human" vibe-talking.

## Install with `npx skills add`

```bash
# List skills from GitHub repository
npx skills add NoizAI/skills --list --full-depth

# Install a specific skill from GitHub repository
npx skills add NoizAI/skills --full-depth --skill tts -y

# Install from GitHub repository
npx skills add NoizAI/skills

# Local development (run in this repo directory)
npx skills add . --list --full-depth
```

## Available skills

| Name | Description | Documentation | Run command |
|------|-------------|---------------|-------------|
| tts | Convert text into speech with Kokoro or Noiz: simple mode, timeline-aligned rendering, precise duration control, and reference-audio voice cloning. | [SKILL.md](./skills/tts/SKILL.md) | `npx skills add NoizAI/skills --full-depth --skill tts -y` |
| video-translation | Translate and dub videos to another language: replace original audio with TTS aligned to subtitle timestamps, using per-segment reference audio from the source video. | [SKILL.md](./skills/video-translation/SKILL.md) | `npx skills add NoizAI/skills --full-depth --skill video-translation -y` |
| characteristic-voice | Make generated speech feel companion-like with fillers, emotional tuning, and preset speaking styles. | [SKILL.md](./skills/characteristic-voice/SKILL.md) | `npx skills add NoizAI/skills --full-depth --skill characteristic-voice -y` |

## Quick Verify

For example, characteristic-voice
```bash
bash skills/characteristic-voice/scripts/speak.sh \
  --preset comfort -t "Hmm... I'm right here." -o comfort.wav
```

## English Audio Demos

Sample outputs for quick listening (MP4 for inline playback):

- Breaking news style


https://github.com/user-attachments/assets/e1e75371-49e2-4858-9993-428d999c3723




- Mindful calm style  


https://github.com/user-attachments/assets/d2e6472d-9edf-449d-a5ee-51ad7e19a861





- Podcast intro style  


https://github.com/user-attachments/assets/e8f78ffa-7f12-4475-b1af-09161b3ee01b



- Startup hype style  


https://github.com/user-attachments/assets/0d3b8af9-2288-4a63-9246-2748ed232b0e



## Noiz API Key (recommended)

For the best experience (faster, emotion control, voice cloning), get your API key from [developers.noiz.ai](https://developers.noiz.ai):

```bash
bash skills/tts/scripts/tts.sh config --set-api-key YOUR_KEY
```

The key is persisted to `~/.noiz_api_key` and loaded automatically. Alternatively, pass `--backend kokoro` to use the local Kokoro backend.

## Contributing

For skill authoring rules, directory conventions, and PR guidance, see `CONTRIBUTING.md`.
