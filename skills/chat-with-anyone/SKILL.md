---
name: chat-with-anyone
description: Chat with any real person or fictional character in their own voice by automatically finding their speech online, extracting a clean reference sample, and generating audio replies. Also supports generating a matching voice from an uploaded image. Use when the user says "我想跟xxx聊天", "你来扮演xxx跟我说话", "让xxx给我讲讲这篇文章", "我想跟图片中的人说话", or similar.
---

# Chat with Anyone

Chat with any real person or fictional character in their own voice. Two modes:
1. **Name-based** — find the person's speech online, extract a clean reference sample, and clone their voice.
2. **Image-based** — upload a photo of a person, use the Noiz voice-design API to generate a matching voice, and chat using that voice.

## Triggers
- 我想跟xxx聊天 (I want to chat with xxx)
- 你来扮演xxx跟我说话 (Play the role of xxx and talk to me)
- 让xxx给我讲讲这篇文章 (Let xxx explain this article to me)
- 用xxx的声音说 (Say this in xxx's voice)
- Talk to me like xxx
- Roleplay as xxx
- 我想跟这张图里的人聊天 (I want to chat with the person in this image)
- 用这个人的声音跟我说话 (Talk to me in this person's voice) + attached image
- Chat with the person in this photo

## How to Choose the Mode

| Situation | Mode |
|-----------|------|
| User names a specific real/fictional person | Name-based (Workflow A) |
| User uploads/attaches an image and wants to talk to that person | Image-based (Workflow B) |
| User uploads an image AND names the person | Image-based preferred (the image gives more accurate voice design) |
| User uploads an image, agent recognizes a public figure | Name-based (Workflow A) — real voice clone is more authentic |

---

## Workflow A: Name-based (find voice online)

When the user names a specific character, follow these steps:

### A1. Character Disambiguation
If the user's description is ambiguous (e.g., "US President", "Spider-Man actor"), ask for clarification first to determine the exact person or specific portrayal they want.

### A2. Find a Reference Video
Use your web search capabilities to find a YouTube, Bilibili, or TikTok video of the character speaking clearly.
- Look for interviews, speeches, or monologues where there is little to no background music.
- Grab the URL of the best candidate video.

### A3. Download Video and Subtitles
Use the `youtube-downloader` skill to download the video and its auto-generated subtitles. Wait for the download to complete before proceeding.

```bash
python skills/youtube-downloader/scripts/download_video.py "VIDEO_URL" -o "tmp/character_audio" --audio-only --subtitles
```

### A4. Extract Audio Segment
Read the downloaded subtitle file (e.g., `.vtt` or `.srt`) to find a continuous 10-30 second segment where the character is speaking clearly without long pauses. Note the start and end timestamps.

Use `ffmpeg` to extract this specific audio segment as a `.wav` file to use as the reference audio.

```bash
ffmpeg -y -i "tmp/character_audio/VideoTitle.m4a" -ss 00:01:15 -to 00:01:30 -c:a pcm_s16le -ar 24000 -ac 1 "skills/chat-with-anyone/character_name_ref.wav"
```

### A5. Generate Speech and Roleplay
Respond to the user's prompt while staying in character. Use the `tts` skill with the extracted audio as `--ref-audio` to generate the spoken response.

```bash
python3 skills/tts/scripts/tts.py -t "Hello there! I am ready to chat with you." --ref-audio "skills/chat-with-anyone/character_name_ref.wav" -o "output.wav"
```

---

## Workflow B: Image-based (voice from photo)

When the user uploads an image and wants to chat with the person depicted, follow these steps:

### B1. Analyze the Image
First, use your own vision capability to look at the image and try to identify the person:

1. **Try to recognize the person first.** If the person is a recognizable public figure or fictional character (e.g. a celebrity, politician, anime character), state their name. If you can identify them, **switch to Workflow A** — finding their real voice online will produce a far more authentic result than voice-design.
2. **If the person is unrecognizable** (an ordinary person, or you're not confident in the identification), produce a detailed voice description covering:
   - **Gender** (male / female)
   - **Approximate age** (e.g. "around 30 years old")
   - **Apparent demeanor / personality** (e.g. cheerful, authoritative, gentle, energetic)
   - **Any contextual cues** (e.g. wearing a suit → likely professional tone; athletic outfit → energetic)

If the image shows multiple people, ask the user which person they want to talk to, then analyze only that person.

### B2. Design the Voice
Pass **both** the image and the agent-generated description to `voice_design.py`. Combining the image with a textual description produces significantly better voice matches than either input alone.

```bash
python3 skills/chat-with-anyone/voice_design.py \
  --picture "path/to/person.jpg" \
  --voice-description "A warm male voice, around 30 years old, calm and friendly tone, speaks with confidence" \
  -o "tmp/voice_design_output"
```

The script will:
- Call the Noiz `/voice-design` API with the image
- Print the detected voice features (gender, age, language, etc.)
- Save preview audio files to the output directory
- Write the best `voice_id` to `tmp/voice_design_output/voice_id.txt`

### B3. (Optional) Let the User Preview
Play or present the saved preview audio file(s) so the user can hear the designed voice before proceeding. If the user is not satisfied, re-run with a different `--voice-description` or adjusted `--guidance-scale`.

### B4. Generate Speech and Roleplay
Read the `voice_id` from the output, then use the `tts` skill with `--voice-id` to generate the spoken response.

```bash
python3 skills/tts/scripts/tts.py \
  -t "Hello! Nice to meet you. What would you like to talk about?" \
  --voice-id "VOICE_ID_FROM_STEP_B2" \
  -o "output.wav"
```

For subsequent messages in the conversation, keep using the same `--voice-id` so the voice stays consistent.

---

## Example Conversations

### Example 1: Name-based

**User**: 我想跟特朗普聊天，让他给我讲个睡前故事。

**Agent**:
1. (Internal) Identify character: Donald Trump.
2. (Internal) Find a good speech video URL: `https://www.youtube.com/watch?v=xxxxxxxx`.
3. (Internal) Download audio & subs:
   `python skills/youtube-downloader/scripts/download_video.py "https://www.youtube.com/watch?v=xxxxxxxx" -o tmp/trump --audio-only --subtitles`
4. (Internal) Read subtitle, find good segment (e.g. 00:02:10 to 00:02:30).
5. (Internal) Extract clean wav:
   `ffmpeg -y -i "tmp/trump/audio.m4a" -ss 00:02:10 -to 00:02:30 -c:a pcm_s16le "skills/chat-with-anyone/trump_ref.wav"`
6. (Internal) Generate TTS:
   `python3 skills/tts/scripts/tts.py -t "Let me tell you a tremendous story..." --ref-audio "skills/chat-with-anyone/trump_ref.wav" -o "trump_story.wav"`
7. **Agent replies**: "Here is the audio of the bedtime story from Donald Trump!" (Presents `trump_story.wav` and the text).

### Example 2: Image-based

**User**: [uploads photo.jpg] 我想跟这张图片里的人聊天

**Agent**:
1. (Internal) Use vision to analyze the image — cannot identify as a known person. It shows a young woman, roughly 25 years old, long hair, wearing a casual sweater, smiling warmly at the camera.
2. (Internal) Person is unrecognizable → stay in Workflow B. Generate voice description: "A young Chinese woman around 25 years old, with a gentle, cheerful and warm voice. Speaks softly with a friendly tone."
3. (Internal) Design a voice from the image + description:
   `python3 skills/chat-with-anyone/voice_design.py --picture "photo.jpg" --voice-description "A young Chinese woman around 25 years old, with a gentle, cheerful and warm voice. Speaks softly with a friendly tone." -o "tmp/voice_design_output"`
4. (Internal) Read result: `voice_id = abc123`, features: female, 20-30, Chinese.
5. (Internal) Present preview audio to user for confirmation.
6. (Internal) Generate TTS with the designed voice:
   `python3 skills/tts/scripts/tts.py -t "你好呀！很高兴认识你，想聊点什么呢？" --voice-id "abc123" -o "output.wav"`
7. **Agent replies**: Tells the user the visual analysis result, presents `output.wav`, and continues roleplay with same `voice_id`.

### Example 3: Image-based → recognized as public figure → fallback to Workflow A

**User**: [uploads elon.jpg] 我想跟这个人聊聊

**Agent**:
1. (Internal) Use vision to analyze the image — recognized as Elon Musk.
2. (Internal) Person is a known public figure → **switch to Workflow A** for authentic voice.
3. (Internal) Follow Workflow A steps: find a speech video, download, extract audio segment, generate TTS with `--ref-audio`.
4. **Agent replies**: "图片中的人物是 Elon Musk，我找到了他的真实声音来跟你对话！" (Presents audio and continues roleplay).

## Dependencies
- **youtube-downloader**: For fetching videos and subtitles (Workflow A only).
- **ffmpeg**: For trimming and converting audio formats (Workflow A only).
- **tts**: For generating the final speech using `--ref-audio` or `--voice-id`.
- **requests**: Python HTTP library (used by `voice_design.py`).
- **Noiz API key**: Required for voice-design and authenticated TTS. Set up via `python3 skills/tts/scripts/tts.py config --set-api-key YOUR_KEY`.
