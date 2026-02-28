# skills

English | [简体中文](./README.zh-CN.md)

Central repository for managing Agent Skills.

## Install with `npx skills add`

```bash
# List skills from GitHub repository
npx skills add NoizAI/skills --list --full-depth

# Install a specific skill from GitHub repository
npx skills add NoizAI/skills --full-depth --skill tts -y

# Install from GitHub repository
npx skills add <owner>/<repo>

# Local development (run in this repo directory)
npx skills add . --list --full-depth
```

## Available skills

| Name | Description | Documentation | Run command |
|------|-------------|---------------|-------------|
| tts | Convert text into speech with Kokoro or Noiz, supporting simple mode and timeline-aligned rendering workflows. | [SKILL.md](./skills/tts/SKILL.md) | `npx skills add NoizAI/skills --full-depth --skill tts -y` |
| characteristic-voice | Make generated speech feel companion-like with fillers, emotional tuning, and preset speaking styles. | [SKILL.md](./skills/characteristic-voice/SKILL.md) | `npx skills add NoizAI/skills --full-depth --skill characteristic-voice -y` |

## Configure `NOIZ_API_KEY`

Set `NOIZ_API_KEY` environment variable to boost speed of some skills.
- macOS / Linux (bash, zsh):
  ```bash
  export NOIZ_API_KEY="your_api_key_here"
  ```
  To persist it, add the same line to `~/.zshrc` or `~/.bashrc`, then restart the shell.
  Special case (macOS + Cursor): if Cursor is launched from GUI, it may not inherit shell env vars, use `launchctl setenv NOIZ_API_KEY your_api_key_here` and restart cursor.
- Windows PowerShell (current session):
  ```powershell
  $env:NOIZ_API_KEY="your_api_key_here"
  ```
- Windows Command Prompt (persist for future sessions):
  ```cmd
  setx NOIZ_API_KEY "your_api_key_here"
  ```

Verify the variable is set:



## Contributing

For skill authoring rules, directory conventions, and PR guidance, see `CONTRIBUTING.md`.
