import multiprocessing
from core.real_formatter_service import RealFormatterService


class FormatterWorker:

    def __init__(self):
        self.queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(
            target=self.worker_loop,
            daemon=True
        )

    def start(self):
        self.process.start()

    def worker_loop(self):

        formatter = RealFormatterService()

        while True:

            task = self.queue.get()

            if task is None:
                break

            disk, filesystem = task

            formatter.format_disk(disk, filesystem)

    def format(self, disk, filesystem):
        self.queue.put((disk, filesystem))