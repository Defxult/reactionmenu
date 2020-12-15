"""
MIT License

Copyright (c) 2020 Defxult#8269

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
import inspect
from functools import wraps
from .errors import *
from . import core


def dynamic_only(func):
    """Check to make sure the method ran matched the dynamic config of the menu"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        inst = args[0]
        if inst._config == core.ReactionMenu.DYNAMIC:
            func(*args, **kwargs)
        else:
            raise MenuSettingsMismatch(f'Method "{func.__name__}" can only be used on a dynamic menu')
    return wrapper   

def static_only(func):
    """Check to make sure the method ran matched the static config of the menu"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        inst = args[0]
        if inst._config == core.ReactionMenu.STATIC:
            func(*args, **kwargs)
        else:
            raise MenuSettingsMismatch(f'Method "{func.__name__}" can only be used on a static menu')
    return wrapper

def ensure_not_primed(func):
    """Check to make sure certain methods cannot be ran once the menu has been fully started"""
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            inst = args[0]
            if not inst._is_running:
                return await func(*args, **kwargs)
            else:
                raise MenuAlreadyRunning(f'You cannot use method "{func.__name__}" after the menu has started. Menu name: {inst._name}')
        return wrapper
    else:
        @wraps(func)
        def wrapper(*args, **kwargs):
            inst = args[0]
            if not inst._is_running:
                func(*args, **kwargs)
            else:
                raise MenuAlreadyRunning(f'You cannot use method "{func.__name__}" after the menu has started. Menu name: {inst._name}')
        return wrapper