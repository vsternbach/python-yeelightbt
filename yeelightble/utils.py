import logging
import time

logger = logging.getLogger(__name__)


def throttle(interval=0.5):
    def decorator(func):
        last_invocation = {}

        def throttled(*args, **kwargs):
            key = (func, *args, frozenset(kwargs.items()))
            current_time = time.time()
            if key not in last_invocation or current_time - last_invocation[key] >= interval:
                last_invocation[key] = current_time
                return func(*args, **kwargs)
            else:
                logger.debug(f'Skipping invocation for {key}')
        return throttled
    return decorator
