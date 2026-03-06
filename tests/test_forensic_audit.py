import json
import tempfile
import unittest
from pathlib import Path

from utils.forensic_audit import ForensicAuditTrail


class ForensicAuditTrailTests(unittest.TestCase):
    def test_basic_event_creation_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            trail = ForensicAuditTrail(root_dir=tmp)
            trail.record("event_basic", {"k": "v"})
            path = Path(tmp) / "forensic_audit.jsonl"
            rows = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(rows), 1)
            payload = json.loads(rows[0])
            self.assertEqual(payload["event"], "event_basic")
            self.assertEqual(payload["payload"], {"k": "v"})

    def test_event_with_optional_forensic_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            trail = ForensicAuditTrail(root_dir=tmp)
            trail.record(
                "event_opt",
                {"a": 1},
                operation_id="op-1",
                substep="verify",
                disk_number=7,
                drive_letter="E:",
                expected="FAT32",
                found="EXFAT",
                duration_ms=123,
                stdout_tail="out",
                stderr_tail="err",
            )
            row = json.loads((Path(tmp) / "forensic_audit.jsonl").read_text(encoding="utf-8").strip())
            self.assertEqual(row["operation_id"], "op-1")
            self.assertEqual(row["substep"], "verify")
            self.assertEqual(row["disk_number"], 7)
            self.assertEqual(row["drive_letter"], "E:")
            self.assertEqual(row["expected"], "FAT32")
            self.assertEqual(row["found"], "EXFAT")
            self.assertEqual(row["duration_ms"], 123)
            self.assertEqual(row["stdout_tail"], "out")
            self.assertEqual(row["stderr_tail"], "err")

    def test_tail_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            trail = ForensicAuditTrail(root_dir=tmp)
            long_text = "x" * 1200
            trail.record("event_tail", {}, stdout_tail=long_text, stderr_tail=long_text)
            row = json.loads((Path(tmp) / "forensic_audit.jsonl").read_text(encoding="utf-8").strip())
            self.assertEqual(len(row["stdout_tail"]), 500)
            self.assertEqual(len(row["stderr_tail"]), 500)

    def test_legacy_minimal_call_compatibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            trail = ForensicAuditTrail(root_dir=tmp)
            trail.record("legacy_event", {"legacy": True})
            row = json.loads((Path(tmp) / "forensic_audit.jsonl").read_text(encoding="utf-8").strip())
            self.assertEqual(row["event"], "legacy_event")
            self.assertIsNone(row["operation_id"])

    def test_partial_event_without_optional_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            trail = ForensicAuditTrail(root_dir=tmp)
            trail.record("partial", {"p": 1})
            row = json.loads((Path(tmp) / "forensic_audit.jsonl").read_text(encoding="utf-8").strip())
            self.assertIsNone(row["error_code"])
            self.assertIsNone(row["stage"])
            self.assertIsNone(row["operation_id"])

    def test_append_only_multiple_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            trail = ForensicAuditTrail(root_dir=tmp)
            trail.record("e1", {"i": 1})
            trail.record("e2", {"i": 2})
            rows = (Path(tmp) / "forensic_audit.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(rows), 2)
            self.assertEqual(json.loads(rows[0])["event"], "e1")
            self.assertEqual(json.loads(rows[1])["event"], "e2")


if __name__ == "__main__":
    unittest.main()
