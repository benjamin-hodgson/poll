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

    def it_should_not_increment_the_failure_count(self):
        assert self.function_to_break.failure_count() == 0

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self, *args, **kwargs):
        self.x += 1
        self.args = args
        self.kwargs = kwargs
        return self.expected_return_value


class WhenAFunctionWithCircuitBreakerThrowsOnce:
    def given_an_exception_to_throw(self):
        self.x = 0
        self.expected_exception = ValueError()

    def when_i_call_the_circuit_breaker_function(self):
        self.exception = contexts.catch(self.function_to_break)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.expected_exception

    def it_should_call_it_once(self):
        assert self.x == 1

    def it_should_increment_the_failure_count(self):
        assert self.function_to_break.failure_count() == 1

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self):
        self.x += 1
        raise self.expected_exception


class WhenACircuitBreakerIsOnTheThresholdOfBreaking:
    def given_the_function_has_failed_three_times(self):
        self.expected_exception = ValueError()
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)

    def when_i_call_the_circuit_breaker_function(self):
        self.exception = contexts.catch(self.function_to_break)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.expected_exception

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self):
        raise self.expected_exception


class WhenCircuitIsBroken:
    def given_the_function_has_failed_four_times(self):
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)
        contexts.catch(self.function_to_break)
        self.x = 0

    def when_i_call_the_circuit_breaker_function(self):
        self.exception = contexts.catch(self.function_to_break)

    def it_should_throw_CircuitBrokenError(self):
        assert isinstance(self.exception, CircuitBrokenError)

    def it_should_not_call_the_function(self):
        assert self.x == 0

    def it_should_not_increment_the_failure_count(self):
        assert self.function_to_break.failure_count() == 4

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self):
        self.x += 1
        raise ValueError


class WhenTheFunctionFailsOnceAndWeWaitForTheTimeout:
    def given_the_function_has_failed_once(self):
        self.patch = mock.patch('time.perf_counter', return_value=0)
        self.mock = self.patch.start()
        contexts.catch(self.function_to_break)

    def when_we_wait_for_the_timeout(self):
        self.mock.return_value = 1.1

    def it_should_reset_the_failure_count(self):
        assert self.function_to_break.failure_count() == 0

    def cleanup_the_mock(self):
        self.patch.stop()

    @circuitbreaker(ValueError, threshold=3, reset_timeout=1)
    def function_to_break(self):
        raise ValueError
