from poll import poll, poll_
from contexts import catch


class WhenConditionIsTrueFirstTime:
    def given_a_call_counter(self):
        self.x = 0
        self.expected_args = (1, 2, 3)
        self.expected_kwargs = {"foo": "bar"}

    def when_i_execute_the_function_to_poll(self):
        self.result = self.function_to_poll(*self.expected_args, **self.expected_kwargs)

    def it_should_run_it_once(self):
        assert self.x == 1

    def it_should_forward_the_arguments(self):
        assert self.args == self.expected_args

    def it_should_forward_the_keyword_arguments(self):
        assert self.kwargs == self.expected_kwargs

    def it_should_return_the_final_answer(self):
        assert self.result is self.x

    @poll(lambda x: x == 1, interval=0.001)
    def function_to_poll(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs
        self.x += 1
        return self.x


class WhenConditionIsTrueAfterAFewTries:
    def given_a_call_counter(self):
        self.x = 0
        self.expected_args = (1, 2, 3)
        self.expected_kwargs = {"foo": "bar"}
        self.args = []
        self.kwargs = []

    def when_i_execute_the_function_to_poll(self):
        self.result = self.function_to_poll(*self.expected_args, **self.expected_kwargs)

    def it_should_keep_trying(self):
        assert self.x == 3

    def it_should_forward_the_arguments_every_time(self):
        assert all(a == self.expected_args for a in self.args)

    def it_should_forward_the_keyword_arguments_every_time(self):
        assert all(k == self.expected_kwargs for k in self.kwargs)

    def it_should_return_the_final_answer(self):
        assert self.result is self.x

    @poll(lambda x: x == 3, interval=0.001)
    def function_to_poll(self, *args, **kwargs):
        self.args.append(args)
        self.kwargs.append(kwargs)
        self.x += 1
        return self.x


class WhenConditionIsNotTrueInTime:
    def given_a_call_counter(self):
        self.x = 0

    def when_i_execute_the_function_to_poll(self):
        self.exception = catch(self.function_to_poll)

    def it_should_keep_trying(self):
        assert self.x == 2

    def it_should_throw(self):
        assert isinstance(self.exception, TimeoutError)

    @poll(lambda x: x == 3, timeout=0.005, interval=0.003)
    def function_to_poll(self):
        self.x += 1
        return self.x


class WhenFunctionThrowsAnError:
    def given_an_exception(self):
        self.to_throw = Exception()

    def when_i_execute_the_function_to_poll(self):
        self.exception = catch(self.function_to_poll)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.to_throw

    @poll(lambda x: x == 1, interval=0.001)
    def function_to_poll(self):
        raise self.to_throw


class WhenConditionThrowsAnError:
    def given_an_exception(self):
        self.to_throw = Exception()

    def when_i_execute_the_function_to_poll(self):
        self.exception = catch(self.function_to_poll)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.to_throw

    @poll(lambda self: self.throw(), interval=0.001)
    def function_to_poll(self):
        return self

    def throw(self):
        raise self.to_throw


class WhenPollingAtUseSiteAndConditionIsTrueFirstTime:
    def given_a_call_counter(self):
        self.x = 0
        self.expected_args = (1, 2, 3)
        self.expected_kwargs = {"foo": "bar"}

    def when_i_poll_the_function(self):
        self.result = poll_(self.function_to_poll, lambda x: x == 1, 1, 0.001, *self.expected_args, **self.expected_kwargs)

    def it_should_run_it_once(self):
        assert self.x == 1

    def it_should_forward_the_arguments(self):
        assert self.args == self.expected_args

    def it_should_forward_the_keyword_arguments(self):
        assert self.kwargs == self.expected_kwargs

    def it_should_return_the_final_answer(self):
        assert self.result is self.x

    def function_to_poll(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs
        self.x += 1
        return self.x


class WhenPollingAtUseSiteAndConditionIsTrueAfterAFewTries:
    def given_a_call_counter(self):
        self.x = 0
        self.expected_args = (1, 2, 3)
        self.expected_kwargs = {"foo": "bar"}
        self.args = []
        self.kwargs = []

    def when_i_poll_the_function(self):
        self.result = poll_(self.function_to_poll, lambda x: x == 3, 1, 0.001, *self.expected_args, **self.expected_kwargs)

    def it_should_keep_trying(self):
        assert self.x == 3

    def it_should_forward_the_arguments_every_time(self):
        assert all(a == self.expected_args for a in self.args)

    def it_should_forward_the_keyword_arguments_every_time(self):
        assert all(k == self.expected_kwargs for k in self.kwargs)

    def it_should_return_the_final_answer(self):
        assert self.result is self.x

    def function_to_poll(self, *args, **kwargs):
        self.args.append(args)
        self.kwargs.append(kwargs)
        self.x += 1
        return self.x


class WhenPollingAtUseSiteAndConditionIsNotTrueInTime:
    def given_a_call_counter(self):
        self.x = 0

    def when_i_poll_the_function(self):
        self.exception = catch(poll_, self.function_to_poll, lambda x: x == 3, timeout=0.005, interval=0.003)

    def it_should_keep_trying(self):
        assert self.x == 2

    def it_should_throw(self):
        assert isinstance(self.exception, TimeoutError)

    def function_to_poll(self):
        self.x += 1
        return self.x


class WhenPollingAtUseSiteAndFunctionThrowsAnError:
    def given_an_exception(self):
        self.to_throw = Exception()

    def when_i_poll_the_function(self):
        self.exception = catch(poll_, self.function_to_poll, lambda x: x == 1, interval=0.001)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.to_throw

    def function_to_poll(self):
        raise self.to_throw


class WhenPollingAtUseSiteAndConditionThrowsAnError:
    def given_an_exception(self):
        self.to_throw = Exception()

    def when_i_poll_the_function(self):
        self.exception = catch(poll_, self.function_to_poll, lambda self: self.throw(), interval=0.001)

    def it_should_bubble_the_exception_out(self):
        assert self.exception is self.to_throw

    def function_to_poll(self):
        return self

    def throw(self):
        raise self.to_throw
