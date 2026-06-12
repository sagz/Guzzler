import multiprocessing

class BatchedProgressTracker:
    """
    A reusable utility class to track progress safely across processes 
    using a shared multiprocessing.Value, batching updates locally 
    to reduce lock contention.
    """
    def __init__(self, shared_counter, lock=None, threshold=10 * 1024 * 1024):
        self.shared_counter = shared_counter
        self.lock = lock if lock is not None else shared_counter.get_lock()
        self.threshold = threshold
        self.local_count = 0

    def update(self, byte_count):
        """
        Add byte_count to the local accumulator. 
        If it exceeds the threshold, flush to the shared counter.
        """
        self.local_count += byte_count
        if self.local_count >= self.threshold:
            self.flush()

    def flush(self):
        """
        Force synchronize any remaining local accumulated bytes to the global counter.
        """
        if self.local_count > 0:
            with self.lock:
                self.shared_counter.value += self.local_count
            self.local_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()
