from poll import retry, retry_
from contexts import catch


class WhenRetryingAFunctionWhichWorksFirstTime:
    def given_a_call_counter(self):
        self.x = 0
        self.expected_args = (1, 2, 3)
        self.expected_kwargs = {"foo": "bar"}

    def when_i_execute_the_retryable_function(self):
        self.result = self.function_to_retry(*self.expected_args, **self.expected_kwargs)

    def it_should_call_it_once(self):
        assert self.x == 1

    def it_should_forward_the_arguments(self):
        assert self.args == self.expected_args

    def it_should_forward_the_keyword_arguments(self):
        assert self.kwargs == self.expected_kwargs

    def it_should_return_the_final_answer(self):
        assert self.result is self.x

    @retry(Exception, times=3, interval=0.001)
    def function_to_retry(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.x += 1
        return self.x


class WhenRetryingAFunctionWhichThrowsAnException:
    def given_a_call_counter(self):
        self.x = 0
        self.expected_args = (1, 2, 3)
        self.expected_kwargs = {"foo": "bar"}
        self.args = []
        self.kwargs = []

    def when_i_execute_the_retryable_function(self):
        self.result = self.function_to_retry(*self.expected_args, **self.expected_kwargs)

    def it_should_keep_trying_until_the_exception_goes_away(self):
        assert self.x == 3

    def it_should_forward_the_arguments_every_time(self):
        assert all(a == self.expected_args for a in self.args)

    def it_should_forward_the_keyword_arguments_every_time(self):
        assert all(k == self.expected_kwargs for k in self.kwargs)

    def it_should_return_the_final_answer(self):
        assert self.result is self.x

    @retry(ValueError, times=3, interval=0.001)
    def function_to_retry(self, *args, **kwargs):
        self.args.append(args)
        self.kwargs.append(kwargs)
        self.x += 1
        if self.x != 3:
            raise ValueError
        return self.x


class WhenRetryingAFunctionWhichThrowsAnExceptionTooManyTimes:
    def given_an_error_to_throw(self):
        self.x = 0
        self.expected_exception = ValueError()

    def when_i_execute_the_retryable_function(self):
        self.exception = catch(self.function_to_retry)

    def it_should_keep_trying_until_the_number_of_retries_is_exceeded(self):
        assert self.x == 3

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.expected_exception

    @retry(ValueError, times=3, interval=0.001)
    def function_to_retry(self):
        self.x += 1
        raise self.expected_exception


class WhenRetryingAFunctionWhichThrowsAnExceptionWeWereNotExpecting:
    def given_an_error_to_throw(self):
        self.x = 0
        self.expected_exception = TypeError()

    def when_i_execute_the_retryable_function(self):
        self.exception = catch(self.function_to_retry)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.expected_exception

    def it_should_only_try_once(self):
        assert self.x == 1

    @retry(ValueError, times=3, interval=0.001)
    def function_to_retry(self, *args, **kwargs):
        self.x += 1
        raise self.expected_exception


class WhenRetryingAFunctionAndListeningForMultipleErrors:
    def given_a_call_counter(self):
        self.x = 0
        self.expected_args = (1, 2, 3)
        self.expected_kwargs = {"foo": "bar"}
        self.args = []
        self.kwargs = []

    def when_i_execute_the_retryable_function(self):
        self.result = self.function_to_retry(*self.expected_args, **self.expected_kwargs)

    def it_should_keep_trying_until_the_exception_goes_away(self):
        assert self.x == 3

    def it_should_forward_the_arguments_every_time(self):
        assert all(a == self.expected_args for a in self.args)

    def it_should_forward_the_keyword_arguments_every_time(self):
        assert all(k == self.expected_kwargs for k in self.kwargs)

    def it_should_return_the_final_answer(self):
        assert self.result is self.x

    @retry([ValueError, IndexError], times=3, interval=0.001)
    def function_to_retry(self, *args, **kwargs):
        self.args.append(args)
        self.kwargs.append(kwargs)
        self.x += 1
        if self.x == 1:
            raise ValueError
        if self.x == 2:
            raise IndexError
        return self.x


class WhenRetryingAFunctionAndListeningForMultipleErrorsButItThrowsAnExceptionWeWereNotExpecting:
    def given_an_error_to_throw(self):
        self.x = 0
        self.expected_exception = TypeError()

    def when_i_execute_the_retryable_function(self):
        self.exception = catch(self.function_to_retry)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.expected_exception

    def it_should_only_try_once(self):
        assert self.x == 1

    @retry([ValueError, IndexError], times=3, interval=0.001)
    def function_to_retry(self, *args, **kwargs):
        self.x += 1
        raise self.expected_exception


class WhenRetryingAFunctionAtTheUseSiteAndItWorksFirstTime:
    def given_a_call_counter(self):
        self.x = 0
        self.expected_args = (1, 2, 3)
        self.expected_kwargs = {"foo": "bar"}

    def when_i_retry_the_function(self):
        self.result = retry_(self.function_to_retry, Exception, 3, 0.001, *self.expected_args, **self.expected_kwargs)

    def it_should_call_it_once(self):
        assert self.x == 1

    def it_should_forward_the_arguments(self):
        assert self.args == self.expected_args

    def it_should_forward_the_keyword_arguments(self):
        assert self.kwargs == self.expected_kwargs

    def it_should_return_the_final_answer(self):
        assert self.result is self.x

    def function_to_retry(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.x += 1
        return self.x


class WhenRetryingAFunctionAtTheUseSiteAndItThrowsAnException:
    def given_a_call_counter(self):
        self.x = 0
        self.expected_args = (1, 2, 3)
        self.expected_kwargs = {"foo": "bar"}
        self.args = []
        self.kwargs = []

    def when_i_retry_the_function(self):
        self.result = retry_(self.function_to_retry, ValueError, 3, 0.001, *self.expected_args, **self.expected_kwargs)

    def it_should_keep_trying_until_the_exception_goes_away(self):
        assert self.x == 3

    def it_should_forward_the_arguments_every_time(self):
        assert all(a == self.expected_args for a in self.args)

    def it_should_forward_the_keyword_arguments_every_time(self):
        assert all(k == self.expected_kwargs for k in self.kwargs)

    def it_should_return_the_final_answer(self):
        assert self.result is self.x

    def function_to_retry(self, *args, **kwargs):
        self.args.append(args)
        self.kwargs.append(kwargs)
        self.x += 1
        if self.x != 3:
            raise ValueError
        return self.x


class WhenRetryingAFunctionAtTheUseSiteAndItThrowsAnExceptionTooManyTimes:
    def given_an_error_to_throw(self):
        self.x = 0
        self.expected_exception = ValueError()

    def when_i_retry_the_function(self):
        self.exception = catch(retry_, self.function_to_retry, ValueError, times=3, interval=0.001)

    def it_should_keep_trying_until_the_number_of_retries_is_exceeded(self):
        assert self.x == 3

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.expected_exception

    def function_to_retry(self):
        self.x += 1
        raise self.expected_exception


class WhenRetryingAFunctionAtTheUseSiteAndItThrowsAnExceptionWeWereNotExpecting:
    def given_an_error_to_throw(self):
        self.x = 0
        self.expected_exception = TypeError()

    def when_i_retry_the_function(self):
        self.exception = catch(retry_, self.function_to_retry, ValueError, times=3, interval=0.001)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.expected_exception

    def it_should_only_try_once(self):
        assert self.x == 1

    def function_to_retry(self, *args, **kwargs):
        self.x += 1
        raise self.expected_exception


class WhenRetryingAFunctionAtTheUseSiteAndListeningForMultipleErrors:
    def given_a_call_counter(self):
        self.x = 0
        self.expected_args = (1, 2, 3)
        self.expected_kwargs = {"foo": "bar"}
        self.args = []
        self.kwargs = []

    def when_i_retry_the_function(self):
        self.result = retry_(self.function_to_retry, [ValueError, IndexError], 3, 0.001, *self.expected_args, **self.expected_kwargs)

    def it_should_keep_trying_until_the_exception_goes_away(self):
        assert self.x == 3

    def it_should_forward_the_arguments_every_time(self):
        assert all(a == self.expected_args for a in self.args)

    def it_should_forward_the_keyword_arguments_every_time(self):
        assert all(k == self.expected_kwargs for k in self.kwargs)

    def it_should_return_the_final_answer(self):
        assert self.result is self.x

    def function_to_retry(self, *args, **kwargs):
        self.args.append(args)
        self.kwargs.append(kwargs)
        self.x += 1
        if self.x == 1:
            raise ValueError
        if self.x == 2:
            raise IndexError
        return self.x


class WhenRetryingAFunctionAtTheUseSiteAndListeningForMultipleErrorsButItThrowsAnExceptionWeWereNotExpecting:
    def given_an_error_to_throw(self):
        self.x = 0
        self.expected_exception = TypeError()

    def when_i_retry_the_function(self):
        self.exception = catch(retry_, self.function_to_retry, [ValueError, IndexError], times=3, interval=0.001)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.expected_exception

    def it_should_only_try_once(self):
        assert self.x == 1

    def function_to_retry(self, *args, **kwargs):
        self.x += 1
        raise self.expected_exception
