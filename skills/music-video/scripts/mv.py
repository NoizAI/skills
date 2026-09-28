#!/usr/bin/env python3
"""Prepare and assemble a local music video.

Commands:
    python3 mv.py init --project ./mv --song ./song.mp3 --mode code
    python3 mv.py analyze --project ./mv
    python3 mv.py inspect --project ./mv
    python3 mv.py assemble --project ./mv
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import NoReturn


FPS = 24
TEMPLATE_REPO = "https://github.com/JohnHeibel/ClaudeAnimationBase.git"
TEMPLATE_COMMIT = "0ac8bf2b31942376cb6b8c4074715595d512acd2"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
ASPECTS = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:3": (1440, 1080),
}
SCENE_FIELDS = {
    "id", "start_frame", "end_frame", "source", "source_start",
    "fit", "transition", "fade_frames",
}
OVERLAY_FIELDS = {
    "id", "source", "source_start", "start_frame", "end_frame",
    "x", "y", "width", "height",
}
ID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")


class CommandError(Exception):
    """A tool exited with an error that the caller can report."""


def die(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        die(f"{name} is required but was not found on PATH")


def execute(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None,
            timeout: int = 600) -> str:
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise CommandError(f"command not found: {cmd[0]}") from None
    except subprocess.TimeoutExpired:
        raise CommandError(f"timed out after {timeout}s: {cmd[0]}") from None
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        if len(detail) > 2000:
            detail = detail[-2000:]
        raise CommandError(f"{cmd[0]} failed ({completed.returncode}): {detail}")
    return completed.stdout


def run(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None,
        timeout: int = 600) -> str:
    try:
        return execute(cmd, cwd=cwd, env=env, timeout=timeout)
    except CommandError as exc:
        die(str(exc))


def resolve_inside(project: Path, raw: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        die("a project path is empty")
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        die(f"path must stay inside the project: {raw}")
    path = (project / candidate).resolve()
    root = project.resolve()
    if path != root and root not in path.parents:
        die(f"path must stay inside the project: {raw}")
    return path


def load_project(raw: str) -> tuple[Path, dict]:
    project = Path(raw).expanduser().resolve()
    meta_path = project / "project.json"
    if not meta_path.is_file():
        die(f"not a music-video project: {project}")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"project.json is invalid: {exc}")
    if not isinstance(meta, dict):
        die("project.json must be an object")
    return project, meta


def probe(path: Path) -> dict:
    raw = execute([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ])
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CommandError(f"ffprobe returned invalid JSON for {path.name}: {exc}") from exc
    if not isinstance(info, dict):
        raise CommandError(f"ffprobe returned unexpected output for {path.name}")
    return info


def probe_or_die(path: Path) -> dict:
    try:
        return probe(path)
    except CommandError as exc:
        die(str(exc))


def stream(info: dict, kind: str) -> dict | None:
    for item in info.get("streams", []):
        if item.get("codec_type") == kind:
            return item
    return None


def media_duration(info: dict) -> float:
    raw = (info.get("format") or {}).get("duration")
    if raw in (None, "N/A"):
        return 0.0
    return float(raw)


def stream_duration(info: dict, kind: str) -> float:
    item = stream(info, kind)
    raw = None if item is None else item.get("duration")
    if raw in (None, "N/A"):
        return media_duration(info)
    return float(raw)


def parse_rate(raw: str | None) -> float:
    if not raw or raw == "0/0":
        return 0.0
    if "/" in raw:
        numerator, denominator = raw.split("/", 1)
        denominator_value = float(denominator)
        return float(numerator) / denominator_value if denominator_value else 0.0
    return float(raw)


def frame_count_for(duration: float, fps: int = FPS) -> int:
    scaled = duration * fps
    nearest = round(scaled)
    if abs(scaled - nearest) <= 1e-6:
        return int(nearest)
    return int(math.ceil(scaled - 1e-9))


def as_object(value, label: str) -> dict:
    if not isinstance(value, dict):
        die(f"{label} must be an object")
    return value


def as_int(value, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        die(f"{label} must be an integer")
    return value


def as_number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        die(f"{label} must be a number")
    return float(value)


def as_identifier(value, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 64:
        die(f"{label} must be a short identifier")
    if not value[0].isalnum() or any(char not in ID_CHARS for char in value):
        die(f"{label} must match [A-Za-z0-9][A-Za-z0-9_-]*")
    return value


def reject_unknown(value: dict, allowed: set[str], label: str) -> None:
    extra = sorted(set(value) - allowed)
    if extra:
        die(f"{label} has unknown fields: {', '.join(extra)}")


def media_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    die(f"unsupported media type: {path.name}")


def refuse_project_path(project: Path) -> None:
    home = Path.home().resolve()
    skill_dir = Path(__file__).resolve().parents[1]
    if project == home or project == Path(project.anchor):
        die("refusing to initialize the home directory or filesystem root")
    if project == skill_dir or skill_dir in project.parents:
        die("create the project outside the music-video skill directory")


def copy_tree(source: Path, destination: Path) -> int:
    copied = 0
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if not path.is_file() or any(part.startswith(".") for part in relative.parts):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
    return copied


def clone_template(destination: Path) -> None:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    run(["git", "init"], cwd=destination, env=env)
    run(["git", "remote", "add", "origin", TEMPLATE_REPO], cwd=destination, env=env)
    run(["git", "fetch", "--depth", "1", "origin", TEMPLATE_COMMIT], cwd=destination,
        env=env, timeout=180)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=destination, env=env)
    commit = run(["git", "rev-parse", "HEAD"], cwd=destination, env=env).strip()
    if commit != TEMPLATE_COMMIT:
        die(f"template commit mismatch: expected {TEMPLATE_COMMIT}, got {commit}")
    if not (destination / "ANIMATION_GUIDE.md").is_file() or not (destination / "LICENSE").is_file():
        die("template checkout is missing ANIMATION_GUIDE.md or LICENSE")


def cmd_init(args: argparse.Namespace) -> None:
    require_tool("ffmpeg")
    project = Path(args.project).expanduser().resolve()
    refuse_project_path(project)
    if project.exists():
        die(f"project already exists: {project}")
    if args.aspect not in ASPECTS:
        die(f"aspect must be one of: {', '.join(ASPECTS)}")

    song = Path(args.song).expanduser().resolve()
    if not song.is_file():
        die(f"song not found: {song}")
    if song.suffix.lower() not in AUDIO_EXTENSIONS:
        die(f"unsupported song type: {song.suffix or '(none)'}")

    lyrics = None
    if args.lyrics:
        lyrics = Path(args.lyrics).expanduser().resolve()
        if not lyrics.is_file():
            die(f"lyrics not found: {lyrics}")
    assets = None
    if args.assets:
        assets = Path(args.assets).expanduser().resolve()
        if not assets.is_dir():
            die(f"assets directory not found: {assets}")
    if args.mode == "code" and shutil.which("git") is None:
        die("git is required for code mode")

    width, height = ASPECTS[args.aspect]
    project.mkdir(parents=True)
    try:
        for relative in ("audio", "assets", "docs", "output", "output/sheets", "output/pilots"):
            (project / relative).mkdir(parents=True, exist_ok=True)
        song_rel = f"audio/source{song.suffix.lower()}"
        shutil.copy2(song, project / song_rel)
        lyrics_rel = None
        if lyrics is not None:
            lyrics_rel = "lyrics.srt" if lyrics.suffix.lower() == ".srt" else "lyrics.txt"
            shutil.copy2(lyrics, project / lyrics_rel)
        copied = copy_tree(assets, project / "assets") if assets is not None else 0
        if args.mode == "code":
            animation = project / "animation"
            animation.mkdir()
            clone_template(animation)

        meta = {
            "mode": args.mode,
            "title": args.title or project.name,
            "fps": FPS,
            "aspect": args.aspect,
            "width": width,
            "height": height,
            "song": song_rel,
        }
        if lyrics_rel:
            meta["lyrics"] = lyrics_rel
        if args.mode == "code":
            meta["template"] = {
                "repo": TEMPLATE_REPO,
                "commit": TEMPLATE_COMMIT,
                "path": "animation",
                "license": "MIT",
            }
        (project / "project.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (project / "docs" / "PROGRESS.md").write_text(
            "# Progress\n\n- [x] Project initialized\n", encoding="utf-8")
    except BaseException:
        shutil.rmtree(project, ignore_errors=True)
        raise

    print(f"initialized {project} ({args.mode})")
    if assets is not None:
        print(f"assets copied: {copied}")
    print(f"next: python3 {Path(__file__).resolve()} analyze --project {project}")


def analyze_wav(path: Path, fps: int = FPS) -> dict:
    try:
        import numpy as np
    except ImportError:
        die("numpy is required for analyze. Run: uv pip install 'numpy>=2,<3'")

    with wave.open(str(path), "rb") as handle:
        if handle.getsampwidth() != 2:
            die("internal WAV must be 16-bit PCM")
        rate = handle.getframerate()
        channels = handle.getnchannels()
        raw = handle.readframes(handle.getnframes())
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32)
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    samples = np.ascontiguousarray(samples / 32768.0)
    if len(samples) < 4096:
        die("song is too short to analyze")
    duration = len(samples) / rate

    hop = 256
    n_fft = 2048
    window = np.hanning(n_fft).astype(np.float32)
    count = 1 + (len(samples) - n_fft) // hop
    framed = np.lib.stride_tricks.as_strided(
        samples,
        shape=(count, n_fft),
        strides=(samples.strides[0] * hop, samples.strides[0]),
    )
    magnitude = np.abs(np.fft.rfft(framed * window, axis=1)).astype(np.float32).T
    freqs = np.fft.rfftfreq(n_fft, 1.0 / rate)
    times = (np.arange(count) * hop + n_fft / 2) / rate

    def flux(low_hz: float, high_hz: float):
        low = int(np.searchsorted(freqs, low_hz))
        high = max(low + 1, int(np.searchsorted(freqs, high_hz)))
        band = np.log1p(100.0 * magnitude[low:high])
        delta = np.diff(band, axis=1, prepend=band[:, :1])
        return np.maximum(delta, 0).sum(axis=0)

    def normalize(values):
        centered = values - np.median(values)
        scale = float(np.percentile(centered, 95))
        return np.clip(centered / (abs(scale) + 1e-9), 0, None)

    full = normalize(flux(20, rate / 2))
    low = normalize(flux(20, 150))
    envelope = full + low
    frame_rate = rate / hop

    def comb_score(period: float, phase: float) -> float:
        hits = np.arange(phase, float(times[-1]), period)
        index = np.round((hits - float(times[0])) * frame_rate).astype(int)
        index = index[(index >= 0) & (index < len(envelope))]
        if len(index) == 0:
            return 0.0
        return float(envelope[index].mean())

    def best_period(periods) -> float:
        scores = []
        for period in periods:
            phases = np.linspace(0, float(period), 24, endpoint=False)
            scores.append(max(comb_score(float(period), float(phase)) for phase in phases))
        return float(periods[int(np.argmax(np.asarray(scores)))])

    coarse = 60.0 / np.arange(70, 181, 0.5)
    period = best_period(coarse)
    fine_bpms = np.arange((60.0 / period) - 0.4, (60.0 / period) + 0.4, 0.02)
    fine_bpms = fine_bpms[(fine_bpms >= 60) & (fine_bpms <= 200)]
    if len(fine_bpms) == 0:
        die("could not estimate a tempo")
    period = best_period(60.0 / fine_bpms)
    phases = np.linspace(0, period, 96, endpoint=False)
    phase = float(phases[int(np.argmax([comb_score(period, float(item)) for item in phases]))])

    beats = []
    snap = max(1, int(round(0.04 * frame_rate)))
    for number, beat_time in enumerate(np.arange(phase, float(times[-1]), period)):
        center = int(round((beat_time - float(times[0])) * frame_rate))
        left = max(center - snap, 0)
        right = min(center + snap + 1, len(envelope))
        if left >= right:
            continue
        peak = left + int(np.argmax(envelope[left:right]))
        beats.append({
            "t": round(float(times[peak]), 3),
            "n": number,
            "strength": round(float(full[peak]), 2),
            "low": round(float(low[peak]), 2),
        })
    if not beats:
        die("no beats found in the song")

    bar = int(np.argmax([
        sum(beat["low"] for beat in beats if beat["n"] % 4 == phase_index)
        for phase_index in range(4)
    ]))
    for beat in beats:
        beat["bar_pos"] = (beat["n"] - bar) % 4
        beat["f"] = int(round(beat["t"] * fps))

    onsets = []
    last_onset = -1.0
    for index in range(1, len(envelope) - 1):
        if envelope[index] < 1.0:
            continue
        if envelope[index] < envelope[index - 1] or envelope[index] < envelope[index + 1]:
            continue
        stamp = float(times[index])
        if stamp - last_onset < 0.09:
            continue
        onsets.append({
            "t": round(stamp, 3),
            "f": int(round(stamp * fps)),
            "strength": round(float(full[index]), 2),
            "low": round(float(low[index]), 2),
        })
        last_onset = stamp

    step = int(0.25 * rate)
    loudness = []
    for start in range(0, len(samples) - step + 1, step):
        chunk = samples[start:start + step]
        rms = float(np.sqrt(np.mean(chunk * chunk)) + 1e-9)
        loudness.append({
            "t": round(start / rate, 2),
            "db": round(20 * math.log10(rms), 1),
        })
    downbeat = next((beat["t"] for beat in beats if beat["bar_pos"] == 0), round(phase, 3))
    return {
        "duration": round(duration, 3),
        "fps": fps,
        "frame_count": frame_count_for(duration, fps),
        "bpm": round(60.0 / period, 2),
        "period": round(float(period), 4),
        "phase": round(phase, 4),
        "first_downbeat": downbeat,
        "beats": beats,
        "onsets": onsets,
        "loudness": loudness,
        "tempo_note": "Steady-grid estimate. Confirm section boundaries when the tempo changes.",
    }


def cmd_analyze(args: argparse.Namespace) -> None:
    require_tool("ffmpeg")
    project, meta = load_project(args.project)
    song = resolve_inside(project, meta.get("song", ""))
    if not song.is_file():
        die(f"song not found: {meta.get('song')}")
    source_duration = media_duration(probe_or_die(song))
    if source_duration <= 0:
        die("the source song has no duration")
    wav_path = project / "audio" / "song.wav"
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(song), "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le",
        str(wav_path),
    ])
    report = analyze_wav(wav_path)
    report["duration"] = round(source_duration, 3)
    report["frame_count"] = frame_count_for(source_duration)
    destination = project / "audio" / "analysis.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"analysis: {destination}")
    print(f"duration: {report['duration']:.3f}s")
    print(f"frames: {report['frame_count']}")
    print(f"bpm: {report['bpm']}")
    print(f"first_downbeat: {report['first_downbeat']:.3f}s")


def sheet_name(relative: Path) -> str:
    flat = "__".join(relative.with_suffix("").parts)
    cleaned = "".join(char if char.isalnum() or char in "-_" else "_" for char in flat)
    return cleaned[:120] or "asset"


def cmd_inspect(args: argparse.Namespace) -> None:
    require_tool("ffprobe")
    require_tool("ffmpeg")
    project, _meta = load_project(args.project)
    root = resolve_inside(project, args.assets or "assets")
    if not root.is_dir():
        die(f"assets directory not found: {root.relative_to(project)}")

    sheets = project / "output" / "sheets"
    sheets.mkdir(parents=True, exist_ok=True)
    entries = []
    failures = 0
    files = [path for path in root.rglob("*") if path.is_file() and not any(
        part.startswith(".") for part in path.relative_to(root).parts)]
    if not files:
        print("no visual assets")

    for path in sorted(files):
        relative = path.relative_to(project).as_posix()
        suffix = path.suffix.lower()
        entry = {"path": relative}
        if suffix in AUDIO_EXTENSIONS:
            entry["kind"] = "audio"
            entries.append(entry)
            continue
        if suffix not in IMAGE_EXTENSIONS and suffix not in VIDEO_EXTENSIONS:
            continue
        try:
            info = probe(path)
        except CommandError as exc:
            entry["error"] = str(exc)
            entries.append(entry)
            failures += 1
            continue
        visual = stream(info, "video")
        if visual is None:
            entry["error"] = "no video stream"
            entries.append(entry)
            failures += 1
            continue
        entry.update({
            "kind": "image" if suffix in IMAGE_EXTENSIONS else "video",
            "width": visual.get("width"),
            "height": visual.get("height"),
        })
        if entry["kind"] == "video":
            duration = media_duration(info)
            entry["duration"] = round(duration, 3)
            entry["fps"] = round(parse_rate(visual.get("avg_frame_rate")), 3)
            destination = sheets / f"{sheet_name(path.relative_to(root))}.jpg"
            try:
                write_contact_sheet(path, destination, duration)
            except CommandError as exc:
                entry["error"] = str(exc)
                failures += 1
            else:
                entry["contact_sheet"] = destination.relative_to(project).as_posix()
                print(f"sheet: {entry['contact_sheet']}")
        entries.append(entry)

    report = {"assets": entries}
    destination = project / "docs" / "inspect.json"
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"inspect: {destination}")
    if failures:
        die(f"{failures} asset(s) could not be inspected")


def write_contact_sheet(video: Path, destination: Path, duration: float, frames: int = 12) -> None:
    if duration <= 0:
        raise CommandError(f"{video.name} has no duration")
    columns = 4
    rows = math.ceil(frames / columns)
    rate = frames / duration
    destination.parent.mkdir(parents=True, exist_ok=True)
    execute([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(video),
        "-vf", f"fps={rate:.8f},scale=320:-2,tile={columns}x{rows}",
        "-frames:v", "1",
        str(destination),
    ])


def load_timeline(project: Path, raw: str | None) -> tuple[Path, dict]:
    path = resolve_inside(project, raw or "timeline.json")
    if not path.is_file():
        die(f"timeline not found: {path.relative_to(project)}")
    try:
        timeline = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"timeline is invalid JSON: {exc}")
    return path, as_object(timeline, "timeline")


def validate_timeline(project: Path, meta: dict, timeline: dict,
                      total_frames: int) -> tuple[list[dict], list[dict]]:
    reject_unknown(timeline, {"fps", "width", "height", "audio", "scenes", "overlays"}, "timeline")
    for key in ("fps", "width", "height", "audio", "scenes"):
        if key not in timeline:
            die(f"timeline is missing {key}")
    if timeline["fps"] != FPS:
        die("timeline fps must be 24")
    width = as_int(timeline["width"], "width")
    height = as_int(timeline["height"], "height")
    if not 2 <= width <= 3840 or width % 2 or not 2 <= height <= 3840 or height % 2:
        die("width and height must be even integers from 2 to 3840")
    if width != meta.get("width") or height != meta.get("height"):
        die("timeline dimensions must match project.json")
    audio = resolve_inside(project, timeline["audio"])
    source = resolve_inside(project, meta.get("song", ""))
    if audio != source:
        die("timeline audio must be the initialized source song")
    if not isinstance(timeline["scenes"], list) or not timeline["scenes"]:
        die("timeline needs at least one scene")

    cursor = 0
    seen = set()
    scenes = []
    for index, raw_scene in enumerate(timeline["scenes"], start=1):
        scene = as_object(raw_scene, f"scene {index}")
        reject_unknown(scene, SCENE_FIELDS, f"scene {index}")
        for key in ("id", "start_frame", "end_frame", "source"):
            if key not in scene:
                die(f"scene {index} is missing {key}")
        scene_id = as_identifier(scene["id"], f"scene {index} id")
        if scene_id in seen:
            die(f"duplicate scene id: {scene_id}")
        seen.add(scene_id)
        start = as_int(scene["start_frame"], f"{scene_id} start_frame")
        end = as_int(scene["end_frame"], f"{scene_id} end_frame")
        if start != cursor:
            die(f"{scene_id} must start at frame {cursor}, found {start}")
        if end <= start:
            die(f"{scene_id} must end after it starts")
        source_path = resolve_inside(project, scene["source"])
        if not source_path.is_file():
            die(f"{scene_id} source not found: {scene['source']}")
        kind = media_kind(source_path)
        source_start = as_number(scene.get("source_start", 0), f"{scene_id} source_start")
        if source_start < 0:
            die(f"{scene_id} source_start must be zero or greater")
        fit = scene.get("fit", "cover")
        if fit not in ("cover", "contain"):
            die(f"{scene_id} fit must be cover or contain")
        transition = scene.get("transition", "cut")
        if transition not in ("cut", "fade"):
            die(f"{scene_id} transition must be cut or fade")
        fade_frames = 0
        if transition == "fade":
            fade_frames = as_int(scene.get("fade_frames", 6), f"{scene_id} fade_frames")
            if not 1 <= fade_frames <= 48:
                die(f"{scene_id} fade_frames must be from 1 to 48")
            if fade_frames * 2 >= end - start:
                die(f"{scene_id} is too short for a {fade_frames}-frame fade")
        if kind == "video":
            info = probe_or_die(source_path)
            available = media_duration(info) - source_start
            needed = (end - start) / FPS
            if available + (1 / FPS) < needed:
                die(f"{scene_id} source is shorter than its frame range")
        scenes.append({
            "id": scene_id,
            "start_frame": start,
            "end_frame": end,
            "source": source_path,
            "source_start": source_start,
            "kind": kind,
            "fit": fit,
            "fade_frames": fade_frames,
        })
        cursor = end
    if cursor != total_frames:
        die(f"timeline ends at frame {cursor}; the song requires {total_frames}")

    overlays = []
    seen_overlays = set()
    for index, raw_overlay in enumerate(timeline.get("overlays", []), start=1):
        overlay = as_object(raw_overlay, f"overlay {index}")
        reject_unknown(overlay, OVERLAY_FIELDS, f"overlay {index}")
        for key in ("id", "source", "start_frame", "end_frame"):
            if key not in overlay:
                die(f"overlay {index} is missing {key}")
        overlay_id = as_identifier(overlay["id"], f"overlay {index} id")
        if overlay_id in seen_overlays:
            die(f"duplicate overlay id: {overlay_id}")
        seen_overlays.add(overlay_id)
        start = as_int(overlay["start_frame"], f"{overlay_id} start_frame")
        end = as_int(overlay["end_frame"], f"{overlay_id} end_frame")
        if start < 0 or end > total_frames or end <= start:
            die(f"{overlay_id} must lie inside the song and have a positive length")
        source_path = resolve_inside(project, overlay["source"])
        if not source_path.is_file():
            die(f"{overlay_id} source not found: {overlay['source']}")
        kind = media_kind(source_path)
        source_start = as_number(overlay.get("source_start", 0), f"{overlay_id} source_start")
        if source_start < 0:
            die(f"{overlay_id} source_start must be zero or greater")
        x = as_int(overlay.get("x", 0), f"{overlay_id} x")
        y = as_int(overlay.get("y", 0), f"{overlay_id} y")
        overlay_width = overlay.get("width")
        overlay_height = overlay.get("height")
        if (overlay_width is None) != (overlay_height is None):
            die(f"{overlay_id} needs both width and height, or neither")
        if overlay_width is not None:
            overlay_width = as_int(overlay_width, f"{overlay_id} width")
            overlay_height = as_int(overlay_height, f"{overlay_id} height")
            if overlay_width < 1 or overlay_height < 1:
                die(f"{overlay_id} width and height must be positive")
        if kind == "video":
            available = media_duration(probe_or_die(source_path)) - source_start
            needed = (end - start) / FPS
            if available + (1 / FPS) < needed:
                die(f"{overlay_id} source is shorter than its frame range")
        overlays.append({
            "id": overlay_id,
            "source": source_path,
            "kind": kind,
            "source_start": source_start,
            "start_frame": start,
            "end_frame": end,
            "x": x,
            "y": y,
            "width": overlay_width,
            "height": overlay_height,
        })
    return scenes, overlays


def fit_filter(width: int, height: int, fit: str) -> str:
    if fit == "contain":
        return (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black"
        )
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height}"
    )


def count_video_frames(path: Path) -> int:
    try:
        raw = execute([
            "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
            "-show_entries", "stream=nb_read_frames", "-print_format", "json", str(path),
        ], timeout=3600)
        info = json.loads(raw)
    except (CommandError, json.JSONDecodeError) as exc:
        die(f"could not count frames in {path.name}: {exc}")
    streams = info.get("streams") or []
    count = streams[0].get("nb_read_frames") if streams else None
    if count in (None, "N/A"):
        die(f"could not count frames in {path.name}")
    return int(count)


def ensure_frame_count(path: Path, frames: int, label: str) -> None:
    got = count_video_frames(path)
    if got == frames:
        return
    corrected = path.with_name(f"{path.stem}-corrected.mp4")
    if got > frames:
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(path), "-frames:v", str(frames), "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(corrected),
        ], timeout=3600)
    elif frames - got <= 2:
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(path),
            "-vf", f"tpad=stop_mode=clone:stop_duration={(frames - got) / FPS:.6f}",
            "-frames:v", str(frames), "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(corrected),
        ], timeout=3600)
    else:
        die(f"{label} produced {got} frames, needed {frames}. The source is shorter than the scene.")
    corrected.replace(path)
    got = count_video_frames(path)
    if got != frames:
        die(f"{label} produced {got} frames after correction, needed {frames}")


def render_segment(scene: dict, destination: Path, width: int, height: int) -> None:
    frames = scene["end_frame"] - scene["start_frame"]
    filters = [fit_filter(width, height, scene["fit"]), f"fps={FPS}", "format=yuv420p"]
    if scene["fade_frames"]:
        fade_seconds = scene["fade_frames"] / FPS
        fade_out = (frames / FPS) - fade_seconds
        filters.append(f"fade=t=in:st=0:d={fade_seconds:.6f}:color=black")
        filters.append(f"fade=t=out:st={fade_out:.6f}:d={fade_seconds:.6f}:color=black")
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    if scene["kind"] == "image":
        command += ["-loop", "1", "-framerate", str(FPS), "-i", str(scene["source"])]
    else:
        command += ["-i", str(scene["source"]), "-ss", f"{scene['source_start']:.6f}"]
    command += [
        "-vf", ",".join(filters), "-frames:v", str(frames), "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(destination),
    ]
    run(command, timeout=3600)
    ensure_frame_count(destination, frames, scene["id"])


def concat_segments(segments: list[Path], destination: Path) -> None:
    listing = destination.with_suffix(".txt")
    lines = []
    for segment in segments:
        escaped = segment.resolve().as_posix().replace("'", r"'\''")
        lines.append(f"file '{escaped}'")
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-fflags", "+genpts", "-f", "concat", "-safe", "0", "-i", str(listing),
        "-c", "copy", str(destination),
    ], timeout=3600)


def apply_overlays(base: Path, overlays: list[dict], destination: Path, frames: int) -> None:
    inputs = ["-i", str(base)]
    filters = []
    previous = "0:v"
    for index, overlay in enumerate(overlays, start=1):
        if overlay["kind"] == "image":
            inputs += ["-loop", "1", "-framerate", str(FPS), "-i", str(overlay["source"])]
        else:
            inputs += ["-i", str(overlay["source"])]
        steps = []
        if overlay["kind"] == "video":
            duration = (overlay["end_frame"] - overlay["start_frame"]) / FPS
            steps.append(f"trim=start={overlay['source_start']:.6f}:duration={duration:.6f}")
            steps.append("setpts=PTS-STARTPTS")
            steps.append(f"fps={FPS}")
        if overlay["width"] is not None:
            steps.append(f"scale={overlay['width']}:{overlay['height']}")
        steps.append("format=rgba")
        delay = overlay["start_frame"] / FPS
        steps.append(f"setpts=PTS+{delay:.6f}/TB")
        label = f"ov{index}"
        output = f"v{index}"
        filters.append(f"[{index}:v]{','.join(steps)}[{label}]")
        # Commas inside enable() must be escaped so ffmpeg does not split the filter.
        enable = f"between(n\\,{overlay['start_frame']}\\,{overlay['end_frame'] - 1})"
        filters.append(
            f"[{previous}][{label}]overlay={overlay['x']}:{overlay['y']}:"
            f"enable='{enable}':eof_action=pass[{output}]"
        )
        previous = output
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *inputs, "-filter_complex", ";".join(filters), "-map", f"[{previous}]",
        "-frames:v", str(frames), "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(destination),
    ], timeout=3600)
    ensure_frame_count(destination, frames, "overlay")


def cmd_assemble(args: argparse.Namespace) -> None:
    require_tool("ffmpeg")
    require_tool("ffprobe")
    project, meta = load_project(args.project)
    _timeline_path, timeline = load_timeline(project, args.timeline)
    song = resolve_inside(project, meta.get("song", ""))
    if not song.is_file():
        die(f"song not found: {meta.get('song')}")
    song_info = probe_or_die(song)
    if stream(song_info, "audio") is None:
        die("the source song has no audio stream")
    duration = media_duration(song_info)
    total_frames = frame_count_for(duration)
    if total_frames < 1:
        die("the source song has no duration")
    analysis_path = project / "audio" / "analysis.json"
    if analysis_path.is_file():
        try:
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            analysis = {}
        analyzed_frames = analysis.get("frame_count")
        if isinstance(analyzed_frames, int) and analyzed_frames != total_frames:
            print(
                f"warning: analysis.json has {analyzed_frames} frames; "
                f"the source song measures {total_frames}",
                file=sys.stderr,
            )

    scenes, overlays = validate_timeline(project, meta, timeline, total_frames)
    for scene in scenes:
        seconds = (scene["end_frame"] - scene["start_frame"]) / FPS
        print(f"{scene['id']} {scene['start_frame']}:{scene['end_frame']} {seconds:.3f}s")

    output = resolve_inside(project, args.output or "output/final.mp4")
    work = project / "output" / ".assemble"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    wrote_output = False
    try:
        segments = []
        for scene in scenes:
            segment = work / f"{scene['id']}.mp4"
            render_segment(scene, segment, timeline["width"], timeline["height"])
            segments.append(segment)
        picture = work / "picture.mp4"
        concat_segments(segments, picture)
        ensure_frame_count(picture, total_frames, "assembly")
        if overlays:
            composited = work / "composited.mp4"
            apply_overlays(picture, overlays, composited, total_frames)
            picture = composited
        output.parent.mkdir(parents=True, exist_ok=True)
        wrote_output = True
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(picture), "-i", str(song),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-avoid_negative_ts", "make_zero", "-movflags", "+faststart",
            str(output),
        ], timeout=3600)
        final_info = probe_or_die(output)
        if stream(final_info, "video") is None or stream(final_info, "audio") is None:
            die("final video is missing its picture or the original soundtrack")
        audio_duration = stream_duration(final_info, "audio")
        if abs(audio_duration - duration) > 0.35:
            die(
                f"final soundtrack is {audio_duration:.3f}s; "
                f"the original song is {duration:.3f}s"
            )
    except BaseException:
        if wrote_output:
            output.unlink(missing_ok=True)
        print(f"partial assembly left in {work}", file=sys.stderr)
        raise
    print(f"final: {output}")
    print(f"frames: {total_frames} (0:{total_frames})")
    print(f"audio: {meta['song']} ({duration:.3f}s)")
    print(f"scenes: {len(scenes)}")
    shutil.rmtree(work, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mv.py",
        description="Prepare and assemble a local music video. The original song remains the only soundtrack.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="Create an isolated project and copy its inputs")
    init.add_argument("--project", required=True, help="New project directory, outside this skill")
    init.add_argument("--song", required=True, help="Finished song to copy into the project")
    init.add_argument("--mode", required=True, choices=("code", "hybrid"))
    init.add_argument("--lyrics", help="Optional lyrics .txt or .srt")
    init.add_argument("--assets", help="Optional directory of stills and clips to copy")
    init.add_argument("--aspect", default="16:9", choices=tuple(ASPECTS))
    init.add_argument("--title", help="Title stored in project.json")
    init.set_defaults(func=cmd_init)

    analyze = commands.add_parser("analyze", help="Write beats, onsets, and loudness for the song")
    analyze.add_argument("--project", required=True)
    analyze.set_defaults(func=cmd_analyze)

    inspect = commands.add_parser("inspect", help="Probe local assets and write contact sheets")
    inspect.add_argument("--project", required=True)
    inspect.add_argument("--assets", help="Project-relative asset directory (default: assets)")
    inspect.set_defaults(func=cmd_inspect)

    assemble = commands.add_parser("assemble", help="Validate a timeline and mux the original song")
    assemble.add_argument("--project", required=True)
    assemble.add_argument("--timeline", help="Project-relative timeline (default: timeline.json)")
    assemble.add_argument("-o", "--output", help="Project-relative MP4 (default: output/final.mp4)")
    assemble.set_defaults(func=cmd_assemble)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
