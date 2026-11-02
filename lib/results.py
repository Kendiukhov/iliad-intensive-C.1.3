import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

COMPLETIONS_FILE = "completions.jsonl"
METRICS_FILE = "metrics.json"


def save_results(results_dir: str | Path, rows: list[dict], metrics: dict) -> None:
    """Write one JSON object per row to completions.jsonl and the run summary to metrics.json."""
    path = Path(results_dir)
    path.mkdir(parents=True, exist_ok=True)
    with open(path / COMPLETIONS_FILE, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")  # ASCII-escaped: no raw U+2028 etc. to split a row
    with open(path / METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        f.write("\n")
    summary = " ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}"
                       for k, v in metrics.items())
    log.info(f"Saved {len(rows)} completions and metrics to {results_dir}: {summary}")


def load_results(results_dir: str | Path) -> tuple[list[dict], dict]:
    """Read back the (rows, metrics) that save_results wrote to results_dir."""
    path = Path(results_dir)
    with open(path / COMPLETIONS_FILE, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    with open(path / METRICS_FILE, encoding="utf-8") as f:
        metrics = json.load(f)
    return rows, metrics
