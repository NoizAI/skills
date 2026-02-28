# skills

English | [简体中文](./README.zh-CN.md)

Central repository for managing Agent Skills.

## Goals

- Store skill definitions in a unified format (`SKILL.md`)
- Organize skills by topic with clear directories
- Prepare for future publishing and reuse

## Repository Structure

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

## Quick Start

1. Create a new skill directory under `skills/` (for example `my-skill/`)
2. Add a `SKILL.md` file
3. Fill triggers, capabilities, and workflow based on `skills/template-skill/SKILL.md`

## Skill Guidelines (Short)

- One skill per directory
- Each skill directory must include `SKILL.md`
- `SKILL.md` should clearly define:
  - Trigger scenarios
  - Capability boundaries (`can / cannot`)
  - Standard workflow (step-by-step)
  - Input and output contract

## Notable Skills

- `skills/tts/SKILL.md`: Scenario-focused voice generation workflows for autonomous agents, including scriptable pipelines for TTS rendering and subtitle generation.
- `skills/characteristic-voice/SKILL.md`: One-step setup for expressive speaking styles (e.g., emotions and persona). It can integrate emoji-aware emotional TTS options such as Noiz, while remaining compatible with other emotional TTS providers.

## Next Steps

- Add validation scripts for structure and required fields
- Add sample inputs/outputs and test data
- Add publishing and installation instructions (project-level/global)
