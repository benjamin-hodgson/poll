`poll`
======
Utilities for polling, retrying, and exception handling.


Installation
------------

```bash
$ pip install poll
```


Example
-------

An function which retries a Web request until the resource exists:

```python
import poll
import requests

@poll(lambda response: response.status_code != 404)
def wait_until_exists(uri):
    return requests.get(uri)
```

