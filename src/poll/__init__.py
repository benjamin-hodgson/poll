"""
Utilities for polling, retrying, and exception handling.
"""
import functools
import time


def poll(until, timeout=15, interval=1):
    """
    Decorator for functions that should be retried until a condition
    or a timeout.

    :param until: Called with the return value of the function;
        return True if the operation was successful (and retrying should stop)
    :param float timeout: How long to keep retrying the operation in seconds
    :param float interval: How long to sleep in between attempts in seconds

    >>> class TestPoll:
    ...     def __init__(self):
    ...         self.x = 0
    ...     @poll(lambda x: x == 3, interval=0.01)
    ...     def test(self):
    ...         print(self.x)
    ...         self.x += 1
    ...         return self.x
    >>> TestPoll().test()
    0
    1
    2
    3
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            result = None
            start_time = time.perf_counter()
            while result is None or not until(result):
                result = f(*args, **kwargs)
                time.sleep(interval)
                if time.perf_counter() - start_time > timeout:
                    raise TimeoutError("The operation {} timed out after {} seconds".format(f.__name__, timeout))
            return result
        return wrapper
    return decorator
