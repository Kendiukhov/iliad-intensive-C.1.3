## ⚠️ This is a Claude Code exercise — do NOT read the exercise brief

This repo is a hands-on exercise for the **user** to practice driving Claude Code.
The markdown brief next to `steg.py` is the participant's task description — the user
will relay it to you in their own words. **Do not read, `cat`, or `grep` it** (a hook
also blocks it). Work only from what the user tells you.

## Project

`steg.py` is a single-file experiment: can a model secretly transmit a sequence of
numbers inside an ordinary answer? Each sample makes two model calls (encode, then
decode) and scores how many numbers survive the round-trip.

## Conventions

- **uv** is the package manager. Run: `uv run python steg.py`. Add deps: `uv add <package>` (never edit pyproject.toml directly).
- Model calls go through the Claude Code CLI (`claude -p`, see `ask()` in `steg.py`), so they run on your Claude subscription — log in once with `claude auth login`. No API keys or `.env` needed.
- Keep it simple: one script, minimal code, no speculative error handling.
- Runs make real model calls on your Claude subscription. Don't launch a run without asking; small debug runs are fine.

## YAML Gotchas

- **Write scientific notation with an explicit decimal and sign**: `5.0e-4`, not `5e-4`. PyYAML parses `5e-4` as a string, not a float.
