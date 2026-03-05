class Disk:
    def __init__(self, number, name, partition_style, status):
        self.number = number
        self.name = name
        self.partition_style = partition_style
        self.status = status
        self.partitions = []

class Partition:
    def __init__(self, disk_number, partition_number, drive_letter):
        self.disk_number = disk_number
        self.partition_number = partition_number
        self.drive_letter = drive_letter
        self.filesystem = None
