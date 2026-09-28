# Opus 5.5 music-video run

Use this as the production contract for project `{{PROJECT}}`. Run the host at `xhigh` effort when that control exists. Do not add instructions to think harder, reveal private reasoning, or consume a token budget.

## Given

- Song: `{{SONG}}`
- Lyrics: `{{LYRICS}}`
- Mode: `{{MODE}}`
- Aspect: `{{ASPECT}}` at 24fps, `{{WIDTH}}×{{HEIGHT}}`
- Brief: `{{BRIEF}}`
- Analysis: `audio/analysis.json`
- Assets: `{{ASSETS}}`

The original song is the only soundtrack. Do not recut, retime, or replace it.

## Done

Done means `output/final.mp4` exists, `mv.py assemble` succeeded, and every completion check below passed. A progress summary is not done. Continue from `docs/TASKS.md` until then. Stop only when a required input is missing, the next action would exceed the approved brief, or a defect cannot be fixed without the user.

## Before drawing

Write these files and do not start scene work before the storyboard exists:

- `docs/CREATIVE_BRIEF.md`: one premise, the opening hook, the main peak, the ending, and one style paragraph. The style paragraph names the medium, materials, lighting, palette, and typography. Plan one recurring visual motif, where it returns changed, and at least one quiet beat. Keep the user's language in the lyrics and brief.
- `docs/STORYBOARD.md`: every scene from frame `0` through `ceil(duration × 24)`, using inclusive `start_frame` and exclusive `end_frame`. Adjacent scenes meet exactly. Each row has its lyric or cue, one focal action, its reads, and its source.
- `docs/TASKS.md`: the checklist. Tick items there.
- `docs/PROGRESS.md`: status only. Do not rewrite an approved storyboard to record progress.

Reject these specific failures while planning: captions that repeat the lyric, one constant speed, a tiny subject in an empty frame for the whole video, expression snaps, an abrupt start or stop, and an unrelated palette in each scene. Also reject cream backgrounds, italic accent words, `01 / 02 / 03` labels, monospace labels, and pill-shaped buttons when designing any on-screen interface.

## Pilots, then chapters

Build the opening and the main peak first. Review each in motion: in code mode use `render.mjs --strip` and a short `--clip`; in hybrid mode inspect the source and the rendered pilot range. A contact sheet only screens layout.

After both pilots are acceptable, build the remaining chapters. Independent chapters may run in parallel. Each worker receives its frame range, the style paragraph, the files it may edit, and the acceptance checks. A worker does not edit `docs/STORYBOARD.md`, `project.json`, the song, or another chapter. Report a shared-file defect instead of patching around it.

## Mode rules

Code mode: read `animation/ANIMATION_GUIDE.md` first. Set tempo and downbeat offset from `audio/analysis.json`. Do not reuse the bundled demo's story, setting, or shot structure. The user's brief overrides a guide ban only when it explicitly asks for the forbidden thing.

Hybrid mode: use only files already in the project. Do not call an image, video, music, or sound-generation API. If a required asset is missing, ask the user for it.

## Assembly

Write `timeline.json` that validates against [timeline.schema.json](timeline.schema.json). Fade inside a scene; do not overlap scenes. Then run:

```bash
python3 skills/music-video/scripts/mv.py assemble --project {{PROJECT}}
```

## Completion checks

- Every frame interval is covered once, with no gap or overlap.
- `final.mp4` plays the complete original song and no other audio.
- Opening, main peak, and ending were reviewed in motion.
- The ending holds its final read.
- The style paragraph still describes the finished video.
- `docs/PROGRESS.md` lists no open blocker.
