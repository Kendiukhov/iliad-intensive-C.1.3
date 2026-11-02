## ⚠️ This is a Claude Code exercise — do NOT read `EXERCISE.md`

This repo is a hands-on exercise for the **user** to practice driving Claude Code.
`EXERCISE.md` is the participant's brief — the task and steps the user will relay to
you in their own words. **Do not read, `cat`, or `grep` `EXERCISE.md`** (a hook also
blocks it). Work only from what the user tells you.

## Project Goal

Steganographic communication: can a model secretly transmit a sequence of numbers while answering an ordinary question? `experiments/steg_comm` encodes numbers into an answer, decodes them back, and scores how many survive the round-trip.

## Repository Structure

### Package Management
- **uv** is the package manager
- Run scripts: `uv run python <script.py>`
- Install dependencies: `uv add <package>` (never edit pyproject.toml directly)

### Model Access
- Model calls go through the Claude Code CLI (`claude -p`, see `lib/sampling.py`), so they run on your Claude subscription — log in once with `claude auth login`. No API keys or `.env` needed.

### Directory Layout

**lib/** - Shared utilities
- Installable Python package (defined in pyproject.toml)
- Import from experiments: `from lib.<module> import ...`

**test/** - Unit tests for lib modules
- Test files named `test_<module>.py`
- Run with `uv run pytest`

**experiments/** - Independent, self-contained ML experiments (one subfolder each)

**tmp/** - exploration and prototyping

## Experiments

An experiment is any self-contained study — training, evaluation, data generation, analysis — all sharing the structure below. The `train_sft` names used in the examples are illustrative; substitute whatever the experiment actually does.

Each experiment lives in `experiments/<name>/`:

- `main.py` - Entry point. Defines a `function_map` (name → callable) and calls `execute_experiments()`:
  ```python
  from research_scaffold.config_tools import execute_experiments
  from research_scaffold.argparsing import get_base_argparser, process_base_args
  from functions import train_sft

  function_map = {"train_sft": train_sft}

  if __name__ == "__main__":
      args = get_base_argparser().parse_args()
      config_path, meta_config_path, sweep_config_path = process_base_args(args)
      execute_experiments(
          function_map=function_map,
          config_path=config_path,
          meta_config_path=meta_config_path,
          sweep_config_path=sweep_config_path,
      )
  ```
- `functions/` - The functions referenced by `function_name`. Called as `func(**function_kwargs)`, so every kwarg the function needs must be in the config.
- `configs/` - All config files (see Config System below).
- `results/<run_name>/` - One subfolder per run: logs, saved config.yaml, and whatever the run writes (checkpoints, eval outputs, …).

Run an experiment from its folder with `-c` — the config type is auto-detected from its shape:
```bash
cd experiments/<name>
uv run python main.py -c configs/<config>.yaml
```

### Config System

`execute_experiments` detects the config type from its keys (no separate flag needed):

1. **Single** - has `name` + `function_name`. Runs one experiment.
2. **Meta** - has `experiments:`. Batch runner that composes and runs many single configs.
3. **Sweep** - has `method:` + `parameters:`. Runs a hyperparameter sweep.

**Single config (`base.yaml`)** holds all shared defaults for an experiment:
```yaml
name: train_sft
function_name: train_sft        # must be a key in main.py's function_map
time_stamp_name: true           # append a timestamp to the run name
log_file_path: results/RUN_NAME/logs.txt
save_config_path: results/RUN_NAME/config.yaml
function_kwargs:                # passed verbatim as **kwargs to the function
  ...
```
`RUN_NAME` (and `RUN_GROUP`, `SWEEP_NAME`) are substituted everywhere in paths/kwargs at runtime. `RUN_NAME` resolves to `name`, plus a timestamp if `time_stamp_name: true`.

**Meta config** inherits from a base via `common_root` and lists overrides:
```yaml
common_root: configs/base.yaml   # prepended to every experiment below
experiments:
  - config:                      # inline overrides (or a path to another config)
      name: my_variant           # composed onto base name -> "train_sft_my_variant"
      function_kwargs:
        learning_rate: 5.0e-4    # only what differs from base
```
Composition is `common_root` → `config` → `common_patch`, merged with a recursive dict update: nested dicts deep-merge, lists/scalars replace, later wins. `name` is special-cased to concatenate instead of replace. Use `config_axes` (a list of option-lists) instead of `config` to run the cartesian product of variants.

Conventions:
- **All defaults live in base.yaml, never in Python.** No default values in function signatures, no `kwargs.get(key, default)` — if a config key is missing, crash.
- **Meta configs override only what changes** from `common_root`. Don't restate values equal to base.
- **Debug configs run in seconds, not minutes.**

### Run Discipline

Only run debug configs unsolicited. Never launch a real (non-debug) experiment without explicit approval — they make real model calls on your Claude subscription. Ask "want me to run it?" rather than running and reporting after the fact.

## YAML Gotchas

- **Write scientific notation with an explicit decimal and sign**: `5.0e-4`, not `5e-4`. PyYAML parses `5e-4` as a string, not a float.
