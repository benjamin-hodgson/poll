from poll import poll
from contexts import catch


class WhenConditionIsTrueFirstTime:
    def given_a_call_counter(self):
        self.x = 0

    def when_i_execute_the_function_to_poll(self):
        self.function_to_poll()

    def it_should_run_it_once(self):
        assert self.x == 1

    @poll(lambda x: x == 1, interval=0.001)
    def function_to_poll(self):
        self.x += 1
        return self.x


class WhenConditionIsTrueAfterAFewTries:
    def given_a_call_counter(self):
        self.x = 0

    def when_i_execute_the_function_to_poll(self):
        self.function_to_poll()

    def it_should_keep_trying(self):
        assert self.x == 3

    @poll(lambda x: x == 3, interval=0.001)
    def function_to_poll(self):
        self.x += 1
        return self.x


class WhenConditionIsNotTrueInTime:
    def given_a_call_counter(self):
        self.x = 0

    def when_i_execute_the_function_to_poll(self):
        self.exception = catch(self.function_to_poll)

    def it_should_keep_trying(self):
        assert self.x == 3

    def it_should_throw(self):
        assert isinstance(self.exception, TimeoutError)

    @poll(lambda x: x == 3, timeout=0.01, interval=0.0045)
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