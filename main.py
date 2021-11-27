from producer import produce
from worker import dispatch_workers

from multiprocessing import Queue

from multiprocessing import RawValue, Lock

class Counter(object):
    def __init__(self, value=0):
        # RawValue because we don't need it to create a Lock:
        self.val = RawValue('i', value)
        self.lock = Lock()

    def increment(self):
        with self.lock:
            self.val.value += 1

    def decrement(self):
        with self.lock:
            self.val.value -= 1

    def value(self):
        with self.lock:
            return self.val.value

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    q = Queue()
    counter = Counter(0)

    dispatch_workers((q, counter))

    produce((q, counter))
