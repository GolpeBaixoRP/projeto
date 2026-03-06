import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from models.pipeline_error import PipelineError
from services.real_format_service import RealFormatterService
from utils.powershell_runner import RunResult


class RealFormatterServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = RealFormatterService()
        self.disk = SimpleNamespace(number=7, unique_id="u", serial_number="s", size=1, friendly_name="d", bus_type="USB", location_path="lp")

    @patch("services.real_format_service.run_powershell_capture")
    def test_success_parses_json_with_minimum_contract(self, run_mock):
        payload = {
            "Success": True,
            "DriveLetter": "G",
            "FileSystem": "FAT32",
            "PartitionStyle": "MBR",
            "ExecutionTimeMs": 1200,
            "RebuildPerformed": False,
            "ErrorCode": 0,
            "ErrorMessage": None,
            "BlockSize": 32768,
        }
        run_mock.return_value = RunResult(0, json.dumps(payload), "", 100)

        result = self.service.format_disk(self.disk, "FAT32")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"]["FileSystem"], "FAT32")

    @patch("services.real_format_service.run_powershell_capture")
    def test_success_parses_json_with_extra_fields(self, run_mock):
        payload = {
            "Success": True,
            "DriveLetter": "G",
            "FileSystem": "FAT32",
            "PartitionStyle": "MBR",
            "ExecutionTimeMs": 1200,
            "RebuildPerformed": True,
            "ErrorCode": 0,
            "ErrorMessage": None,
            "PipelineErrorCode": None,
            "BlockSize": 32768,
            "Step": "verify",
            "Expected": "FAT32",
            "Found": "FAT32",
        }
        run_mock.return_value = RunResult(0, json.dumps(payload), "", 100)

        result = self.service.format_disk(self.disk, "FAT32")

        self.assertEqual(result["status"], "success")
        self.assertIn("Step", result["data"])

    @patch("services.real_format_service.run_powershell_capture")
    def test_stdout_empty_raises_ipc_001(self, run_mock):
        run_mock.return_value = RunResult(0, "", "", 100)
        with self.assertRaises(PipelineError) as ctx:
            self.service.format_disk(self.disk, "FAT32")
        self.assertEqual(ctx.exception.code, "MS-IPC-001")

    @patch("services.real_format_service.run_powershell_capture")
    def test_invalid_json_raises_ipc_002_or_003(self, run_mock):
        run_mock.return_value = RunResult(0, "noise", "", 100)
        with self.assertRaises(PipelineError) as ctx:
            self.service.format_disk(self.disk, "FAT32")
        self.assertIn(ctx.exception.code, {"MS-IPC-002", "MS-IPC-003"})

    @patch("services.real_format_service.run_powershell_capture")
    def test_success_false_raises_worker_failure(self, run_mock):
        payload = {
            "Success": False,
            "DriveLetter": "G",
            "FileSystem": "FAT32",
            "PartitionStyle": "MBR",
            "ExecutionTimeMs": 1200,
            "RebuildPerformed": False,
            "ErrorCode": 41,
            "ErrorMessage": "formatter failed",
            "PipelineErrorCode": "MS-FMT-001",
        }
        run_mock.return_value = RunResult(0, json.dumps(payload), "", 100)

        with self.assertRaises(PipelineError) as ctx:
            self.service.format_disk(self.disk, "FAT32")

        self.assertEqual(ctx.exception.code, "MS-FMT-001")

    @patch("services.real_format_service.run_powershell_capture")
    def test_failure_exit_code_raises_runner_code(self, run_mock):
        run_mock.return_value = RunResult(1, "", "Acesso negado", 100)
        with self.assertRaises(PipelineError) as ctx:
            self.service.format_disk(self.disk, "FAT32")
        self.assertEqual(ctx.exception.code, "MS-RUN-003")


if __name__ == "__main__":
    unittest.main()
