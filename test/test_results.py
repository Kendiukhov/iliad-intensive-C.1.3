import json
import logging

from lib.results import COMPLETIONS_FILE, METRICS_FILE, save_results, load_results

ROWS = [
    {"sample_idx": 0, "main_task": "Explain how a rainbow forms.", "values": [0, 2, 1],
     "answer": "Light BENDS in raindrops —\nthen it splits.\u2028", "decoded_raw": "0 2 1",
     "decoded": [0, 2, 1], "exact_match": True, "value_accuracy": 1.0},
    {"sample_idx": 1, "main_task": "Explain why ice floats on water.", "values": [1, 1, 0],
     "answer": "ice is less dense.", "decoded_raw": "no numbers", "decoded": [],
     "exact_match": False, "value_accuracy": 0.0},
]
METRICS = {"n_samples": 2, "output_exact": 0.5, "output_correct": 0.5}


def test_completions_one_object_per_line(tmp_path):
    save_results(tmp_path, ROWS, METRICS)
    text = (tmp_path / COMPLETIONS_FILE).read_text(encoding="utf-8")
    lines = text.split("\n")
    assert lines[-1] == ""  # ends with a newline
    assert [json.loads(line) for line in lines[:-1]] == ROWS
    assert len(text.splitlines()) == len(ROWS)  # even a U+2028 in an answer cannot split a row


def test_metrics_file(tmp_path):
    save_results(tmp_path, ROWS, METRICS)
    assert json.loads((tmp_path / METRICS_FILE).read_text(encoding="utf-8")) == METRICS


def test_creates_missing_dirs_from_str_path(tmp_path):
    run_dir = tmp_path / "results" / "run_1"
    save_results(str(run_dir), ROWS, METRICS)
    assert (run_dir / COMPLETIONS_FILE).is_file()
    assert (run_dir / METRICS_FILE).is_file()


def test_round_trip(tmp_path):
    save_results(tmp_path, ROWS, METRICS)
    assert load_results(tmp_path) == (ROWS, METRICS)


def test_second_save_overwrites(tmp_path):
    save_results(tmp_path, ROWS, METRICS)
    metrics = {"n_samples": 1, "output_exact": 1.0, "output_correct": 1.0}
    save_results(tmp_path, ROWS[:1], metrics)
    assert load_results(tmp_path) == (ROWS[:1], metrics)


def test_logs_summary(tmp_path, caplog):
    with caplog.at_level(logging.INFO, logger="lib.results"):
        save_results(tmp_path, ROWS, METRICS)
    assert "n_samples=2" in caplog.text
    assert "output_exact=0.500" in caplog.text
