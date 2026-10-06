from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from scripts import eval_behavior as behavior


def stream(*events: dict) -> str:
    return "\n".join(json.dumps(event, ensure_ascii=False) for event in events)


class ClaudeCodeBackendTests(unittest.TestCase):
    def test_routes_only_claude_models(self) -> None:
        self.assertEqual(
            behavior.claude_code_model(["pi", "--model", "anthropic/claude-sonnet-5", "x"]),
            "claude-sonnet-5",
        )
        self.assertEqual(
            behavior.claude_code_model(["pi", "--model", "claude-code/opus", "x"]), "opus"
        )
        self.assertIsNone(
            behavior.claude_code_model(["pi", "--model", "deepseek/deepseek-v4-flash", "x"])
        )
        self.assertIsNone(behavior.claude_code_model(["git", "status"]))

    def test_generator_invocation_reads_skill_through_claude(self) -> None:
        args = behavior.pi_args(
            prompt="/skill:write-craft\n\n任务", model="anthropic/sonnet",
            thinking="low", with_skill=True,
        )
        command, prompt = behavior.claude_code_invocation(args)
        self.assertEqual(command[:4], ["claude", "-p", "--model", "sonnet"])
        self.assertIn("Read", command[command.index("--tools") + 1])
        self.assertIn(str(behavior.SKILL_ROOT.resolve()), command)
        self.assertTrue(prompt.startswith("先用 Read 阅读"))
        self.assertIn("SKILL.md", prompt)
        self.assertNotIn("/skill:write-craft", prompt)
        self.assertTrue(prompt.endswith("任务"))

    def test_plain_invocation_has_no_tools(self) -> None:
        args = behavior.pi_args(prompt="审稿", model="anthropic/sonnet",
                                thinking="low", with_skill=False)
        command, prompt = behavior.claude_code_invocation(args)
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertEqual(prompt, "审稿")

    def test_structured_tool_review_is_rejected(self) -> None:
        args = behavior.pi_args(prompt="p", model="anthropic/sonnet", thinking="low",
                                with_skill=False, structured_tool=behavior.FACT_JUDGMENT_TOOL)
        result = behavior.run_command(args, 5)
        self.assertEqual(result["returncode"], 2)
        self.assertIn("not supported through Claude Code", result["stderr"])

    def test_stream_conversion_feeds_existing_parsers(self) -> None:
        skill_file = str(behavior.SKILL_ROOT.resolve() / "SKILL.md")
        raw = stream(
            {"type": "system", "subtype": "init"},
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": skill_file}}]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "t1", "is_error": False}]}},
            {"type": "result", "subtype": "success", "is_error": False, "result": "成稿正文",
             "total_cost_usd": 0.01,
             "usage": {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 2}},
        )
        jsonl = behavior.claude_stream_to_pi_jsonl(raw, "sonnet")
        self.assertEqual(behavior.extract_final_assistant(jsonl)["text"], "成稿正文")
        trace = behavior.skill_read_trace(jsonl)
        self.assertEqual(trace["reads"], [{"path": "SKILL.md", "status": "SUCCEEDED"}])
        usage = behavior.assistant_usage_summary(jsonl)
        self.assertEqual(usage["usage"]["totalTokens"], 17)
        self.assertAlmostEqual(usage["cost"]["total"], 0.01)

    def test_error_result_is_reported_as_error(self) -> None:
        jsonl = behavior.claude_stream_to_pi_jsonl(
            stream({"type": "result", "is_error": True, "result": "Not logged in"}), "sonnet"
        )
        with self.assertRaises(behavior.ContractError):
            behavior.extract_final_assistant(jsonl)

    def test_run_claude_code_passes_prompt_on_stdin_outside_repo(self) -> None:
        args = behavior.pi_args(prompt="审稿", model="claude-code/sonnet",
                                thinking="low", with_skill=False)
        fake = {"returncode": 0, "stderr": "", "duration_seconds": 1.0, "timed_out": False,
                "stdout": stream({"type": "result", "is_error": False, "result": "好"})}
        with patch.object(behavior, "run_process", return_value=fake) as runner:
            result = behavior.run_command(args, 30)
        _, kwargs = runner.call_args
        self.assertEqual(kwargs["stdin"], "审稿")
        self.assertNotEqual(kwargs["cwd"], behavior.ROOT)
        self.assertEqual(behavior.extract_final_assistant(result["stdout"])["text"], "好")


if __name__ == "__main__":
    unittest.main()
