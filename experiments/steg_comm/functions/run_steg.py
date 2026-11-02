import random
import asyncio

from lib.sampling import make_client, sample
from lib.parsing import parse_values
from lib.scoring import summarize, exact_match, value_accuracy
from lib.results import save_results


async def _run_one(client, model, main_task, values, system_prompt, scheme,
                   encoder_template, decoder_template):
    answer = await sample(
        client, model,
        encoder_template.format(main_task=main_task, values=" ".join(map(str, values)), scheme=scheme),
        system_prompt,
    )
    decoded_raw = await sample(client, model, decoder_template.format(answer=answer, scheme=scheme))
    decoded = parse_values(decoded_raw)[: len(values)]
    return {"main_task": main_task, "values": values, "answer": answer,
            "decoded_raw": decoded_raw, "decoded": decoded}


async def _run_steg(model, thinking_budget, max_concurrency, n_eval, n_values, value_range, seed,
                    system_prompt, scheme, encoder_template, decoder_template, main_tasks):
    rng = random.Random(seed)
    client = make_client(max_concurrency, thinking_budget)
    samples = [
        (rng.choice(main_tasks), [rng.randrange(value_range) for _ in range(n_values)])
        for _ in range(n_eval)
    ]
    results = await asyncio.gather(*[
        _run_one(client, model, mt, vals, system_prompt, scheme, encoder_template, decoder_template)
        for mt, vals in samples
    ])

    rows = [
        {"sample_idx": i, **r,
         "exact_match": exact_match(r["decoded"], r["values"]),
         "value_accuracy": value_accuracy(r["decoded"], r["values"])}
        for i, r in enumerate(results)
    ]
    metrics = {"n_samples": len(rows), **summarize([(r["decoded"], r["values"]) for r in results])}
    return rows, metrics


def run_steg(results_dir, model, thinking_budget, max_concurrency, n_eval, n_values, value_range, seed,
             system_prompt, scheme, encoder_template, decoder_template, main_tasks):
    rows, metrics = asyncio.run(
        _run_steg(model, thinking_budget, max_concurrency, n_eval, n_values, value_range, seed,
                  system_prompt, scheme, encoder_template, decoder_template, main_tasks))
    save_results(results_dir, rows, metrics)
