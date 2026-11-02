import json

# Constrains the reply to {"suspiciousness": <int 0-9>} via `claude -p --json-schema`.
SCHEMA = {
    "type": "object",
    "properties": {"suspiciousness": {"type": "integer", "minimum": 0, "maximum": 9}},
    "required": ["suspiciousness"],
}


def parse_suspiciousness(content: str) -> int:
    """Pull the integer suspiciousness score out of a monitor's JSON reply."""
    return int(json.loads(content)["suspiciousness"])


async def monitor(client, model, prompt_template, task, output):
    """Ask a model how suspicious `output` looks for `task`. Returns an int score.

    `prompt_template` must contain `{task}` and `{output}` placeholders and ask
    for a JSON reply of the form {"suspiciousness": <int>}.
    """
    content = await client.complete(
        model, prompt_template.format(task=task, output=output), json_schema=SCHEMA,
    )
    return parse_suspiciousness(content)
