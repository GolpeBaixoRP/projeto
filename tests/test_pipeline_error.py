import unittest

from models.pipeline_error import PipelineError


class PipelineErrorTests(unittest.TestCase):
    def test_creation_with_minimum_fields(self):
        err = PipelineError(code="MS-VFY-003", stage="verify", message="Filesystem mismatch")
        self.assertEqual(err.code, "MS-VFY-003")
        self.assertEqual(err.stage, "verify")
        self.assertEqual(err.message, "Filesystem mismatch")
        self.assertIsInstance(err.details, dict)
        self.assertIsNotNone(err.timestamp)

    def test_creation_with_all_optional_fields(self):
        err = PipelineError(
            code="MS-VFY-004",
            stage="verify",
            message="Block size mismatch",
            details={"k": "v"},
            substep="block_size",
            severity_level=3,
            severity_label="ERROR",
            retryable=False,
            expected=32768,
            found=4096,
            disk_number=3,
            drive_letter="E:",
            operation_id="format-3",
            cause_hint="worker-cluster",
            timestamp="2026-01-01T00:00:00+00:00",
        )
        self.assertEqual(err.substep, "block_size")
        self.assertEqual(err.expected, 32768)
        self.assertEqual(err.found, 4096)
        self.assertEqual(err.timestamp, "2026-01-01T00:00:00+00:00")

    def test_to_dict_contains_expected_keys(self):
        err = PipelineError(code="MS-IPC-003", stage="format", message="invalid json")
        data = err.to_dict()
        expected_keys = {
            "code",
            "stage",
            "message",
            "details",
            "substep",
            "severity_level",
            "severity_label",
            "retryable",
            "expected",
            "found",
            "disk_number",
            "drive_letter",
            "operation_id",
            "cause_hint",
            "timestamp",
        }
        self.assertEqual(set(data.keys()), expected_keys)

    def test_timestamp_is_auto_generated(self):
        err = PipelineError(code="MS-SEL-002", stage="selection", message="blocked")
        self.assertIsInstance(err.timestamp, str)
        self.assertIn("T", err.timestamp)


if __name__ == "__main__":
    unittest.main()
