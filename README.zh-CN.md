# skills

[English](./README.md) | 简体中文

用于集中管理 Agent Skills 的仓库。

## 目标

- 统一存放技能定义（`SKILL.md`）
- 按主题清晰组织技能目录
- 支持后续发布与复用

## 仓库结构

```text
.
├── skills/
│   ├── README.md
│   ├── characteristic-voice/
│   │   └── SKILL.md
│   ├── tts/
│   │   └── SKILL.md
│   └── template-skill/
│       └── SKILL.md
├── CONTRIBUTING.md
├── README.md
└── README.zh-CN.md
```

## 快速开始

1. 在 `skills/` 下创建技能目录（例如 `my-skill/`）
2. 添加 `SKILL.md`
3. 参考 `skills/template-skill/SKILL.md` 填写触发词、能力和执行流程

## 技能规范（简版）

- 一个技能对应一个目录
- 每个技能目录必须包含 `SKILL.md`
- `SKILL.md` 需要清楚说明：
  - 触发场景（triggers）
  - 能力边界（can / cannot）
  - 标准执行步骤（step-by-step）
  - 输入输出约定

## 后续建议

- 增加结构与必填字段校验脚本
- 增加示例输入输出与测试数据
- 增加发布与安装说明（项目级/全局级）
