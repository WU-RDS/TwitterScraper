from multiprocessing import RawValue, Lock
import json
from hashlib import md5


def hash_dict(dct):
    if dct == None:
        return 'None'
    dct['keywords'].sort()
    dct_dumped = json.dumps(dct, sort_keys=True).encode('utf-8')
    return md5(dct_dumped).hexdigest()[0:7]


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
