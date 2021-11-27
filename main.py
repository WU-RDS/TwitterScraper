from producer import produce
from worker import dispatch_workers
from multiprocessing import Queue
from utils import Counter

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    q = Queue()
    counter = Counter(0)

    dispatch_workers((q, counter))

    produce((q, counter))
