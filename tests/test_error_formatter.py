import unittest

from models.pipeline_error import PipelineError
from utils.error_formatter import format_detailed, format_short, format_structured


class ErrorFormatterTests(unittest.TestCase):
    def test_format_short_with_complete_error(self):
        err = PipelineError(
            code="MS-VFY-004",
            stage="verify",
            message="Cluster mismatch",
            substep="block_size",
        )
        text = format_short(err)
        self.assertIn("[MS-VFY-004]", text)
        self.assertIn("VERIFY.BLOCK_SIZE", text)

    def test_format_short_with_missing_optional_fields(self):
        err = PipelineError(code="MS-SYS-001", stage="system", message="admin required", substep=None)
        text = format_short(err)
        self.assertIn("[MS-SYS-001]", text)
        self.assertIn("SYSTEM", text)

    def test_format_detailed_with_complete_error(self):
        err = PipelineError(
            code="MS-VFY-003",
            stage="verify",
            message="Filesystem mismatch",
            substep="filesystem",
            expected="FAT32",
            found="EXFAT",
            disk_number=3,
            drive_letter="E:",
            operation_id="format-3",
            severity_level=3,
            severity_label="ERROR",
        )
        text = format_detailed(err)
        self.assertIn("Código: MS-VFY-003", text)
        self.assertIn("Stage: verify", text)
        self.assertIn("Substep: filesystem", text)
        self.assertIn("- Esperado: FAT32", text)
        self.assertIn("- Encontrado: EXFAT", text)
        self.assertIn("Disco: 3", text)
        self.assertIn("Unidade: E:", text)
        self.assertIn("Operação: format-3", text)

    def test_format_detailed_with_none_fields_uses_fallback(self):
        err = PipelineError(code="MS-CFG-001", stage="config", message="", substep=None)
        text = format_detailed(err)
        self.assertIn("Substep: N/A", text)
        self.assertIn("- Esperado: N/A", text)
        self.assertIn("- Encontrado: N/A", text)
        self.assertIn("Disco: N/A", text)

    def test_format_structured_with_complete_error(self):
        err = PipelineError(
            code="MS-VFY-004",
            stage="verify",
            message="Block size mismatch",
            substep="block_size",
            expected=32768,
            found=4096,
            disk_number=7,
            drive_letter="G:",
            operation_id="format-7",
            timestamp="2026-01-01T00:00:00+00:00",
        )
        data = format_structured(err)
        self.assertEqual(data["error_code"], "MS-VFY-004")
        self.assertEqual(data["stage"], "verify")
        self.assertEqual(data["substep"], "block_size")
        self.assertEqual(data["expected"], 32768)
        self.assertEqual(data["found"], 4096)
        self.assertEqual(data["disk_number"], 7)
        self.assertEqual(data["drive_letter"], "G:")
        self.assertEqual(data["operation_id"], "format-7")
        self.assertEqual(data["timestamp"], "2026-01-01T00:00:00+00:00")

    def test_format_structured_with_missing_fields_is_stable(self):
        err = PipelineError(code="MS-SNP-001", stage="snapshot", message="snap failed")
        data = format_structured(err)
        self.assertIn("error_code", data)
        self.assertIsNone(data["expected"])
        self.assertIsNone(data["found"])
        self.assertIsNone(data["disk_number"])
        self.assertIsNone(data["drive_letter"])

    def test_catalog_fallback_when_code_not_found(self):
        err = PipelineError(code="MS-UNK-999", stage="verify", message="mensagem fallback", substep="x")
        self.assertIn("mensagem fallback", format_short(err))
        self.assertIn("Resumo: mensagem fallback", format_detailed(err))
        data = format_structured(err)
        self.assertEqual(data["error_code"], "MS-UNK-999")


if __name__ == "__main__":
    unittest.main()
