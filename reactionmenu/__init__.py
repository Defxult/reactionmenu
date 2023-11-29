"""
reactionmenu • discord pagination
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A library to create a discord.py 2.0+ paginator. Supports pagination with buttons, reactions, and category selection using selects.

:copyright: (c) 2021-present @defxult
:license: MIT

"""

from .buttons import ReactionButton, ViewButton
from .core import ReactionMenu
from .views_menu import ViewMenu, ViewSelect
from .abc import Page


__source__ = 'https://github.com/Defxult/reactionmenu'
__all__ = (
    'ReactionMenu',
    'ReactionButton',
    'ViewMenu',
    'ViewButton',
    'ViewSelect',
    'Page'
)
