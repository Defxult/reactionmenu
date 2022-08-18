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
        releaseLevel: Literal['alpha', 'beta', 'rc', 'final']
        serial: int
        
        @property
        def _version(self) -> str:
            base = f'{self.major}.{self.minor}.{self.patch}'
            return base if self.releaseLevel == 'final' else base + f'{self.releaseLevel}-{self.serial}'

    return VersionInfo(major=3, minor=1, patch=0, releaseLevel='rc', serial=1)

__source__ = 'https://github.com/Defxult/reactionmenu'
__all__ = (
    'ReactionMenu',
    'ReactionButton',
    'ViewMenu',
    'ViewButton',
    'ViewSelect',
    'Page'
)
