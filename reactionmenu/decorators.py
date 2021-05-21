"""
MIT License

Copyright (c) 2021 Defxult#8269

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

import asyncio
from functools import wraps

from . import core
from .errors import MenuSettingsMismatch, MenuAlreadyRunning, ReactionMenuException, NoButtons

__all__ = ('menu_verification', 'dynamic_only', 'static_only', 'ensure_not_primed')


def menu_verification(func):
    """Checks if the basic settings of :class:`ReactionMenu` and :class:`TextMenu` are in compliance with how the menu functions.
    Specifics to each menu are not done here. Those are done in their own classes
    
        .. added:: v1.0.9
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        inst = args[0]

        if isinstance(inst, core.ReactionMenu):
            if inst._config not in (core.ReactionMenu.STATIC, core.ReactionMenu.DYNAMIC):
                raise MenuSettingsMismatch("The menu's setting for dynamic or static was not recognized")

        if inst._all_buttons_removed:
            raise NoButtons

        # first, check if the user is requesting a DM session. this needs to be done first because if it is a DM session,
        # there are a lot of attr values that will be overridden
        is_using_send_to = True if kwargs else False
        inst._verify_dm_usage(is_using_send_to)

        # theres no need to do button duplicate checks for an auto-pagination menu because no buttons will be used
        if not inst._auto_paginator:
            inst._duplicate_emoji_check()
            inst._duplicate_name_check()

        return await func(*args, **kwargs)
    return wrapper

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
    if asyncio.iscoroutinefunction(func):
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
