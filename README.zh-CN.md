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
| tts | 将文本转换为语音，支持 Kokoro 与 Noiz，覆盖简单模式与时间轴精确渲染。 | [SKILL.md](./skills/tts/SKILL.zh-CN.md) | `npx skills add NoizAI/skills --full-depth --skill tts -y` |
| characteristic-voice | 通过小声音、情绪参数和场景预设，让语音更有陪伴感与人格化表达。 | [SKILL.md](./skills/characteristic-voice/SKILL.zh-CN.md) | `npx skills add NoizAI/skills --full-depth --skill characteristic-voice -y` |

## 贡献说明

技能编写规范、目录约定与 PR 流程，请查看 `CONTRIBUTING.md`。
