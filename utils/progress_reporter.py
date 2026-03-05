class ProgressReporter:
    def __init__(self):
        self.percent = 0
        self.label = "INIT"

    def set(self, percent: int, label: str) -> None:
        self.percent = int(percent)
        self.label = str(label)
        print(f"[PROGRESS] {self.percent:>3}% - {self.label}")
