"""
Utilities for polling, retrying, and exception handling.
"""
import collections
import time
from functools import wraps


def poll(until, timeout=15, interval=1):
    """
    Decorator for functions that should be repeated until a condition
    or a timeout.

    :param until: The success condition.
        ``until`` should be a function; it will be called with
        the return value of the function.
        ``until`` should return ``True`` if the operation was successful
        (and retrying should stop) and ``False`` if retrying should continue.
    :param float timeout: How long to keep retrying the operation in seconds
    :param float interval: How long to sleep between attempts in seconds

    :return: The final return value of the decorated function

    >>> class TestPoll:
    ...     def __init__(self):
    ...         self.x = 0
    ...
    ...     @poll(lambda x: x == 3, interval=0.01)
    ...     def test(self):
    ...         print(self.x)
    ...         self.x += 1
    ...         return self.x
    ...
    >>> TestPoll().test()
    0
    1
    2
    3
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return poll_(f, until, timeout, interval, *args, **kwargs)
        return wrapper
    return decorator


def poll_(f, until, timeout=15, interval=1, *args, **kwargs):
    """
    Repeatedly call a function until a condition becomes
    true or a timeout expires.

    :param f: The function to poll
    :param until: The success condition.
        ``until`` should be a function; it will be called with
        the return value of the function.
        ``until`` should return ``True`` if the operation was successful
        (and retrying should stop) and ``False`` if retrying should continue.
    :param float timeout: How long to keep retrying the operation in seconds
    :param float interval: How long to sleep in between attempts in seconds

    Any other arguments are forwarded to ``f``.

    :return: The final return value of the function ``f``.
    """
    return exec_(f, (), until, float("inf"), timeout, interval, *args, **kwargs)


def retry(ex, times=3, interval=1):
    """
    Decorator for functions that should be retried upon error.

    :param ex: The class of the exception to catch, or an iterable of classes
    :param times: The maximum number of times to retry
    :param interval: The amount of time to sleep between retries

    :return: The return value of the decorated function
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return retry_(f, ex, times, interval, *args, **kwargs)
        return wrapper
    return decorator


def retry_(f, ex, times=3, interval=1, *args, **kwargs):
    """
    Call a function and try again if it throws a specified exception.

    :param f: The function to retry
    :param ex: The class of the exception to catch, or an iterable of classes
    :param times: The maximum number of times to retry
    :param interval: The amount of time to sleep between retries

    Any other arguments are forwarded to ``f``.

    :return: The final return value of the function ``f``.
    """
    return exec_(f, ex, lambda _: True, times, float("inf"), interval, *args, **kwargs)


def exec_(f, ex, until, times=3, timeout=15, interval=1, *args, **kwargs):
    """
    General function for polling, retrying, and handling errors.

    :param f: The function to retry
    :param ex: The class of the exception to catch, or an iterable of classes
    :param until: The success condition.
        ``until`` should be a function; it will be called with
        the return value of the function.
        ``until`` should return ``True`` if the operation was successful
        (and retrying should stop) and ``False`` if retrying should continue.
    :param times: The maximum number of times to retry
    :param interval: The amount of time to sleep between retries

    Any other arguments are forwarded to ``f``.

    :return: The final return value of the function ``f``.
    """
    if isinstance(ex, collections.Iterable):
        exs = tuple(ex)
    else:
        exs = (ex,)

    count = 0
    start_time = time.perf_counter()
    while True:
        try:
            result = f(*args, **kwargs)
            if until(result):
                return result
        except BaseException as e:
            count += 1
            if count >= times or not isinstance(e, exs):
                raise
        time.sleep(interval)
        if time.perf_counter() - start_time > timeout:
            raise TimeoutError("The operation {} timed out after {} seconds".format(f.__name__, timeout))
