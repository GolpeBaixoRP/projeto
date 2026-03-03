
import subprocess

class Fat32Formatter:

    @staticmethod
    def format(drive_letter):
        process = subprocess.run(
            ["fat32format.exe", f"{drive_letter}:"],
            capture_output=True,
            text=True
        )

        if process.returncode != 0:
            raise RuntimeError("Falha no FAT32Format externo")

        return True
