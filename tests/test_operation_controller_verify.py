import unittest
from types import SimpleNamespace

from core.operation_controller import OperationController
from models.pipeline_error import PipelineError


class OperationControllerVerifyTests(unittest.TestCase):
    def setUp(self):
        self.controller = OperationController()
        self.operation_id = "format-7"

    def _disk(self, *, partition_style="MBR", partitions=None, volumes=None, number=7):
        return SimpleNamespace(
            number=number,
            partition_style=partition_style,
            partitions=partitions if partitions is not None else [{"PartitionNumber": 1}],
            volumes=volumes if volumes is not None else [{"FileSystem": "FAT32", "DriveLetter": "E"}],
        )

    def test_partition_style_mismatch_raises_vfy_001(self):
        disk = self._disk(partition_style="GPT")
        with self.assertRaises(PipelineError) as ctx:
            self.controller._verify_post_conditions(disk, "FAT32", {"Success": True}, self.operation_id)
        self.assertEqual(ctx.exception.code, "MS-VFY-001")

    def test_missing_volume_raises_vfy_002(self):
        disk = self._disk(volumes=[])
        with self.assertRaises(PipelineError) as ctx:
            self.controller._verify_post_conditions(disk, "FAT32", {"Success": True}, self.operation_id)
        self.assertEqual(ctx.exception.code, "MS-VFY-002")

    def test_filesystem_mismatch_raises_vfy_003(self):
        disk = self._disk(volumes=[{"FileSystem": "EXFAT", "DriveLetter": "E"}])
        with self.assertRaises(PipelineError) as ctx:
            self.controller._verify_post_conditions(disk, "FAT32", {"Success": True}, self.operation_id)
        self.assertEqual(ctx.exception.code, "MS-VFY-003")

    def test_block_size_mismatch_raises_vfy_004(self):
        disk = self._disk()
        with self.assertRaises(PipelineError) as ctx:
            self.controller._verify_post_conditions(
                disk,
                "FAT32",
                {"Success": True, "FileSystem": "FAT32", "BlockSize": 4096, "DriveLetter": "E"},
                self.operation_id,
            )
        self.assertEqual(ctx.exception.code, "MS-VFY-004")

    def test_verify_success_passes(self):
        disk = self._disk()
        self.controller._verify_post_conditions(
            disk,
            "FAT32",
            {"Success": True, "FileSystem": "FAT32", "BlockSize": 32768, "DriveLetter": "E"},
            self.operation_id,
        )


if __name__ == "__main__":
    unittest.main()
