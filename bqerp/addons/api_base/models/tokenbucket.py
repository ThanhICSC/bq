import redis
from redis import WatchError
import time

RATE = 0.1
DEFAULT = 10
TIMEOUT = 60*60

r = redis.Redis(host='localhost', port=6379, db=0)


def token_bucket(tokens, key):
    pipe = r.pipeline()
    while 1:
        try:
            pipe.watch('%s:available' % key)
            pipe.watch('%s:ts' % key)

            current_ts = time.time()

            old_tokens = pipe.get('%s:available' % key)
            if old_tokens is None:
                current_tokens = DEFAULT
            else:
                old_ts = pipe.get('%s:ts' % key)
                current_tokens = float(old_tokens) + min(
                    (current_ts - float(old_ts)) * RATE,
                    DEFAULT - float(old_tokens)
                )

            if 0 <= tokens <= current_tokens:
                current_tokens -= tokens
                consumes = True
            else:
                consumes = False

            pipe.multi()
            pipe.set('%s:available' % key, current_tokens)
            pipe.expire('%s:available' % key, TIMEOUT)
            pipe.set('%s:ts' % key, current_ts)
            pipe.expire('%s:ts' % key, TIMEOUT)
            pipe.execute()
            break
        except WatchError:
            continue
        finally:
            pipe.reset()
    return consumes
