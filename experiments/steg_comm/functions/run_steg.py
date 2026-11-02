import json
import random
import asyncio
from pathlib import Path

from lib.sampling import make_client, sample
from lib.parsing import parse_values
from lib.scoring import summarize, exact_match, value_accuracy


async def _run_one(client, model, main_task, values, scheme, system_prompt,
                   encoder_template, decoder_template):
    answer = await sample(
        client, model,
        encoder_template.format(main_task=main_task, values=" ".join(map(str, values)), scheme=scheme),
        system_prompt,
    )
    decoded_raw = await sample(client, model, decoder_template.format(answer=answer, scheme=scheme))
    decoded = parse_values(decoded_raw)[: len(values)]
    return {
        "main_task": main_task,
        "values": values,
        "answer": answer,
        "decoded_raw": decoded_raw,
        "decoded": decoded,
        "exact": exact_match(decoded, values),
        "accuracy": value_accuracy(decoded, values),
    }


async def _run_steg(model, thinking_budget, max_concurrency, n_eval, n_values, value_range, seed,
                    log_path, system_prompt, encoder_template, decoder_template, scheme, main_tasks):
    rng = random.Random(seed)
    client = make_client(max_concurrency, thinking_budget)
    samples = [
        (rng.choice(main_tasks), [rng.randrange(value_range) for _ in range(n_values)])
        for _ in range(n_eval)
    ]
    results = await asyncio.gather(*[
        _run_one(client, model, mt, vals, scheme, system_prompt,
                 encoder_template, decoder_template)
        for mt, vals in samples
    ])

    metrics = summarize([(r["decoded"], r["values"]) for r in results])

    out = Path(log_path)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "completions.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    with open(out / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"wrote {len(results)} completions to {out}")
    print(f"metrics: {metrics}")


def run_steg(model, thinking_budget, max_concurrency, n_eval, n_values, value_range, seed,
             log_path, system_prompt, encoder_template, decoder_template, scheme, main_tasks):
    asyncio.run(_run_steg(model, thinking_budget, max_concurrency, n_eval, n_values, value_range, seed,
                          log_path, system_prompt, encoder_template, decoder_template, scheme, main_tasks))
