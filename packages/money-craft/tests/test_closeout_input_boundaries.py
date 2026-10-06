from pathlib import Path
import json
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/money-craft/scripts"))
import money_craft as cli
import fuyao_client
import research_run
import tracking_workflow

class CloseoutInputTests(unittest.TestCase):
    def test_fuyao_header_values_rejected_without_echo(self):
        for key in ("synthetic-secret\nsecond-line", "synthetic-secret\x00", "synthetic-secret密钥"):
            for call in (lambda: cli.load_fuyao_credential({cli.API_KEY_ENV: key}), lambda: cli.FuyaoClient(key)):
                with self.subTest(key=repr(key)), self.assertRaises(cli.MoneyCraftError) as caught:
                    call()
                self.assertEqual(caught.exception.exit_code, cli.EXIT_CONFIG)
                self.assertNotIn("synthetic-secret", str(caught.exception))

    def test_fuyao_surrogates_rejected_before_capture(self):
        for data in ({"label": "\ud800"}, {"\udfff": "value"}, {"items": ["\ud800"]}):
            payload = {"code": 0, "message": "ok", "request_id": "id", "data": data}
            with self.assertRaises(cli.MoneyCraftError) as caught:
                fuyao_client.parse_json(json.dumps(payload).encode())
            self.assertEqual(caught.exception.exit_code, cli.EXIT_SCHEMA)
        good = {"code": 0, "message": "中文", "request_id": "id", "data": {"label": "😀"}}
        self.assertEqual(fuyao_client.parse_json(json.dumps(good).encode()), good)

    def test_upper_date_range_and_leap_year(self):
        cli.validate_range("9999-01-01", "9999-01-02", max_years=10)
        cli.validate_range("2024-02-29", "2025-02-28", max_years=1)
        with self.assertRaises(cli.MoneyCraftError):
            cli.validate_range("2024-02-29", "2025-03-01", max_years=1)

    def test_json_runtime_errors_are_structured(self):
        for raw in ('{"value":' + '9' * 5000 + '}',):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/"input.json"
                path.write_text(raw)
                with self.assertRaises(research_run.ResearchRunError):
                    research_run.load_json(path)
                with self.assertRaises(tracking_workflow.TrackingError):
                    tracking_workflow.read_json(path, "fixture")
