
class DiskEvaluator:

    @staticmethod
    def evaluate(disk):
        if disk["PartitionStyle"] != "MBR":
            return "NEEDS_PREPARATION"

        if disk["OperationalStatus"] != "Online":
            return "NEEDS_PREPARATION"

        return "READY"
