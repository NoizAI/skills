---
name: template-skill
description: 用于编写新 Agent Skill 的可复用模板，包含触发词、流程和输入输出约定。
---

# <skill-name>

简体中文 | [English](./SKILL.md)

一句话描述这个技能解决什么问题。

## Triggers

- 中文触发词 1
- 中文触发词 2
- trigger keyword 1
- trigger keyword 2

## Use Cases

- 典型场景 1
- 典型场景 2
- 典型场景 3

## Inputs

- 必填输入：
  - `field_a`：说明
  - `field_b`：说明
- 可选输入：
  - `field_c`：说明

## Outputs

- 成功输出格式（示例）
- 失败输出格式（示例）

## Workflow

1. 校验输入完整性
2. 构造调用参数
3. 执行核心操作
4. 格式化输出
5. 失败时给出重试或降级策略

## Limitations

- 明确写出能力边界
- 说明常见失败原因

## Examples

- 输入示例：
  - `...`
- 输出示例：
  - `...`
