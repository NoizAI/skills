---
name: text-to-music
description: "Use this skill whenever the user wants to generate a song or music with vocals from a text description and/or lyrics, or cover an existing song in a new style. Triggers include: any mention of 'make a song', 'generate music', 'text to music', 'compose', 'write and sing a song', 'jingle', 'theme song', 'birthday song', 'song with lyrics', 'cover', 'cover version', 'remake this song as jazz', 'sing this song in another style', or requests like 'turn these lyrics into a song' or 'make a lo-fi track about coffee'. Also use when the user supplies lyrics and wants them sung, wants a song modeled on a reference track, wants new lyrics sung over an existing melody, or wants to extract lyrics from a song for covering. Do NOT use for short sound effects (use sound-fx), speech/voiceover (use tts), or pure instrumental tracks (not supported)."
permissions:
  - network
  - filesystem
metadata: {"openclaw": {"primaryEnv": "NOIZ_API_KEY"}}
---

# text-to-music

Two ways to make a song with vocals + accompaniment, saved as MP3. Every request produces **two variants**.

- **Generate** — a new song from a music description plus lyrics.
- **Cover** — re-sing an existing song in a new style, keeping its melody. Lyrics can be the original (auto-recognized) or new ones.

## Triggers

- make a song / generate music / text to music / compose
- turn these lyrics into a song / sing this / jingle / theme song / birthday song
- cover this song / make a jazz version / remake in another style
- 写歌 / 生成音乐 / 作曲 / 唱首歌 / 歌词谱曲 / 翻唱 / 改编 / 换个风格唱

## Generate — new song from text

A request needs a **prompt** (the music description) and **exactly one** lyrics source:

```bash
# Let the server write lyrics from a theme
python3 skills/text-to-music/scripts/t2m.py "upbeat indie pop, bright guitars, 120 BPM" \
  --lyrics-prompt "a song about summer road trips with friends"

# Use your own lyrics (inline or from a file)
python3 skills/text-to-music/scripts/t2m.py "mandopop ballad, piano and strings" \
  --lyrics $'[Verse]\n窗外的雨停了\n[Chorus]\n我还在等你' --vocal-gender Female --title "雨停了"
python3 skills/text-to-music/scripts/t2m.py "lo-fi hip hop, mellow, vinyl crackle" \
  --lyrics-file song.txt --duration 120 -o chill.mp3

# Model the vocal/style on a reference song (local file ≤20 MB or public URL)
python3 skills/text-to-music/scripts/t2m.py "dreamy synth-pop" --lyrics-file song.txt --ref-audio ./ref.mp3
```

Output: `song_v1.mp3` and `song_v2.mp3` (or `<stem>_v1.mp3` / `<stem>_v2.mp3` with `-o`). When lyrics were written by the server, they are also saved to `<stem>_lyrics.txt`.

| Argument | Default | Description |
|----------|---------|-------------|
| `prompt` | required | Music description: genre, mood, instruments, tempo (≤1500 chars) |
| `--lyrics` / `-l` | — | Lyrics text; `[Verse]`, `[Chorus]`, `[Bridge]` markers help structure |
| `--lyrics-file` | — | UTF-8 `.txt` file with lyrics (≤64 KB) |
| `--lyrics-prompt` | — | Theme for server-side lyric writing |
| `--tags` | — | Style tags, comma-separated (≤50 chars) |
| `--negative-tags` | — | Styles to avoid |
| `--duration` / `-d` | auto | Target length hint: `60`, `120`, or `180` seconds. A hint, not a guarantee. |
| `--ref-audio` | — | Reference song, local path or public URL |

`--lyrics`, `--lyrics-file`, and `--lyrics-prompt` are mutually exclusive; one is required.

## Cover — re-sing an existing song

Needs the **source song**, **lyrics**, and a description of the new sound (`--style` and/or `--prompt`):

```bash
# Same lyrics, new style: recognize lyrics from the original, then cover it
python3 skills/text-to-music/scripts/t2m.py cover original.mp3 \
  --style "jazz, smoky female vocal" --recognize-lyrics -o jazz_cover.mp3

# New lyrics over the original melody, looser arrangement
python3 skills/text-to-music/scripts/t2m.py cover https://example.com/song.mp3 \
  --prompt "acoustic folk, fingerpicked guitar, intimate" --lyrics-file new_lyrics.txt \
  --adherence main_melody --vocal-gender Male

# Recognize lyrics only (to review or edit before covering)
python3 skills/text-to-music/scripts/t2m.py lyrics original.mp3 -o lyrics.txt
```

Recommended flow when the user wants to tweak lyrics: run `lyrics` → edit the file → `cover --lyrics-file`.

| Argument | Default | Description |
|----------|---------|-------------|
| `source` | required | Original song: local file (≤100 MB; mp3/wav/m4a/aac/flac/ogg) or public URL |
| `--style` / `-s` | — | Short style tags, e.g. `"rock, male vocal"` (≤50 chars) |
| `--prompt` / `-p` | — | Longer description of the cover's sound (≤1500 chars) |
| `--adherence` | `high` | `high` = follow the original arrangement closely; `main_melody` = keep only the main melody, more freedom |
| `--lyrics` / `-l` | — | Lyrics to sing |
| `--lyrics-file` | — | UTF-8 `.txt` file with lyrics (≤64 KB) |
| `--recognize-lyrics` | off | Transcribe the source's lyrics first and use them |
| `--output` / `-o` | `cover.mp3` | Output path; variants get `_v1` / `_v2` suffixes |

At least one of `--style` / `--prompt` is required; exactly one lyrics source is required.

## Shared Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--title` | — | Song title (≤80 chars) |
| `--vocal-gender` | — | `Male` or `Female` |
| `--vocal-timbre` | — | Free-form voice description, e.g. `"husky warm alto"` (≤50 chars) |
| `--output` / `-o` | `song.mp3` (`cover.mp3` for covers) | Output path; variants get `_v1` / `_v2` suffixes |
| `--no-wait` | off | Submit, print the job ID(s), then exit |
| `--poll-interval` | `10` | Seconds between status checks |
| `--timeout` | `1800` | Max seconds to wait (the job keeps running server-side) |
| `--api-key` | from env/config | Noiz API key (overrides stored key) |

## Resuming / Checking Jobs

Generation prints two `gen_product_id`s; a cover prints one `task_id`. If the wait times out or you used `--no-wait`, resume with:

```bash
python3 skills/text-to-music/scripts/t2m.py status <id_v1> <id_v2> -o song.mp3
python3 skills/text-to-music/scripts/t2m.py status --cover <task_id> -o cover.mp3
python3 skills/text-to-music/scripts/t2m.py status --cover <task_id> --no-wait   # just print status
```

Status goes `submitted` → `running` → `succeeded` / `failed`. Covers also report a `stage` (analysis runs before singing, so covers take longer). Download URLs expire after ~24h; re-run `status` for fresh ones.

## Writing Good Prompts

- **Prompt / style** = the sound: genre + mood + instrumentation + tempo. `"cinematic orchestral pop, soaring strings, 90 BPM, hopeful"`.
- **Lyrics**: keep sections short and label them. Chinese, English, and mixed lyrics all work.
- **Short songs**: for jingles or greetings, pass `-d 60` and write only a verse + chorus.
- **Covers**: pick `high` to keep the cover recognizable; pick `main_melody` for a bigger genre change.
- Not satisfied? Run again — each run gives two fresh variants.

## Cost

- **Songs and covers** are billed **once per job** (not per variant): `ceil(longest variant seconds) × 15` credits, charged after both variants succeed. A 2-minute song costs about 1,800 credits. If subscription credits don't cover the whole job, it is billed as pay-as-you-go at $0.00015/s. The script prints the charged amount on completion.
- **Lyrics recognition** (`lyrics` / `--recognize-lyrics`): 100 credits (or $0.001 pay-as-you-go), charged only when vocals are detected.

Rate limits: 5 submissions per minute per key per endpoint; status polling 60 per minute.

## Limitations

- Pure instrumental music is not supported — lyrics are always required.
- `--duration` is only a hint; actual length may differ. Covers follow the source's length.
- Prompts or lyrics containing sensitive content are rejected (`code=400`).

## Configuration

```bash
python3 skills/text-to-music/scripts/t2m.py config --set-api-key YOUR_KEY
# or
export NOIZ_API_KEY=YOUR_KEY
```

Get your API key at [developers.noiz.ai](https://developers.noiz.ai/api-keys).

## Requirements

- Python 3.6+
- `requests` package: `uv pip install requests`
- Noiz API key from [developers.noiz.ai](https://developers.noiz.ai/api-keys)

## Security & Data Disclosure

- **API key**: Stored in `~/.config/noiz/api_key` (permissions `0600`) or via `NOIZ_API_KEY` env variable.
- **Network**: Prompts, lyrics, and any reference/source audio (file upload or URL) are sent to `https://noiz.ai/v1/text-to-music` and `https://noiz.ai/v1/text-to-music/cover*`; job status is polled from the same endpoints. No other data is transmitted.
- **Output**: Generated MP3s (and lyrics text files) are downloaded from signed Noiz storage URLs and saved to the output path. No other files are modified.
