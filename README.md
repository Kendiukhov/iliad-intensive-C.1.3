# Exercise 01 — Logging & config (plan mode)

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

## Editor: LazyVim

Install [LazyVim](https://www.lazyvim.org) (needs Neovim ≥ 0.11.2 and git):

```bash
brew install neovim
brew install --cask font-jetbrains-mono-nerd-font  # then select it as your terminal font (for icons)
mv ~/.config/nvim ~/.config/nvim.bak 2>/dev/null  # back up any existing config
git clone https://github.com/LazyVim/starter ~/.config/nvim
rm -rf ~/.config/nvim/.git
nvim  # first launch installs plugins
```
