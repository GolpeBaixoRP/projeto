from domain.format_profile import FormatProfile


PROFILE_PS2_OPL_FAT32_MBR = FormatProfile(
    id="ps2-opl-fat32-mbr",
    filesystem="FAT32",
    partition_style="MBR",
    worker_ps1="fat32_process.ps1",
)

PROFILE_EXFAT_OPL_MODERN_MBR = FormatProfile(
    id="opl-modern-exfat-mbr",
    filesystem="EXFAT",
    partition_style="MBR",
    worker_ps1="xfat_process.ps1",
)

FILESYSTEM_TO_PROFILE = {
    PROFILE_PS2_OPL_FAT32_MBR.filesystem: PROFILE_PS2_OPL_FAT32_MBR,
    PROFILE_EXFAT_OPL_MODERN_MBR.filesystem: PROFILE_EXFAT_OPL_MODERN_MBR,
}

DEFAULT_PROFILE = PROFILE_PS2_OPL_FAT32_MBR
