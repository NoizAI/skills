# tts

简体中文 | [English](./SKILL.md)

将任意文本转换为语音音频。支持两个后端（Kokoro 本地 / Noiz 云端）、两种模式（简单 / 时间轴）、逐句音色控制。

## Triggers

- 文本转语音 / tts / 朗读 / 生成音频
- 音色克隆 / 字幕配音 / srt 转音频
- epub 转音频 / markdown 转音频 / kokoro

## Quick Start

```bash
# 一次性安装（选一个或都装）
bash skills/tts/scripts/tts.sh setup kokoro    # 本地，免费
bash skills/tts/scripts/tts.sh setup noiz      # 云端，需 NOIZ_API_KEY
```

## 简单模式 — 文本转音频

```bash
# Kokoro（安装后自动检测）
bash skills/tts/scripts/tts.sh speak -t "你好世界" -v zf_xiaoni --lang cmn -o hello.wav
bash skills/tts/scripts/tts.sh speak -f article.txt -v af_sarah -o out.mp3 --format mp3

# Noiz（设置 NOIZ_API_KEY 后自动检测，或 --backend noiz 强制指定）
bash skills/tts/scripts/tts.sh speak -t "你好" --backend noiz --voice-id voice_abc -o hi.wav
bash skills/tts/scripts/tts.sh speak -f input.txt --backend noiz --voice-id voice_abc --auto-emotion --emo '{"Joy":0.5}' -o out.wav

# 音色克隆（仅 Noiz）
bash skills/tts/scripts/tts.sh speak -t "你好" --backend noiz --ref-audio ./ref.wav -o clone.wav
```

脚本自动选后端：有 `NOIZ_API_KEY` → Noiz；有 `kokoro-tts` → Kokoro。可用 `--backend` 覆盖。

Kokoro 原生支持 EPUB/PDF：

```bash
kokoro-tts book.epub --split-output ./chapters/ --format mp3 --voice af_bella
kokoro-tts document.pdf output.wav --voice am_michael
```

## 时间轴模式 — SRT 转精确对齐音频

适用于配音、字幕、视频旁白等需要逐句精确时间的场景。

### 第一步：获取或创建 SRT

如果用户没有 SRT，从文本生成：

```bash
bash skills/tts/scripts/tts.sh to-srt -i article.txt -o article.srt
bash skills/tts/scripts/tts.sh to-srt -i article.txt -o article.srt --cps 15 --gap 500
```

`--cps` = 每秒字符数（默认 4，适合中文；英文约 15）。Agent 也可以手写 SRT。

### 第二步：创建 voice map

JSON 文件控制默认及逐句音色。`segments` 键支持单句 `"3"` 或范围 `"5-8"`。

Kokoro voice map：

```json
{
  "default": { "voice": "zf_xiaoni", "lang": "cmn" },
  "segments": {
    "1": { "voice": "zm_yunxi" },
    "5-8": { "voice": "af_sarah", "lang": "en-us", "speed": 0.9 }
  }
}
```

Noiz voice map（额外支持 `emo`、`reference_audio`）：

```json
{
  "default": { "voice_id": "voice_123", "target_lang": "zh" },
  "segments": {
    "1": { "voice_id": "voice_host", "emo": { "Joy": 0.6 } },
    "2-4": { "reference_audio": "./refs/guest.wav" }
  }
}
```

完整示例见 `examples/`。

### 第三步：渲染

```bash
bash skills/tts/scripts/tts.sh render --srt input.srt --voice-map vm.json -o output.wav
bash skills/tts/scripts/tts.sh render --srt input.srt --voice-map vm.json --backend noiz --auto-emotion -o output.wav
```

## 选择建议

| 需求 | 推荐 |
|------|------|
| 只是朗读文本 | Kokoro（默认） |
| EPUB/PDF 转有声书 | Kokoro（原生支持） |
| 音色混合（`"v1:60,v2:40"`） | Kokoro |
| 从参考音频克隆音色 | Noiz |
| 情感控制（`emo` 参数） | Noiz |
| 服务端逐句精确时长 | Noiz |

> 需要情感控制 + 音色克隆 + 精确时长三合一时，Noiz 是唯一同时支持的后端。

## Limitations

- **Kokoro**：无克隆、无情感、无服务端时长控制；Python 3.9–3.12；模型约 500MB
- **Noiz**：单次最多 5000 字符；云端延迟；需 API Key + 额度
- 时间轴模式：文本过长而时长过短 → 语速不自然（两端均存在）

## Requirements

- `ffmpeg`（时间轴模式需要）
- 运行 `tts.sh setup kokoro` 和/或 `tts.sh setup noiz`

后端细节和完整参数参见 [reference.md](reference.md)。
