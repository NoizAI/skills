---
name: music-video
description: "Build a music video from an existing song and lyrics, either as p5.js/p5.brush animation or by assembling local images and clips. Use when the user mentions a music video, MV, lyric video, visualizer, storyboard, 音乐视频, 歌词动画, or MV合成. Do not use it to compose the song, generate sound effects, or call an image or video generation API."
permissions:
  - filesystem
  - network
---

# music-video

Turn one finished song into a 24fps music video. The song is the master audio. Scene intervals cover it exactly once.

## Triggers

- music video / MV / lyric video / visualizer / storyboard
- 音乐视频 / MV合成 / 歌词动画 / 歌曲动画

## Capabilities

- `code`: initialize a pinned p5.js and p5.brush project, then animate the song in JavaScript.
- `hybrid`: inspect local character images, scene stills, and video clips, then assemble them. No image or video generation API is called.
- Local beat, onset, low-frequency, and loudness analysis for cut points and animation cues.
- Frame-exact assembly with the original song as the only soundtrack.

## Inputs

Required:

- `song`: local audio (`.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.aac`)
- `brief`: the visual idea, audience, and any required references
- `mode`: `code` or `hybrid`

Optional:

- `lyrics`: text or `.srt`. Required before storyboarding when the vocal timing matters.
- `assets`: directory of stills and clips for `hybrid`
- `aspect`: `16:9` (default), `9:16`, `1:1`, or `4:3`

If the user wants a song created first, use [text-to-music](../text-to-music/SKILL.md), then return here with the chosen file.

## Outputs

- `<project>/output/final.mp4`
- `docs/CREATIVE_BRIEF.md`, `docs/STORYBOARD.md`, `docs/TASKS.md`, and `docs/PROGRESS.md`
- `audio/analysis.json`, and `docs/inspect.json` when assets exist

## Workflow

Run `python3 skills/music-video/scripts/mv.py` from the repository root. If this skill is installed elsewhere, use the `scripts/mv.py` beside this file. Create the project outside the skill directory.

1. Choose `code` when the video is drawn in JavaScript. Choose `hybrid` when the user supplies stills or clips. Ask once when neither is clear.
2. Initialize an isolated project:

```bash
python3 skills/music-video/scripts/mv.py init \
  --project ./mv-project --song ./song.mp3 --lyrics ./lyrics.txt --mode code

python3 skills/music-video/scripts/mv.py init \
  --project ./mv-project --song ./song.mp3 --lyrics ./lyrics.srt \
  --assets ./clips --mode hybrid --aspect 16:9
```

3. Analyze the song. Treat tempo changes as approximate and confirm section boundaries from the audio:

```bash
python3 skills/music-video/scripts/mv.py analyze --project ./mv-project
```

4. Get lyric timing. If the user did not supply it, use [speech-to-text](../speech-to-text/SKILL.md) only when `NOIZ_API_KEY` or `~/.config/noiz/api_key` already exists. Never print the key. If neither exists, ask for lyrics or timestamps and do not upload the song.
5. Read [references/opus-5.5-prompt.md](references/opus-5.5-prompt.md) and follow it. Write the creative brief and storyboard before scene code or assembly. Review the opening and main peak before building the other chapters.
6. In `code` mode, read `<project>/animation/ANIMATION_GUIDE.md` before drawing. Set `PROJECT.bpm` and `PROJECT.offset` from `audio/analysis.json`. The pinned template canvas is 1920×1080; change `studio.html` and the renderer window before using another aspect. Check motion with the template renderer:

```bash
node render.mjs --sheet=1,2,3 --out=../output/sheets/pilot.jpg
node render.mjs --strip=START:END --out=../output/sheets/pilot-motion.jpg
node render.mjs --clip --range=START:END --out=../output/pilots/opening.mp4
```

Run those inside `<project>/animation`. Pass `--chrome` or set `CHROME_PATH` when Chrome is not in a standard location. A contact sheet only screens layout. A `--strip`, or playback of the opening, peak, and ending, is the motion review.
7. In `hybrid` mode, inspect local media and stop if a required clip is missing. Do not generate a replacement.

```bash
python3 skills/music-video/scripts/mv.py inspect --project ./mv-project
```

8. Write `timeline.json` using [references/timeline.schema.json](references/timeline.schema.json). Intervals are inclusive at `start_frame` and exclusive at `end_frame`.
9. Assemble and probe the result:

```bash
python3 skills/music-video/scripts/mv.py assemble --project ./mv-project
```

## Timeline

```json
{
  "fps": 24,
  "width": 1920,
  "height": 1080,
  "audio": "audio/source.mp3",
  "scenes": [
    {
      "id": "opening",
      "start_frame": 0,
      "end_frame": 240,
      "source": "output/pilots/opening.mp4",
      "source_start": 0,
      "fit": "cover",
      "transition": "fade",
      "fade_frames": 6
    }
  ],
  "overlays": []
}
```

`fade` stays inside its own scene. Do not overlap scenes to create a crossfade.

## Completion

Finish only when every item is true:

- `[0, ceil(duration × 24))` is covered exactly once, with no gap or overlap.
- `final.mp4` has a video stream and the complete original song.
- The opening, main peak, and ending were reviewed in motion.
- The last story read has time to land.
- `docs/PROGRESS.md` has no open blocker.

## Security

`init --mode code` clones `JohnHeibel/ClaudeAnimationBase` at commit `0ac8bf2b31942376cb6b8c4074715595d512acd2` into the project. That template is MIT licensed. Analysis, inspection, rendering, and assembly stay local. Hybrid mode does not upload media and does not call an image, video, or music generation service.

## Requirements

- `ffmpeg` and `ffprobe`
- Python 3.9+
- `analyze`: `uv pip install 'numpy>=2,<3'`
- `code` mode: `git`, Node.js, and Google Chrome
- `hybrid` mode: local assets only

## Limitations

- This skill does not compose music, generate sound effects, or create images and video through an API.
- The beat grid assumes a mostly steady tempo.
- Watercolour fills in code mode can take seconds per frame without a discrete GPU. Ask the renderer to avoid those fills on integrated graphics.
- Assembly rejects a clip that is shorter than its scene instead of freezing or retiming it.
