import time
import json
from hashlib import md5


def hash_dict(dct):
    dct['keywords'].sort()
    dct_dumped = json.dumps(dct, sort_keys=True).encode('utf-8')
    return md5(dct_dumped).hexdigest()[0:7]
