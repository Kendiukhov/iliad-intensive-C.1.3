import random
import asyncio

from lib.sampling import make_client, sample
from lib.parsing import parse_values
from lib.scoring import summarize, exact_match


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

    for i, r in enumerate(results):
        print(f"\n=== sample {i + 1}/{len(results)} ===")
        print(f"main task: {r['main_task']}")
        print(f"values:    {r['values']}")
        print(f"answer:    {r['answer']}")
        print(f"decoded:   {r['decoded']}  (exact={exact_match(r['decoded'], r['values'])})")

    metrics = summarize([(r["decoded"], r["values"]) for r in results])
    print("\n=== summary ===")
    for k, v in metrics.items():
        print(f"{k}: {v:.3f}")


def run_steg(model, thinking_budget, max_concurrency, n_eval, n_values, value_range, seed,
             system_prompt, scheme, encoder_template, decoder_template, main_tasks):
    asyncio.run(_run_steg(model, thinking_budget, max_concurrency, n_eval, n_values, value_range, seed,
                          system_prompt, scheme, encoder_template, decoder_template, main_tasks))
