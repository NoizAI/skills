# skills

[English](./README.md) | 简体中文

用于集中管理 Agent Skills 的仓库。

## 用 `npx skills add` 安装

```bash
# 查看 GitHub 仓库可安装技能
npx skills add NoizAI/skills --list --full-depth

# 从 GitHub 仓库安装指定技能
npx skills add NoizAI/skills --full-depth --skill tts -y

# 从 GitHub 仓库安装
npx skills add <owner>/<repo>

# 本地开发调试（在仓库目录执行）
npx skills add . --list --full-depth
```

## 已有技能

| 名称 | 说明 | 文档 | 可运行命令 |
|------|------|------|------------|
| tts | 将文本转为语音，支持 Kokoro / Noiz：简单模式、时间轴精确渲染、精确时长控制与参考音频音色克隆。 | [SKILL.md](./skills/tts/SKILL.md) | `npx skills add NoizAI/skills --full-depth --skill tts -y` |
| video-translation | 视频翻译与配音：按字幕时间轴生成 TTS 并替换原音轨，支持按句使用原视频对应时间段的参考音频。 | [SKILL.md](./skills/video-translation/SKILL.md) | `npx skills add NoizAI/skills --full-depth --skill video-translation -y` |
| characteristic-voice | 通过小声音、情绪参数和场景预设，让语音更有陪伴感与人格化表达。 | [SKILL.md](./skills/characteristic-voice/SKILL.zh-CN.md) | `npx skills add NoizAI/skills --full-depth --skill characteristic-voice -y` |

## 快速验证

```bash
bash skills/characteristic-voice/scripts/speak.sh \
  --preset comfort -t "嗯... 我在呢" -o comfort.wav
```

## 英文音频示例

可直接试听以下示例（转为 MP4 以支持页面内播放）：

- 新闻快讯风格  
  <video src="./examples/audio/demo-breaking-news.mp4" controls></video>
- 冥想治愈风格  
  <video src="./examples/audio/demo-mindful-calm.mp4" controls></video>
- 播客开场风格  
  <video src="./examples/audio/demo-podcast-intro.mp4" controls></video>
- 创业激励风格  
  <video src="./examples/audio/demo-startup-hype.mp4" controls></video>

## Noiz API Key（推荐）

为获得最佳体验（更快、支持情绪控制、音色克隆），从 [developers.noiz.ai](https://developers.noiz.ai) 获取 API key：

```bash
bash skills/tts/scripts/tts.sh config --set-api-key YOUR_KEY
```

Key 会持久化到 `~/.noiz_api_key`，后续自动加载。也可传 `--backend kokoro` 使用本地 Kokoro 后端。

## 贡献说明

技能编写规范、目录约定与 PR 流程，请查看 `CONTRIBUTING.md`。
