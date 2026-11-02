import argparse
import json
import os
import random
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import yaml


def load_config(path):
    """Read a YAML config. A top-level `extends: <file>` (relative to it) is loaded first and overridden."""
    path = Path(path)
    cfg = yaml.safe_load(path.read_text())
    if "extends" in cfg:
        cfg = load_config(path.parent / cfg.pop("extends")) | cfg
    return cfg


parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True, help="YAML config, e.g. configs/base.yaml")
config_path = parser.parse_args().config
cfg = load_config(config_path)

# Model calls go through the Claude Code CLI (`claude -p`), so they run on your Claude
# subscription; log in once with `claude auth login`. The empty cwd keeps this repo's
# CLAUDE.md out of the model's context, and dropping CLAUDE* vars stops a parent Claude
# Code session's settings leaking into the CLI. MAX_THINKING_TOKENS caps the thinking.
cli_cwd = tempfile.mkdtemp()
cli_env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE") or k == "CLAUDE_CONFIG_DIR"}
cli_env["MAX_THINKING_TOKENS"] = str(cfg["thinking_budget"])


def ask(prompt, system=""):
    out = subprocess.run(
        ["claude", "-p", "--model", cfg["model"], "--system-prompt", system,
         "--tools", "", "--safe-mode", "--no-session-persistence", "--output-format", "json"],
        input=prompt, capture_output=True, text=True, cwd=cli_cwd, env=cli_env,
    )
    reply = json.loads(out.stdout)
    if reply["is_error"]:
        raise RuntimeError(reply["result"])
    return reply["result"]


run_dir = Path(cfg["results_dir"]) / f"{Path(config_path).stem}_{datetime.now():%Y-%m-%d_%H-%M-%S}"
run_dir.mkdir(parents=True)

n_samples, n_values = cfg["n_samples"], cfg["n_values"]
rng = random.Random(cfg["seed"])
n_exact = 0
n_correct = 0
rows = []

for i in range(n_samples):
    task = rng.choice(cfg["tasks"])
    values = [rng.randrange(cfg["value_range"]) for _ in range(n_values)]

    # encode
    answer = ask(
        cfg["encoder_template"].format(task=task, values=" ".join(str(v) for v in values), scheme=cfg["scheme"]),
        system=cfg["system_prompt"],
    )

    # decode
    decoded_raw = ask(cfg["decoder_template"].format(answer=answer, scheme=cfg["scheme"]))
    decoded = [int(x) for x in re.findall(r"-?\d+", decoded_raw)][:n_values]

    exact = decoded == values
    correct = sum(a == b for a, b in zip(decoded, values))
    n_exact += exact
    n_correct += correct
    rows.append({"task": task, "values": values, "answer": answer, "decoded_raw": decoded_raw,
                 "decoded": decoded, "exact": exact, "values_correct": correct / n_values})
    print(f"sample {i + 1}/{n_samples}: values={values} decoded={decoded}" + (" (exact)" if exact else ""))

metrics = {"n_samples": n_samples, "exact_matches": n_exact / n_samples,
           "values_correct": n_correct / (n_samples * n_values)}
with open(run_dir / "config.yaml", "w") as f:
    yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)
with open(run_dir / "completions.jsonl", "w") as f:
    for row in rows:
        f.write(json.dumps(row) + "\n")
with open(run_dir / "metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print("\n=== summary ===")
print("exact matches:", metrics["exact_matches"])
print("values correct:", metrics["values_correct"])
print("results written to", run_dir)
