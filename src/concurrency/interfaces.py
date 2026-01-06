class IWorker:
    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def submit_task(self, task):
        raise NotImplementedError

class ITaskScheduler:
    def submit(self, task):
        raise NotImplementedError