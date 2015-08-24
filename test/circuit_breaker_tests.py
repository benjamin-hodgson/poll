import contexts
from unittest import mock
from poll import circuitbreaker, CircuitBrokenError


class WhenAFunctionWithCircuitBreakerDoesNotThrow:
    def given_a_call_counter(self):
        self.x = 0
        self.expected_args = (1, 4, "hello")
        self.expected_kwargs = {"blah": "bloh", "bleh": 5}
        self.expected_return_value = "some thing that was returned"

    def when_i_call_the_circuit_breaker_function(self):
        self.result = self.function_to_break(*self.expected_args, **self.expected_kwargs)

    def it_should_forward_the_arguments(self):
        assert self.args == self.expected_args

    def it_should_forward_the_keyword_arguments(self):
        assert self.kwargs == self.expected_kwargs

    def it_should_call_it_once(self):
        assert self.x == 1

    def it_should_return_the_result_of_the_function(self):
        assert self.result is self.expected_return_value

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self, *args, **kwargs):
        self.x += 1
        self.args = args
        self.kwargs = kwargs
        return self.expected_return_value


class WhenAFunctionWithCircuitBreakerThrowsOnceAndTheOnErrorCallbackHasNoParams:
    def given_an_exception_to_throw(self):
        self.x = 0
        self.expected_exception = ValueError()

        @circuitbreaker(ValueError, threshold=3, reset_timeout=1, on_error=self.on_error_callback)
        def function_to_break():
            self.x += 1
            raise self.expected_exception
        self.function_to_break = function_to_break

    def when_i_call_the_circuit_breaker_function(self):
        self.exception = contexts.catch(self.function_to_break)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.expected_exception

    def it_should_call_the_function_to_break_once(self):
        assert self.x == 1

    def it_should_call_the_on_error_callback(self):
        assert self.on_error_called

    def on_error_callback(self):
        self.on_error_called = True


class WhenAFunctionWithCircuitBreakerThrowsOnceAndTheOnErrorCallbackHasOneParam:
    def given_an_exception_to_throw(self):
        self.x = 0
        self.expected_exception = ValueError()

        @circuitbreaker(ValueError, threshold=3, reset_timeout=1, on_error=self.on_error_callback)
        def function_to_break():
            self.x += 1
            raise self.expected_exception
        self.function_to_break = function_to_break

    def when_i_call_the_circuit_breaker_function(self):
        self.exception = contexts.catch(self.function_to_break)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.expected_exception

    def it_should_call_the_function_to_break_once(self):
        assert self.x == 1

    def it_should_call_the_on_error_callback(self):
        assert self.on_error_result is self.expected_exception

    def on_error_callback(self, ex):
        self.on_error_result = ex


class WhenACircuitBreakerIsOnTheThresholdOfBreaking:
    def given_the_function_has_failed_twice(self):
        self.expected_exception = ValueError()
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)

    def when_the_call_fails_again(self):
        self.exception = contexts.catch(self.function_to_break)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.expected_exception

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self):
        raise self.expected_exception


class WhenCircuitIsBroken:
    def given_the_function_has_failed_three_times(self):
        self.patch = mock.patch('time.perf_counter', return_value=0)
        self.mock = self.patch.start()
        self.x = 0
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)
        self.x = 0

    def when_i_call_the_circuit_breaker_function(self):
        self.mock.return_value = 0.5
        self.exception = contexts.catch(self.function_to_break)

    def it_should_throw_CircuitBrokenError(self):
        assert isinstance(self.exception, CircuitBrokenError)

    def it_should_say_how_long_it_will_take_to_close_the_circuit(self):
        assert self.exception.time_remaining == 0.5

    def it_should_not_call_the_function(self):
        assert self.x == 0

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self):
        self.x += 1
        raise ValueError


# 'leaky bucket' functionality
class WhenTheCircuitBreakerWasAboutToTripAndWeWaitForTheTimeout:
    def given_the_circuit_was_about_to_be_broken(self):
        self.patch = mock.patch('time.perf_counter', return_value=0)
        self.mock = self.patch.start()
        contexts.catch(self.function_to_break)
        self.mock.return_value = 0.5
        contexts.catch(self.function_to_break)
        self.mock.return_value = 1.1

    def when_we_run_the_function_again(self):
        self.exception1 = contexts.catch(self.function_to_break)
        self.exception2 = contexts.catch(self.function_to_break)
        self.exception3 = contexts.catch(self.function_to_break)

    def it_should_have_decremented_the_failure_count(self):
        assert isinstance(self.exception1, ValueError)
        assert isinstance(self.exception2, ValueError)
        assert isinstance(self.exception3, CircuitBrokenError)

    def cleanup_the_mock(self):
        self.patch.stop()

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self):
        raise ValueError


class WhenTheCircuitIsHalfBrokenAndTheFunctionSucceeds:
    def given_the_circuit_was_broken_in_the_past(self):
        self.x = 0
        self.expected_return_value = "some thing that was returned"
        self.patch = mock.patch('time.perf_counter', return_value=0)
        self.mock = self.patch.start()
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)

    def when_we_wait_for_the_timeout_and_retry(self):
        self.mock.return_value = 1.1
        self.result = self.function_to_break()

    def it_should_call_the_function(self):
        assert self.x == 4

    def it_should_forward_the_return_value(self):
        assert self.result == self.expected_return_value

    def cleanup_the_mock(self):
        self.patch.stop()

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self):
        self.x += 1
        if self.x < 3:
            raise ValueError
        return self.expected_return_value


class WhenTheCircuitIsHalfBrokenAndTheFunctionFails:
    def given_the_circuit_was_broken_in_the_past(self):
        self.x = 0
        self.expected_exception = ValueError()
        self.patch = mock.patch('time.perf_counter', return_value=0)
        self.mock = self.patch.start()
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)

    def when_we_wait_for_the_timeout_and_retry(self):
        self.mock.return_value = 1.1
        self.exception = contexts.catch(self.function_to_break)

    def it_should_call_the_function(self):
        assert self.x == 4

    def it_should_bubble_out_the_exception(self):
        assert self.exception is self.expected_exception

    def cleanup_the_mock(self):
        self.patch.stop()

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self):
        self.x += 1
        raise self.expected_exception


class WhenRetryingAfterTheFunctionFailedInTheHalfBrokenState:
    def given_the_circuit_was_half_broken_and_the_function_failed_again(self):
        self.x = 0
        self.patch = mock.patch('time.perf_counter', return_value=0)
        self.mock = self.patch.start()
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)
        self.mock.return_value = 1.1
        contexts.catch(self.function_to_break)

    def when_we_wait_for_the_timeout_and_retry(self):
        self.exception = contexts.catch(self.function_to_break)

    def it_should_not_call_the_function(self):
        assert self.x == 4

    def it_should_throw_CircuitBrokenError(self):
        assert isinstance(self.exception, CircuitBrokenError)

    def cleanup_the_mock(self):
        self.patch.stop()

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self):
        self.x += 1
        raise ValueError
