`poll`
======

[![Build Status](https://travis-ci.org/benjamin-hodgson/poll.svg)](https://travis-ci.org/benjamin-hodgson/poll)
[![Documentation Status](https://readthedocs.org/projects/poll/badge/?version=v0.1)](https://readthedocs.org/projects/poll/?badge=v0.1)

Utilities for polling, retrying, and exception handling, inspired by [Polly](https://github.com/michael-wolfenden/Polly).


Installation
------------

```bash
$ pip install poll
```


Example
-------

A function which retries a Web request every second until the resource exists, up to a maximum of 15 seconds:

```python
from poll import poll
import requests

@poll(lambda response: response.status_code != 404, timeout=15, interval=1)
def wait_until_exists(uri):
    return requests.get(uri)
```

