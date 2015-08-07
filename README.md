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

An function which retries a Web request until the resource exists:

```python
from poll import poll
import requests

@poll(lambda response: response.status_code != 404)
def wait_until_exists(uri):
    return requests.get(uri)
```

