"""
reactionmenu • discord pagination
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A library to create a discord paginator. Supports pagination with Discords Buttons feature and reactions.

:copyright: (c) 2021-present Defxult#8269
:license: MIT

"""

from .buttons import ReactionButton, ViewButton
from .core import ReactionMenu
from .views_menu import ViewMenu, ViewSelect
from .abc import Page


def version_info():
    """Shows the current version of the library

    >>> print(reactionmenu.version_info())
    """
    from typing import NamedTuple, Literal
    class VersionInfo(NamedTuple):
        major: int
        minor: int
        patch: int
        releaseLevel: Literal['alpha', 'beta', 'candidate', 'final']
        
        def __str__(self) -> str:
            return f'{self.major}.{self.minor}.{self.patch}' + 'b5'

    return VersionInfo(major=3, minor=1, patch=0, releaseLevel='beta')

__source__ = 'https://github.com/Defxult/reactionmenu'
__all__ = (
    'ReactionMenu',
    'ReactionButton',
    'ViewMenu',
    'ViewButton',
    'ViewSelect',
    'Page'
)
