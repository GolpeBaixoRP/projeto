
from infrastructure.powershell_runner import PowerShellRunner

class DiskSnapshot:

    @staticmethod
    def collect():
        script = '''
        $disks = Get-Disk | Select Number, FriendlyName, PartitionStyle, OperationalStatus, Size
        $result = @{ Disks = $disks }
        $result | ConvertTo-Json -Depth 3
        '''
        return PowerShellRunner.run(script)
