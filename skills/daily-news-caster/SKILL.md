---
name: daily-news-caster
description: Fetches the latest news using news-aggregator-skill, formats it into a podcast script in Markdown format, and uses the tts skill to generate a podcast audio file. Use when the user asks to get the latest news and read it out as a podcast.
---

# Daily News Caster Skill

This skill allows the agent to fetch real-time news, organize it into a conversational podcast script, and generate an audio file reading the script out loud.

## Workflow Instructions

When the user asks to get the latest news and make a podcast out of it, follow these steps strictly:

### Step 1: Ensure Skills are Installed
If the `news-aggregator-skill` and `tts` skills are not already installed in the workspace, run the following commands to install them:
```bash
npx skills add https://github.com/cclank/news-aggregator-skill --skill news-aggregator-skill -y
npx skills add https://github.com/noizai/skills --skill tts -y
```

### Step 2: Fetch the Latest News
Find the `fetch_news.py` script from the `news-aggregator-skill` (usually located in `.cursor/skills/news-aggregator-skill/scripts/fetch_news.py` or `skills/news-aggregator-skill/scripts/fetch_news.py`).

Run the script to fetch real-time news. You can specify a source (e.g., `hackernews`, `github`, `all`) or keywords based on the user's request.
Example command:
```bash
python3 path/to/fetch_news.py --source all --limit 10 --deep
```

### Step 3: Write the Podcast Script
Read the fetched news data and rewrite the information into a **Markdown podcast script**. 
The script should be:
- **Conversational yet concise:** Write as if a podcast host is speaking, but **avoid unnecessary fluff or overly long transitions**. Keep it to the point (言简意赅) while retaining all critical information and facts.
- **Structured:** Use markdown headings and clear paragraphs.
- **Clear text for speech:** Avoid complex URLs, raw markdown links, or unpronounceable characters in the spoken text.

Save this script to a local file named `podcast_script.md`.

**Example `podcast_script.md` Content:**
```markdown
Welcome to today's news roundup! Today we have some exciting updates across the tech world.

First up... [Insert conversational summary of News Item 1].
This is particularly interesting because... [Insert analysis or context].

Moving on to our next story... [Insert conversational summary of News Item 2].

That's all for today's quick update. Thanks for tuning in!
```

### Step 4: Generate the Podcast Audio
Use the `tts` skill to convert the `podcast_script.md` into an audio file.

Find the `tts.sh` script (usually located in `skills/tts/scripts/tts.sh` or `.cursor/skills/tts/scripts/tts.sh`) and use the `speak` command with the `-f` flag to read the file:
```bash
bash path/to/tts.sh speak -f podcast_script.md -o podcast_output.mp3
```

### Step 5: Present the Result
Let the user know that the podcast has been successfully generated. You **MUST** provide both files back to the user:
- Show or link to the `podcast_script.md` file so they can read the script.
- Provide the path to the `podcast_output.mp3` file so they can listen to the audio.
- Briefly summarize the headlines that were included in the podcast.
