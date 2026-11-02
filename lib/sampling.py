import asyncio
import json
import os
import tempfile

# Model calls go through the Claude Code CLI (`claude -p`), so they run on your Claude
# subscription rather than a metered API key. Log in once with `claude auth login`.


def build_command(model: str, system: str | None, json_schema: dict | None = None) -> list[str]:
    """CLI args for one tool-less completion; `system` replaces Claude Code's own system prompt."""
    cmd = [
        "claude", "-p", "--model", model, "--system-prompt", system or "",
        "--tools", "", "--safe-mode", "--no-session-persistence", "--output-format", "json",
    ]
    if json_schema is not None:
        cmd += ["--json-schema", json.dumps(json_schema)]
    return cmd


def parse_result(stdout: str, structured: bool) -> str:
    """The reply in `claude -p --output-format json` output (re-serialized JSON if `structured`)."""
    data = json.loads(stdout)
    if data["is_error"]:
        raise RuntimeError(f"claude -p failed: {data['result']}")
    return json.dumps(data["structured_output"]) if structured else data["result"]


class ClaudeCodeClient:
    """Runs completions as `claude -p` subprocesses, at most `max_concurrency` at a time."""

    def __init__(self, max_concurrency: int, thinking_budget: int):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        # An empty cwd keeps this repo's CLAUDE.md and git state out of the model's context, and
        # dropping CLAUDE* vars stops a parent Claude Code session's settings leaking into the CLI
        # (CLAUDE_CONFIG_DIR stays: it says where your login lives).
        self.cwd = tempfile.mkdtemp(prefix="claude-sampling-")
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith("CLAUDE") or k == "CLAUDE_CONFIG_DIR"}
        self.env["MAX_THINKING_TOKENS"] = str(thinking_budget)

    async def complete(self, model: str, prompt: str, system: str | None = None,
                       json_schema: dict | None = None) -> str:
        async with self.semaphore:
            proc = await asyncio.create_subprocess_exec(
                *build_command(model, system, json_schema), cwd=self.cwd, env=self.env,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate(prompt.encode())
        if not stdout:
            raise RuntimeError(f"claude -p exited with {proc.returncode}: {stderr.decode()}")
        return parse_result(stdout.decode(), structured=json_schema is not None)


def make_client(max_concurrency: int, thinking_budget: int) -> ClaudeCodeClient:
    return ClaudeCodeClient(max_concurrency, thinking_budget)


async def sample(client, model, prompt, system=None):
    """One completion. Returns the reply text."""
    return await client.complete(model, prompt, system)
