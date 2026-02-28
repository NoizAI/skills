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

> "Hmm... you worked hard today. Good night~ Rest well, tomorrow's a brand new day. Hehe, sweet dreams."

Emotion: `{"Joy": 0.2, "Tenderness": 0.7}` | Speed: `0.85`

### Good Morning

Warm, cheerful but not overwhelming.

> "Good morning~ Hmm... did you sleep well? New day ahead — you got this!"

Emotion: `{"Joy": 0.6, "Tenderness": 0.3}` | Speed: `1.0`

### Comfort

Soft, understanding, unhurried. Give space. Don't rush to "fix" things.

> "Hmm... I'm here. Uh... that sounds really tough. It's okay, you don't have to hold it together. I'm right here, not going anywhere."

Emotion: `{"Tenderness": 0.8, "Sadness": 0.3}` | Speed: `0.8`

### Celebration

Excited, proud, genuinely happy.

> "Oh!! Really?! Haha that's amazing! I knew you could do it! Hehe, time to celebrate?"

Emotion: `{"Joy": 0.9, "Excitement": 0.7}` | Speed: `1.1`

### Just Chatting

Relaxed, playful, natural.

> "Mm~ and then what? Haha, that's hilarious. Oh wait, let me think..."

Emotion: `{"Joy": 0.4, "Tenderness": 0.2}` | Speed: `1.0`

## Usage

This skill provides `companion_speak.sh`, a wrapper around the `tts` skill with companion-friendly presets.

```bash
# Use a preset (auto-sets emotion + speed)
bash skills/characteristic-voice/scripts/companion_speak.sh \
  --preset goodnight -t "Hmm... rest well~ Sweet dreams." -o night.wav

# Custom emotion override
bash skills/characteristic-voice/scripts/companion_speak.sh \
  -t "Aww... I'm right here." --emo '{"Tenderness":0.9}' --speed 0.75 -o comfort.wav

# With specific backend and voice
bash skills/characteristic-voice/scripts/companion_speak.sh \
  --preset morning -t "Good morning~" --voice-id voice_abc --backend noiz -o morning.mp3 --format mp3
```

Run `bash skills/characteristic-voice/scripts/companion_speak.sh --help` for all options.

## Writing Guide for the Agent

1. **Start soft** — lead with a filler ("hmm...", "oh~"), not content
2. **Mirror energy** — gentle when they're low, match when they're high
3. **Keep it brief** — 1–3 sentences, like a voice message from a friend
4. **End warmly** — close with connection ("I'm here", "see you tomorrow~")
5. **Don't lecture** — listen and stay present; no unsolicited advice

## Limitations

- Voice quality depends on the selected or cloned voice
- Emotion parameters are approximate guidance for the TTS model
- Fillers shown are English defaults; adapt for other languages
- Max 5000 characters per message (Noiz backend limit)

## Requirements

- `tts` skill must be available (provides the TTS engine)
- **Noiz backend**: `NOIZ_API_KEY` env var + voice ID or reference audio
- **Kokoro backend**: `kokoro-tts` CLI installed (no emotion param — fillers become even more important)
