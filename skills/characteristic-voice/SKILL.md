---
name: characteristic-voice
description: Make generated speech feel companion-like with fillers, emotional tuning, and preset speaking styles.
---

# characteristic-voice

Make your AI agent sound like a real companion — one who sighs, laughs, hesitates, and speaks with genuine feeling.

## Triggers

- characteristic voice
- companion voice
- talk like a friend
- good morning / good night voice
- comfort me
- cheer me up
- sound more human

## The Two Tricks

1. **Non-lexical fillers** — sprinkle in little human noises (hmm, haha, aww, heh) at natural pause points to make speech feel alive
2. **Emotion tuning** — adjust warmth, joy, sadness, tenderness to match the moment

## Filler Sounds Palette

| Sound | Feeling | Use for |
|-------|---------|---------|
| hmm... | Thinking, gentle acknowledgment | Comfort, pondering |
| ah... | Realization, soft surprise | Discoveries, transitions |
| uh... | Hesitation, empathy | Careful moments |
| heh / hehe | Playful, mischievous | Teasing, light moments |
| haha | Laughter | Joy, humor |
| aww | Tenderness, sympathy | Deep comfort |
| oh? / oh! | Surprise, attention | Reacting to news |
| pfft | Stifled laugh | Playful disbelief |
| whew | Relief | After tension |
| ~ (tilde) | Drawn out, melodic ending | Warmth, playfulness |

**Rules**: 2–4 fillers per short message max. Place at natural pauses — sentence starts, thought shifts. Use `...` after fillers for a beat of silence, `~` at word endings for warmth.

## Presets

### Good Night

Gentle, warm, slightly sleepy. Slow pace.

### Good Morning

Warm, cheerful but not overwhelming.

### Comfort

Soft, understanding, unhurried. Give space. Don't rush to "fix" things.

### Celebration

Excited, proud, genuinely happy.

### Just Chatting

Relaxed, playful, natural.

## Using a Character's Voice

When a user says something like *"speak in Hermione's voice"* or *"sound like Tony Stark"*, always find voice in `skills/characteristic-voice/` first. If none exists, *must* follow this one-time setup:

> 1. Find a YouTube video, movie clip where the character / person speaks clearly, prefer personal speech or voice memo.
> 2. Download the audio (e.g. via `yt-dlp`) and trim **1–10 seconds**.
> 3. Save the file into the skill folder, e.g. `skills/characteristic-voice/hermione.wav`.

pass it as `--ref-audio`:

```bash
bash skills/characteristic-voice/scripts/speak.sh \
  --preset goodnight -t "Hmm... rest well~ Sweet dreams." \
  --ref-audio skills/characteristic-voice/hermione.wav -o night.wav
```

The `--ref-audio` flag is forwarded to the Noiz backend for voice cloning (requires Noiz API key).

---

## Usage

This skill provides `speak.sh`, a wrapper around the `tts` skill with companion-friendly presets.

```bash
# Use a preset (auto-sets emotion + speed)
bash skills/characteristic-voice/scripts/speak.sh \
  --preset goodnight -t "Hmm... rest well~ Sweet dreams." -o night.wav

# Custom emotion override
bash skills/characteristic-voice/scripts/speak.sh \
  -t "Aww... I'm right here." --emo '{"Tenderness":0.9}' --speed 0.75 -o comfort.wav

# With specific backend and voice
bash skills/characteristic-voice/scripts/speak.sh \
  --preset morning -t "Good morning~" --voice-id voice_abc --backend noiz -o morning.mp3 --format mp3
```

Run `bash skills/characteristic-voice/scripts/speak.sh --help` for all options.

## Writing Guide for the Agent

1. **Start soft** — lead with a filler ("hmm...", "oh~"), not content
2. **Mirror energy** — gentle when they're low, match when they're high
3. **Keep it brief** — 1–3 sentences, like a voice message from a friend
4. **End warmly** — close with connection ("I'm here", "see you tomorrow~")
5. **Don't lecture** — listen and stay present; no unsolicited advice
