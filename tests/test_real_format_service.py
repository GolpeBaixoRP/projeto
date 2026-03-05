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
    def test_success_parses_json_only_from_stdout(self, run_mock):
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
    def test_invalid_json_raises_pipeline_error(self, run_mock):
        run_mock.return_value = RunResult(0, "noise", "", 100)
        with self.assertRaises(PipelineError):
            self.service.format_disk(self.disk, "FAT32")

    @patch("services.real_format_service.run_powershell_capture")
    def test_failure_exit_code_raises(self, run_mock):
        run_mock.return_value = RunResult(1, "", "Acesso negado", 100)
        with self.assertRaises(PipelineError):
            self.service.format_disk(self.disk, "FAT32")


if __name__ == "__main__":
    unittest.main()
