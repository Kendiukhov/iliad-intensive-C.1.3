"""Turn steg_comm runs into a monitor_test dataset: one row per completion, labelled per run.

Lets the monitor score each scheme's answers (mean suspiciousness per label = per scheme):
    uv run python collect_steg_answers.py shipped=../steg_comm/results/<run> acrostic=../steg_comm/results/<run> \
        > data/scheme_answers.jsonl
    uv run python main.py -c configs/scheme_answers.yaml
"""
import json
import sys
from pathlib import Path

for arg in sys.argv[1:]:
    label, run_dir = arg.split("=", 1)
    for line in (Path(run_dir) / "completions.jsonl").read_text().splitlines():
        row = json.loads(line)
        print(json.dumps({"task": row["main_task"], "text": row["answer"], "label": label}))
