`poll`
======

[![Build Status](https://travis-ci.org/benjamin-hodgson/poll.svg)](https://travis-ci.org/benjamin-hodgson/poll)
[![Documentation Status](https://readthedocs.org/projects/poll/badge/?version=v1.0)](https://readthedocs.org/projects/poll/?badge=v0.1)

Utilities for polling, retrying, and exception handling,
inspired by [Polly](https://github.com/michael-wolfenden/Polly).


Installation
------------

```bash
$ pip install poll
```


Polling
-------

When you're waiting for a long-running process to become complete,
it's often necessary to _poll_ an external system to determine whether
the operation is complete.

Here is a function which retries a Web request (using the `requests` library)
every second until the resource exists, up to a maximum of 15 seconds:

```python
from poll import poll
import requests

@poll(lambda response: response.status_code != 404, timeout=15, interval=1)
def wait_until_exists(uri):
    return requests.get(uri)
```

There's also a non-decorator form available, for when you want
the _user_ of a function to decide whether to poll the operation.
The following code is equivalent to the function above:

```python
from poll import poll_
import requests

def wait_until_exists(uri):
    poll_(
        lambda: requests.get(uri),
        lambda response: response.status_code != 404,
        timeout=15,
        interval=1
    )
```


Retrying
--------

When an operation may occasionally fail,
it's often useful to _retry_ the operation in the hope
that it will succeed the next time.

Here's an approximately equivalent function to the above example,
which catches the exception thrown by `raise_for_status`
and retries until the response has a 2xx status code.

```python
from poll import retry
import requests

@retry(requests.HTTPError, times=15, interval=1)
def wait_until_succeeds(uri):
    response = requests.get(uri)
    response.raise_for_status()
    return response
```

As with polling, you can use the 'underscored' version
of `retry` to add retry logic to a function which doesn't already have it.

```python
from poll import retry_
import requests

def get_or_raise(uri):
    response = requests.get(uri)
    response.raise_for_status()
    return response

def wait_until_succeeds(uri):
    retry_(
        lambda: get_or_raise(uri),
        requests.HTTPError,
        times=15,
        interval=1
    )
```


Circuit Breaker
---------------

Simple retry logic often gets the job done, but it can cause problems.
If your calls to an external service are failing because the external
service is struggling under load, you don't want to exacerbate
the problem by hammering it with retry attempts.

The _circuit breaker_ pattern is a strategy for backing off, to avoid
causing harm to external systems by retrying. If a call fails a
certain number of times, the circuit breaker 'trips' and blocks any
future calls.

After a time, the circuit enters the 'half-broken' state where it
is ready to make one real call to test if the external service is
functioning again. If this one real call fails, the circuit is broken
again; otherwise, normal service is resumed.

Here's another version of our example, which blocks future attempts
for sixty seconds after three calls to `attempt` fail.

```python
from poll import circuitbreaker
import requests

@circuitbreaker(requests.HTTPError, threshold=3, reset_timeout=60)
def attempt(uri):
    response = requests.get(uri)
    response.raise_for_status()
    return response
```

For a more detailed explanation of Circuit Breaker, see Martin
Fowler's article: http://martinfowler.com/bliki/CircuitBreaker.html
