"""
reactionmenu • discord pagination
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A library to create a discord.py 2.0+ paginator. Supports pagination with buttons, reactions, and category selection using selects.

:copyright: (c) 2021-present Defxult#8269
:license: MIT

"""

from .buttons import ReactionButton, ViewButton
from .core import ReactionMenu
from .views_menu import ViewMenu, ViewSelect
from .abc import Page


def version_info() -> str:
    """Shows the current version of the library

    >>> print(reactionmenu.version_info())
    """
    from typing import Final, Literal

    version = (3, 1, 0)
    release_level: Literal['alpha', 'beta', 'rc', 'final'] = 'rc'
        
    BASE: Final[str] = '.'.join([str(n) for n in version])

    if release_level == 'final':
        return BASE
    else:
        # try and get the last commit hash for a more precise version, if it fails, just use the basic version
        try:
            import subprocess
            p = subprocess.Popen(['git', 'ls-remote', __source__, 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, _ = p.communicate()
            short_hash = out.decode('utf-8')[:7]
            p.kill()
            return BASE + f"{release_level}+{short_hash}"
        except Exception:
            print('reactionmenu notification: An error occurred when attempting to get the last commit ID of the repo for a more precise version of the library. Returning base development version instead.')
            return BASE + release_level

__source__ = 'https://github.com/Defxult/reactionmenu'
__version__ = version_info()
__all__ = (
    'ReactionMenu',
    'ReactionButton',
    'ViewMenu',
    'ViewButton',
    'ViewSelect',
    'Page'
)
