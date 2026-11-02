# Exercise 02 — Monitor & schemes (subagents)

Part of the Claude Code exercises for the ILIAD intensive. The brief is in the markdown
file next to this one. Exercise 00 is the same steganography experiment as a single script;
here it lives in a structured repo (`experiments/`, `lib/`, a config framework).

```bash
uv sync
cd experiments/<name>
uv run python main.py -c configs/<config>.yaml
```

Model calls run through the Claude Code CLI on your Claude subscription: log in once with
`claude auth login` (no API key needed). See `CLAUDE.md` for conventions.
