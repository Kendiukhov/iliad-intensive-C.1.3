# Exercise 00 — one script

A single-file steganography experiment: `steg.py`. The exercise brief is in the
markdown file next to it.

```bash
uv run python steg.py --config configs/base.yaml    # 5 samples
uv run python steg.py --config configs/debug.yaml   # 2 samples, quick check
```

All settings and prompts live in `configs/`. Each run writes
`results/<config>_<timestamp>/` with `config.yaml`, `completions.jsonl` and `metrics.json`.

Model calls run through the Claude Code CLI on your Claude subscription: log in once with
`claude auth login` (no API key needed).
