import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.real_format_service import RealFormatterService


class RealFormatterServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = RealFormatterService()
        self.disk = SimpleNamespace(number=7)

    @patch("services.real_format_service.subprocess.run")
    def test_success_parses_json_only_from_stdout(self, run_mock):
        payload = {
            "Success": True,
            "DriveLetter": "G",
            "FileSystem": "FAT32",
            "PartitionStyle": "MBR",
            "ExecutionTimeMs": 1200,
            "RebuildPerformed": False,
            "ErrorCode": None,
            "ErrorMessage": None,
        }
        run_mock.return_value = SimpleNamespace(
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

        result = self.service.format_disk(self.disk, "FAT32")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"], payload)
        # Tabela humana deve ser emitida fora do canal capturado de JSON.
        print("Get-Disk 7 | Format-Table Number,FriendlyName")

    @patch("services.real_format_service.subprocess.run")
    def test_success_with_empty_stdout_does_not_parse_json(self, run_mock):
        run_mock.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch.object(self.service, "_parse_ipc", side_effect=AssertionError("não deve parsear")):
            result = self.service.format_disk(self.disk, "FAT32")

        self.assertEqual(result["status"], "success")
        self.assertIsNone(result["data"])

    @patch("services.real_format_service.subprocess.run")
    def test_failure_includes_exit_code_and_stderr(self, run_mock):
        run_mock.return_value = SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="Acesso negado",
        )

        result = self.service.format_disk(self.disk, "FAT32")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["exit_code"], 1)
        self.assertEqual(result["error"]["stderr"], "Acesso negado")


if __name__ == "__main__":
    unittest.main()
