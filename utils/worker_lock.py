import threading

_GLOBAL_WORKER_LOCK = threading.Lock()

def acquire_worker_lock():
    return _GLOBAL_WORKER_LOCK.acquire(timeout=5)

def release_worker_lock():
    if _GLOBAL_WORKER_LOCK.locked():
        _GLOBAL_WORKER_LOCK.release()