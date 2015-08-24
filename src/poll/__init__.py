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

    :param function until: The success condition.
        ``until`` should be a function; it will be called with
        the return value of the function.
        ``until`` should return ``True`` if the operation was successful
        (and retrying should stop) and ``False`` if retrying should continue.
    :param float timeout: How long to keep retrying the operation in seconds
    :param float interval: How long to sleep between attempts in seconds

    :return: The final return value of the decorated function
    :raises TimeoutError: The condition did not become true
        within the specified timeout.
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

    :param function f: The function to poll
    :param function until: The success condition.
        ``until`` should be a function; it will be called with
        the return value of the function.
        ``until`` should return ``True`` if the operation was successful
        (and retrying should stop) and ``False`` if retrying should continue.
    :param float timeout: How long to keep retrying the operation in seconds
    :param float interval: How long to sleep in between attempts in seconds

    Any other arguments are forwarded to ``f``.

    :return: The final return value of the function ``f``.
    :raises TimeoutError: The condition did not become true
        within the specified timeout.
    """
    return exec_(f, (), until, float("inf"), timeout, interval, lambda e, x: None, *args, **kwargs)


def retry(ex, times=3, interval=1, on_error=lambda e, x: None):
    """
    Decorator for functions that should be retried upon error.

    :param ex: The class of the exception to catch, or an iterable of classes
    :type ex: class or iterable
    :param int times: The maximum number of times to retry
    :param float interval: How long to sleep in between attempts in seconds
    :param function on_error: A function to be called when the decorated
        function throws an exception.

        If ``on_error()`` takes no parameters,
        it will be called without arguments.

        If ``on_error(exception)`` takes one parameter,
        it will be called with the exception that was raised.

        If ``on_error(exception, retry_count)`` takes two parameters,
        it will be called with the exception that was raised and
        the number of previous attempts (starting at 0).

        A typical use of ``on_error`` would be to log the exception.

    :return: The return value of the decorated function
    :raises TimeoutError: The function did not succeed
        within the specified timeout.
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

    :param funciton f: The function to retry
    :param ex: The class of the exception to catch, or an iterable of classes
    :type ex: class or iterable
    :param int times: The maximum number of times to retry
    :param float interval: How long to sleep in between attempts in seconds
    :param function on_error: A function to be called when
        ``f`` throws an exception.

        If ``on_error()`` takes no parameters, it will be called
        without arguments.

        If ``on_error(exception)`` takes one parameter,
        it will be called with the exception that was raised.

        If ``on_error(exception, retry_count)`` takes two parameters,
        it will be called with the exception that was raised and the
        number of previous attempts (starting at 0).

        A typical use of ``on_error`` would be to log the exception.

    Any other arguments are forwarded to ``f``.

    :return: The final return value of the function ``f``.
    :raises TimeoutError: The function did not succeed
        within the specified timeout.
    """
    return exec_(f, ex, lambda _: True, times, float("inf"), interval, on_error, *args, **kwargs)


def circuitbreaker(ex, threshold, reset_timeout, on_error=lambda e: None):
    """
    Decorator for functions which should 'back off' using the
    Circuit Breaker pattern: http://martinfowler.com/bliki/CircuitBreaker.html

    This implementation of Circuit Breaker uses a 'leaky bucket' form
    of failure counting. For example, if `threshold` is 3 and
    `reset_timeout` is 60, then the circuit will be broken if the call
    fails three times *within a sixty-second period*. The circuit breaker
    is lenient towards intermittent failures.

    :param ex: The class of the exception to catch, or an iterable of classes.
    :type ex: class or iterable
    :param int threshold: The number of times a failure can occur before
        the circuit is broken.
    :param float reset_timeout: The length of time, in seconds,
        that a broken circuit should remain broken.
    :param function on_error: A function to be called when the
        decorated function throws an exception.

        If ``on_error()`` takes no parameters,
        it will be called without arguments.

        If ``on_error(exception)`` takes one parameter,
        it will be called with the exception that was raised.

        A typical use of ``on_error`` would be to log the exception.

    :return: The final return value of the function ``f``.
    :raises CircuitBrokenError: The operation was
        not carried out because the circuit is broken.
    """

    if isinstance(ex, collections.Iterable):
        exs = tuple(ex)
    else:
        exs = (ex,)

    def decorator(f):
        failure_counter = _FailureCounter(threshold, reset_timeout)

        @wraps(f)
        def wrapper(*args, **kwargs):
            state = failure_counter.state()
            if state == "broken":
                time_remaining = failure_counter.time_remaining()
                message = "The circuit for {} was broken. Try again in {}".format(f.__name__, time_remaining)
                raise CircuitBrokenError(message, time_remaining)

            try:
                result = f(*args, **kwargs)
            except BaseException as e:
                _call_with_correct_number_of_args(on_error, (e,))
                if isinstance(e, exs):
                    failure_counter.add_failure()
                raise
            failure_counter.add_success()
            return result

        return wrapper
    return decorator


class _FailureCounter(object):
    def __init__(self, threshold, timeout):
        self._failure_times = collections.deque()
        self._threshold = threshold
        self._timeout = timeout
        self._broken_time = None

    def state(self):
        if self._broken_time is not None:
            if self._is_halfbroken():
                return "halfbroken"
            return "broken"
        return "ok"

    def add_failure(self):
        self._update_failures()
        self._failure_times.append(time.perf_counter())
        if len(self._failure_times) >= self._threshold or self._is_halfbroken():
            self._broken_time = time.perf_counter()

    def add_success(self):
        if self._is_halfbroken():
            self._failure_times = collections.deque()
        self._update_failures()
        self._broken_time = None

    def time_remaining(self):
        if self._broken_time is None:
            return 0
        result = self._timeout - self._time_since_broken()
        return result if result > 0 else 0

    def _is_halfbroken(self):
        return self._broken_time is not None and self._time_since_broken() >= self._timeout

    def _time_since_broken(self):
        return time.perf_counter() - self._broken_time

    def _update_failures(self):
        current_time = time.perf_counter()
        while self._failure_times and self._failure_times[0] < (current_time - self._timeout):
            result = self._failure_times.popleft()
            print(result, self._failure_times[0] if self._failure_times else None)


def exec_(f, ex, until, times=3, timeout=15, interval=1, on_error=lambda e, x: None, *args, **kwargs):
    """
    General function for polling, retrying, and handling errors.

    :param function f: The function to retry
    :param ex: The class of the exception to catch, or an iterable of classes
    :type ex: class or iterable
    :param function until: The success condition.
        ``until`` should be a function; it will be called with
        the return value of the function.
        ``until(x)`` should return ``True`` if the operation was successful
        (and retrying should stop) and ``False`` if retrying should continue.
    :param int times: The maximum number of times to retry
    :param float interval: How long to sleep in between attempts in seconds
    :param function on_error: A function to be called when ``f`` throws an exception.

        If ``on_error()`` takes no parameters,
        it will be called without arguments.

        If ``on_error(exception)`` takes one parameter,
        it will be called with the exception that was raised.

        If ``on_error(exception, retry_count)`` takes two parameters,
        it will be called with the exception that was raised and the
        number of previous attempts (starting at 0).

        A typical use of ``on_error`` would be to log the exception.

    Any other arguments are forwarded to ``f``.

    :return: The final return value of the function ``f``.
    :raises TimeoutError: The call did not succeed
        within the specified timeout.
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
            _call_with_correct_number_of_args(on_error, (e, count))
            count += 1
            if count >= times or not isinstance(e, exs):
                raise
        else:
            if until(result):
                return result
        time.sleep(interval)
        if time.perf_counter() - start_time > timeout:
            msg = "The operation '{}' timed out after {} seconds and {} attempts".format(
                f.__name__,
                timeout,
                count
            )
            raise TimeoutError(msg)


class CircuitBrokenError(Exception):
    """
    Exception to indicate that the operation was
    not carried out because the circuit is broken.
    """
    def __init__(self, message="", time_remaining=0):
        super().__init__(message)
        self.time_remaining = time_remaining


def _call_with_correct_number_of_args(f, args):
    arg_count = len(inspect.signature(f).parameters)
    f(*args[:arg_count])
