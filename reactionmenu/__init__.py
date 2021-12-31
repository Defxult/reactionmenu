"""
reactionmenu • discord pagination
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A library to create a discord paginator. Supports pagination with Discords Buttons feature and reactions.

:copyright: (c) 2021-present Defxult#8269
:license: MIT

"""

from .buttons import ReactionButton, ViewButton
from .core import ReactionMenu
from .views_menu import ViewMenu


def version_info():
    """Shows the current version, release type, and patch of the library

    - `version` Current version of the library
    - `releasetype` Either "final" (the PyPI version) or "pre-release" (the GitHub version)
    - `patch` The last significant bug fix
    
    >>> print(reactionmenu.version_info())
    """
    from collections import namedtuple
    VersionInfo = namedtuple('VersionInfo', ['version', 'releasetype', 'patch'])
    return VersionInfo(version='3.0.0b5', releasetype='pre-release', patch=None)

__source__ = 'https://github.com/Defxult/reactionmenu'
__all__ = (
    'ReactionMenu',
    'ReactionButton',
    'ViewMenu',
    'ViewButton'
)
