"""
MIT License

Copyright (c) 2021-present @defxult

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
DEALINGS IN THE SOFTWARE.
"""

from asyncio import iscoroutinefunction
from functools import wraps

from .errors import MenuAlreadyRunning


def ensure_not_primed(func):
    """Check to make sure certain methods cannot be ran once the menu has been fully started"""
    if iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs): # type: ignore
            inst = args[0]
            if not inst._is_running or inst._bypass_primed:
                if inst._bypass_primed:
                    inst._bypass_primed = False
                return await func(*args, **kwargs)
            else:
                raise MenuAlreadyRunning(f'You cannot use method "{func.__name__}" after the menu has started. Menu name: {inst.name!r}')
        return wrapper
    else:
        @wraps(func)
        def wrapper(*args, **kwargs):
            inst = args[0]
            if not inst._is_running or inst._bypass_primed:
                if inst._bypass_primed:
                    inst._bypass_primed = False
                return func(*args, **kwargs)
            else:
                raise MenuAlreadyRunning(f'You cannot use method "{func.__name__}" after the menu has started. Menu name: {inst.name!r}')
        return wrapper
