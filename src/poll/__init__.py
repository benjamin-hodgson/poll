"""
Utilities for polling, retrying, and exception handling.
"""
import collections
import inspect
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
    return exec_(f, (), until, float("inf"), timeout, interval, lambda e, x: None, *args, **kwargs)


def retry(ex, times=3, interval=1, on_error=lambda e, x: None):
    """
    Decorator for functions that should be retried upon error.

    :param ex: The class of the exception to catch, or an iterable of classes
    :param times: The maximum number of times to retry
    :param interval: The amount of time to sleep between retries
    :param on_error: A function to be called when the decorated
        function throws an exception.
        * If ``on_error()`` takes no parameters, it will be called without arguments.
        * If ``on_error(exception)`` takes one parameter,
          it will be called with the exception that was raised.
        * If ``on_error(exception, retry_count)`` takes two parameters,
          it will be called with the exception that was raised and the number
          of previous attempts (starting at 0).
        A typical use of ``on_error`` would be to log the exception.

    :return: The return value of the decorated function
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return retry_(f, ex, times, interval, on_error, *args, **kwargs)
        return wrapper
    return decorator


def retry_(f, ex, times=3, interval=1, on_error=lambda e, x: None, *args, **kwargs):
    """
    Call a function and try again if it throws a specified exception.

    :param f: The function to retry
    :param ex: The class of the exception to catch, or an iterable of classes
    :param times: The maximum number of times to retry
    :param interval: The amount of time to sleep between retries
    :param on_error: A function to be called when ``f`` throws an exception.
        * If ``on_error()`` takes no parameters, it will be called without arguments.
        * If ``on_error(exception)`` takes one parameter,
          it will be called with the exception that was raised.
        * If ``on_error(exception, retry_count)`` takes two parameters,
          it will be called with the exception that was raised and the number
          of previous attempts (starting at 0).
        A typical use of ``on_error`` would be to log the exception.

    Any other arguments are forwarded to ``f``.

    :return: The final return value of the function ``f``.
    """
    return exec_(f, ex, lambda _: True, times, float("inf"), interval, on_error, *args, **kwargs)


def circuitbreaker(ex, threshold, reset_timeout):
    def decorator(f):
        failure_counter = FailureCounter(reset_timeout)

        @wraps(f)
        def wrapper(*args, **kwargs):
            if failure_counter.count() > threshold:
                raise CircuitBrokenError

            try:
                result = f(*args, **kwargs)
            except:
                failure_counter.add_failure()
                raise
            return result
        wrapper.failure_count = lambda: failure_counter.count()

        return wrapper
    return decorator


class FailureCounter(object):
    def __init__(self, timeout):
        self._failure_times = []
        self._timeout = timeout

    def add_failure(self):
        self._failure_times.append(time.perf_counter())

    def count(self):
        current_time = time.perf_counter()
        return len([x for x in self._failure_times if current_time - x < self._timeout])


def exec_(f, ex, until, times=3, timeout=15, interval=1, on_error=lambda e, x: None, *args, **kwargs):
    """
    General function for polling, retrying, and handling errors.

    :param f: The function to retry
    :param ex: The class of the exception to catch, or an iterable of classes
    :param until: The success condition.
        ``until`` should be a function; it will be called with
        the return value of the function.
        ``until(x)`` should return ``True`` if the operation was successful
        (and retrying should stop) and ``False`` if retrying should continue.
    :param times: The maximum number of times to retry
    :param interval: The amount of time to sleep between retries
    :param on_error: A function to be called when ``f`` throws an exception.
        * If ``on_error()`` takes no parameters, it will be called without arguments.
        * If ``on_error(exception)`` takes one parameter,
          it will be called with the exception that was raised.
        * If ``on_error(exception, retry_count)`` takes two parameters,
          it will be called with the exception that was raised and the number
          of previous attempts (starting at 0).
        A typical use of ``on_error`` would be to log the exception.

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
        except BaseException as e:
            # if on_error takes 0, 1 or 2 arguments, supply none, one, or both of (e, count)
            arg_count = len(inspect.signature(on_error).parameters)
            on_error(*(e, count)[:arg_count])
            count += 1
            if count >= times or not isinstance(e, exs):
                raise
        else:
            if until(result):
                return result
        time.sleep(interval)
        if time.perf_counter() - start_time > timeout:
            raise TimeoutError("The operation {} timed out after {} seconds".format(f.__name__, timeout))


class CircuitBrokenError(Exception):
    pass
