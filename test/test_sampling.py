import asyncio
import json
import os

import pytest

from lib.sampling import build_command, parse_result, make_client, sample


def _arg(cmd, flag):
    return cmd[cmd.index(flag) + 1]


def test_command_replaces_system_prompt_and_disables_tools():
    cmd = build_command("m", "sys")
    assert cmd[:2] == ["claude", "-p"]
    assert _arg(cmd, "--model") == "m"
    assert _arg(cmd, "--system-prompt") == "sys"
    assert _arg(cmd, "--tools") == ""
    assert "--json-schema" not in cmd


def test_command_without_system_uses_empty_system_prompt():
    assert _arg(build_command("m", None), "--system-prompt") == ""


def test_command_with_json_schema():
    cmd = build_command("m", None, {"type": "object"})
    assert json.loads(_arg(cmd, "--json-schema")) == {"type": "object"}


def test_parse_result():
    assert parse_result(json.dumps({"is_error": False, "result": "hi"}), structured=False) == "hi"


def test_parse_structured_result():
    out = json.dumps({"is_error": False, "result": "...", "structured_output": {"x": 1}})
    assert json.loads(parse_result(out, structured=True)) == {"x": 1}


def test_parse_error_raises():
    with pytest.raises(RuntimeError, match="session expired"):
        parse_result(json.dumps({"is_error": True, "result": "session expired"}), structured=False)


def test_client_runs_cli(tmp_path, monkeypatch):
    """A fake `claude` on PATH echoes what it was given: prompt via stdin, clean env, empty cwd."""
    fake = tmp_path / "claude"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "seen = {'argv': sys.argv[1:], 'stdin': sys.stdin.read(), 'cwd': os.getcwd(),\n"
        "        'thinking': os.environ.get('MAX_THINKING_TOKENS'), 'claudecode': os.environ.get('CLAUDECODE'),\n"
        "        'api_key': os.environ.get('ANTHROPIC_API_KEY'), 'config_dir': os.environ.get('CLAUDE_CONFIG_DIR'),\n"
        "        'cwd_files': os.listdir('.')}\n"
        "print(json.dumps({'is_error': False, 'result': json.dumps(seen)}))\n"
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/tmp/claude-config")

    seen = json.loads(asyncio.run(sample(make_client(max_concurrency=2, thinking_budget=7), "m", "hi", "sys")))
    assert seen["stdin"] == "hi"
    assert _arg(seen["argv"], "--system-prompt") == "sys"
    assert seen["thinking"] == "7"
    assert seen["claudecode"] is None
    assert seen["cwd"] != os.getcwd() and seen["cwd_files"] == []
    assert seen["api_key"] is None  # stays on the subscription login
    assert seen["config_dir"] == "/tmp/claude-config"
