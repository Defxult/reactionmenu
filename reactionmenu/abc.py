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

import abc
import asyncio
import collections
import itertools
import warnings
from datetime import datetime
from typing import List, Union

import discord

from .buttons import Button, ButtonType
from .decorators import ensure_not_primed
from .errors import *

class _PageController:
    """An helper class to control the pagination process
    
        .. added:: v2.0.0
    """

    __slots__ = ('pages', 'total_pages', 'index')

    def __init__(self, pages: List[Union[discord.Embed, str]]):
        self.pages = pages
        self.total_pages = len(pages) - 1
        self.index = 0

    @property
    def current_page(self) -> Union[discord.Embed, str]:
        """Return the current page in the pagination process"""
        return self.pages[self.index]
    
    def next(self) -> Union[discord.Embed, str]:
        """Go to the next page in the pagination process"""
        try:
            self.index += 1
            temp = self.pages[self.index]
        except IndexError:
            if self.index > self.total_pages:
                self.index = 0
            
            elif self.index < 0:
                self.index = self.total_pages
        finally:
            return self.pages[self.index]
    
    def prev(self) -> Union[discord.Embed, str]:
        """Go to the last page in the pagination process"""
        try:
            self.index -= 1
            temp = self.pages[self.index]
        except IndexError:
            if self.index > self.total_pages:
                self.index = 0
            
            elif self.index < 0:
                self.index = self.total_pages
        finally:
            return self.pages[self.index]

class Menu(metaclass=abc.ABCMeta):
    """Abstract base class for :class:`ReactionMenu` and :class:`TextMenu`
    
        .. added:: v1.0.9

        .. changes::
            v2.0.0
                Moved session limit class variables here (.core and .text use to have their own)
                Added :attr:`_sessions_limit_details` (used to be :attr:`_limit_message` and `_sessions_limit`)
                Replaced :meth:`_is_currently_limited` with :meth:`_handle_session_limits` to support different types of limits

        .. note::
            The class itself was created in v1.0.9, any other abc that is not labeled with a version was moved from :class:`ReactionMenu`. So their version
            varies from v1.0.0 - v1.0.8
    """
    NORMAL = 'NORMAL'
    FAST = 'FAST'

    EMOJI_BACK_BUTTON = '◀️'
    EMOJI_NEXT_BUTTON = '▶️'
    EMOJI_FIRST_PAGE =  '⏪'
    EMOJI_LAST_PAGE =   '⏩'
    EMOJI_GO_TO_PAGE =  '🔢'
    EMOJI_END_SESSION = '❌'

    _sessions_limited = False
    _sessions_limit_details = None 
    _task_sessions_pool: List[asyncio.Task] = []

    def __repr__(self):
        """
            .. added:: v1.0.9
        
            .. changes::
                v2.0.0
                    Added owner
        """
        class_name = self.__class__.__name__
        return f'<{class_name} name={self._name!r} owner={str(self._menu_owner)!r} is_running={self._is_running} run_time={self._run_time} timeout={self._timeout} auto_paginator={self._auto_paginator}>'

    @property
    def owner(self) -> Union[discord.Member, discord.User]:
        """
        Returns
        -------
        Union[:class:`discord.Member`, :class:`discord.User`]:
            The owner of the menu (the person that started the menu). If the menu was started in a DM, this will return `discord.User`
        
            .. added:: v2.0.0
        """
        return self._menu_owner
    
    @property
    @abc.abstractmethod
    def total_pages(self):
        raise NotImplementedError
    
    @property
    def message(self) -> discord.Message:
        """
        Returns
        -------
        :class:`discord.Message`:
            The menu's message object. Can be :class:`None` if the menu has not been started
        
            .. added:: v1.0.9
        """
        return self._msg
    
    @property
    def auto_paginator(self) -> bool:
        """
        Returns
        -------
        :class:`bool`:
            `True` if the menu has been set as an auto-pagination menu, `False` otherwise

            .. added:: v1.0.9
        """
        return self._auto_paginator
    
    @property
    def auto_turn_every(self) -> int:
        """
        Returns
        -------
        :class:`int`:   
            The amount of time in seconds for how frequently an auto-pagination menu should turn each page. Can be :class:`None` if the menu
            has not been set as an auto-pagination menu
        
            .. added:: v1.0.9
        """
        return self._auto_turn_every
    
    @property
    def run_time(self) -> int:
        """
        Returns
        -------
        :class:`int`:
            The amount of time in seconds for how long the menu has been running

            .. added:: v1.0.9
        """
        return self._run_time

    @property
    def is_running(self) -> bool:
        """
        Returns
        -------
        :class:`bool`:
            `True` if the menu is currently running, `False` otherwise
        """
        return self._is_running

    @property
    def default_next_button(self) -> Button:
        """
        Returns
        -------
        :class:`Button`:
            The default next button of the menu. This is the next button you set in the constructor
        
            .. changes::
                v1.0.9
                    Replaced indexing of :attr:`_all_buttons` with attr of :attr:`_default_next_button`
        """
        return self._default_next_button
        
    @property
    def default_back_button(self) -> Button:
        """
        Returns
        -------
        :class:`Button`:
            The default back button of the menu. This is the back button you set in the constructor

            .. changes::
                v1.0.9
                    Replaced indexing of :attr:`_all_buttons` with attr of :attr:`_default_back_button`
        """
        return self._default_back_button

    @property
    def all_buttons(self) -> List[Button]:
        """
        Returns
        -------
        List[:class:`Button`]:
            All the buttons that have been added to the menu. Can be :class:`None` if all buttons were removed

            .. changes::
                v1.0.9
                    Now returns :class:`None` instead of an empty list 
        """
        return self._all_buttons if self._all_buttons else None

    @property
    def next_buttons(self) -> List[Button]:
        """
        Returns
        -------
        List[:class:`Button`]:
            All the buttons with a `linked_to` of `ButtonType.NEXT_PAGE` that have been added to the menu. Can be :class:`None` if there are no next page buttons

            .. changes::
                v1.0.9
                    Now returns :class:`None` instead of an empty list
        """
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.NEXT_PAGE]
        return temp if temp else None

    @property
    def back_buttons(self) -> List[Button]:
        """
        Returns
        -------
        List[:class:`Button`]:
            All the buttons with a `linked_to` of `ButtonType.PREVIOUS_PAGE` that have been added to the menu. Can be :class:`None` if there are no previous page buttons

            .. changes::
                v1.0.9
                    Now returns :class:`None` instead of an empty list
        """
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.PREVIOUS_PAGE]
        return temp if temp else None

    @property
    def first_page_buttons(self) -> List[Button]:
        """
        Returns
        -------
        List[:class:`Button`]:
            All the buttons with a `linked_to` of `ButtonType.GO_TO_FIRST_PAGE` that have been added to the menu. Can be :class:`None` if there are no first page buttons
        """
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.GO_TO_FIRST_PAGE]
        return temp if temp else None

    @property
    def last_page_buttons(self) -> List[Button]:
        """
        Returns
        -------
        List[:class:`Button`]:
            All the buttons with a `linked_to` of `ButtonType.GO_TO_LAST_PAGE` that have been added to the menu. Can be :class:`None` if there are no last page buttons
        """
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.GO_TO_LAST_PAGE]
        return temp if temp else None

    @property
    def caller_buttons(self) -> List[Button]:
        """
        Returns
        ------- 
        List[:class:`Button`]:
            All the buttons with a `linked_to` of `ButtonType.CALLER` that have been added to the menu. Can be :class:`None` if there are no caller buttons
            
            .. added:: v1.0.3
        """
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.CALLER]
        return temp if temp else None

    @property
    def end_session_buttons(self) -> List[Button]:
        """
        Returns
        ------- 
        List[:class:`Button`]:
            All the buttons with a `linked_to` of `ButtonType.END_SESSION` that have been added to the menu. Can be :class:`None` if there are no end session buttons
        """
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.END_SESSION]
        return temp if temp else None

    @property
    def go_to_page_buttons(self) -> List[Button]:
        """
        Returns
        ------- 
        List[:class:`Button`]:
            All the buttons with a `linked_to` of `ButtonType.GO_TO_PAGE` that have been added to the menu. Can be :class:`None` if there are no go-to-page buttons
            
            .. added:: v1.0.1
        """
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.GO_TO_PAGE]
        return temp if temp else None
    
    @property
    def navigation_speed(self) -> str:
        return self._navigation_speed
    
    @navigation_speed.setter
    def navigation_speed(self, value):
        """A property getter/setter for kwarg "navigation_speed"
        
        Example
        -------
        ```
        menu = Menu(ctx, ...)
        menu.navigation_speed = Menu.NORMAL
        >>> print(menu.navigation_speed)
        NORMAL
        ```
        Returns
        -------
        :class:`str`:
            If not set, defaults to `Menu.NORMAL`

            .. added:: v1.0.5

            .. changes::
                v1.0.9
                    Moved to ABC
                    Replaced now removed class :meth:`ReactionMenu.cancel_all_sessions()` with class :meth:`Menu._force_stop`
        """
        cls = self.__class__
        if not self._is_running:
            if value in (cls.NORMAL, cls.FAST):
                self._navigation_speed = value
            else:
                raise ReactionMenuException(f"When setting the 'navigation_speed' of a menu, {value!r} is not a valid value")
        else:
            # this is here because even though the exception is raised, the main session task has already started so the exception will not stop the main session task.
            # i do not want the menu to continue functioning after an exception involving that menu was raised
            cls._force_stop(self)

            raise MenuAlreadyRunning(f'You cannot set the navigation speed when the menu is already running. Menu name: {self._name!r}')

    @property
    def only_roles(self) -> List[discord.Role]:
        """ .. added:: v1.0.9"""
        return self._only_roles
    
    @only_roles.setter
    def only_roles(self, value):
        """A property getter/setter for kwarg "only_roles"
        
        Example
        -------
        ```
        menu = Menu(ctx, ...)

        rookie = ctx.guild.get_role(87445687123745754)
        legend = ctx.guild.get_role(19873261980198704)
        
        menu.only_roles = [rookie, legend]
        >>> print(menu.only_roles)
        ```
        Returns
        -------
        List[:class:`discord.Role`]:
            If not set, defaults to :class:`None`

            .. added:: v1.0.9
        """
        if isinstance(value, list):
            if all([isinstance(i, discord.Role) for i in value]):
                self._only_roles = value
            else:
                raise IncorrectType('"only_roles" expected a list of discord.Role. All values were not of type discord.Role')
        else:
            raise IncorrectType(f'"only_roles" expected a list, got {value.__class__.__name__}')

    @property
    def style(self) -> str:
        return self._style

    @style.setter
    def style(self, value):
        """A property getter/setter for kwarg "style"
        
        Example
        -------
        ```
        menu = Menu(ctx, ...)
        menu.style = 'On $ out of &'

        # in the embed footer, it would produce
        'On 1 out of 5'
        ```
        Returns
        -------
        :class:`str`:
            If not set, defaults to "Page $/&"
        """
        self._style = str(value)
    
    @property
    def clear_reactions_after(self) -> bool:
        return self._clear_reactions_after

    @clear_reactions_after.setter
    def clear_reactions_after(self, value):
        """A property getter/setter for kwarg "clear_reactions_after"
        
        Example
        -------
        ```
        menu = Menu(ctx, ...)
        menu.clear_reactions_after = True
        >>> print(menu.clear_reactions_after)
        True
        ```
        Returns
        -------
        :class:`bool`:
            If not set, defaults to `True`
        """
        if isinstance(value, bool):
            self._clear_reactions_after = value
        else:
            raise IncorrectType(f'"clear_reactions_after" expected bool, got {value.__class__.__name__}')

    @property
    def timeout(self) -> float:
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        """A property getter/setter for kwarg "timeout"
        
        Example
        -------
        ```
        menu = Menu(ctx, ...)
        menu.timeout = 30.0
        >>> print(menu.timeout)
        30.0
        ```
        Returns
        -------
        Union[:class:`int`, :class:`float`, :class:`None`]:
            If not set, defaults to `60.0`
        """
        if isinstance(value, (int, float, type(None))):
            self._timeout = value
        else:
            raise IncorrectType(f'"timeout" expected float, int, or None, got {value.__class__.__name__}')

    @property
    def show_page_director(self) -> bool:
        return self._show_page_director

    @show_page_director.setter
    def show_page_director(self, value):
        """A property getter/setter for kwarg "show_page_director"
        
        Example
        -------
        ```
        menu = Menu(ctx, ...)
        menu.show_page_director = True
        >>> print(menu.show_page_director)
        True
        ```
        Returns
        -------
        :class:`bool`:
            If not set, defaults to `True`
        """
        if isinstance(value, bool):
            self._show_page_director = value
        else:
            raise IncorrectType(f'"show_page_director" expected bool, got {value.__class__.__name__}')

    @property
    def delete_interactions(self) -> bool:
        """.. added:: v1.0.2"""
        return self._delete_interactions

    @delete_interactions.setter
    def delete_interactions(self, value):
        """A property getter/setter for kwarg "delete_interactions"
        
        Example
        -------
        ```
        menu = Menu(ctx, ...)
        menu.delete_interactions = True
        >>> print(menu.delete_interactions)
        True
        ```
        Returns
        -------
        :class:`bool`:
            If not set, defaults to `True`
            
            .. added:: v1.0.2
        """
        if isinstance(value, bool):
            self._delete_interactions = value
        else:
            raise IncorrectType(f'"delete_interactions" expected bool, got {value.__class__.__name__}')

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value):
        """A property getter/setter for kwarg "name"
        
        Example
        -------
        ```
        menu = Menu(ctx, ...)
        menu.name = 'my menu'
        >>> print(menu.name)
        my menu
        ```
        Returns
        -------
        :class:`str`:
            If not set, defaults to :class:`None`
        """
        self._name = str(value)

    @property
    def all_can_react(self) -> bool:
        return self._all_can_react

    @all_can_react.setter
    def all_can_react(self, value):
        """A property getter/setter for kwarg "all_can_react"
        
        Example
        -------
        ```
        menu = Menu(ctx, ...)
        menu.all_can_react = True
        >>> print(menu.all_can_react)
        True
        ```
        Returns
        -------
        :class:`bool`:
            If not set, defaults to `False` 
        """
        if isinstance(value, bool):
            self._all_can_react = value
        else:
            raise IncorrectType(f'"all_can_react" expected bool, got {value.__class__.__name__}')

    @property
    def delete_on_timeout(self) -> bool:
        """.. added:: v1.0.8"""
        return self._delete_on_timeout

    @delete_on_timeout.setter
    def delete_on_timeout(self, value):
        """A property getter/setter for kwarg "delete_on_timeout"
        
        Example
        -------
        ```
        menu = Menu(ctx, ...)
        menu.delete_on_timeout = True
        >>> print(menu.delete_on_timeout)
        True
        ```
        Returns
        -------
        :class:`bool`:
            If not set, defaults to `False`

            .. added:: v1.0.8
        """
        if isinstance(value, bool):
            self._delete_on_timeout = value
        else:
            raise IncorrectType(f'"delete_on_timeout" expected bool, got {value.__class__.__name__}')

    @classmethod
    def _remove_session(cls, menu, task):
        """|class method| Upon session completion whether by timeout, call to :meth:`Menu.stop`, or exception in the main session task, remove it from the list of active sessions as well
        as the task from the task pool
        
            .. added:: v1.0.1

            .. changes::
                v1.0.9
                    Added :param:`task`
                    Added removal of task from the task sessions pool upon completion
        """
        if menu in cls._active_sessions:
            cls._active_sessions.remove(menu)
        if task in cls._task_sessions_pool:
            cls._task_sessions_pool.remove(task)
    
    @classmethod
    def get_menu_from_message(cls, message_id: int):
        """|class method| Return the menu object associated with the message with the given ID
        
        Parameters
        ----------
        message_id: :class:`int`
            The `discord.Message.id` from the menu message
        
        Returns
        -------
        The menu object. Can be :class:`None` if the menu is not found in this list of active menu sessions
            
            .. added:: v2.0.0
        """
        for menu in cls._active_sessions:
            if menu._msg.id == message_id:
                return menu
        return None
    
    @classmethod
    def remove_limit(cls):
        """|class method| Remove the limits currently set for reaction menu's
        
            .. added:: v2.0.0
        """
        cls._sessions_limited = False
        cls._sessions_limit_details = None
    
    @classmethod
    def get_all_dm_sessions(cls):
        """|class method| Returns all active DM menu sessions
        
        Returns
        -------
        :class:`list`:
            Can return :class:`None` if the there are no active DM sessions

            .. added:: v2.0.0
        """
        dm_sessions = [session for session in cls._active_sessions if session.message.guild is None]
        return dm_sessions if dm_sessions else None
    
    @classmethod
    def update_all_turn_every(cls, turn_every: Union[int, float]):
        """|class method| Update the amount of seconds to wait before going to the next page for all active auto-paginated sessions. When updated, the new value doesn't go into effect until the last
        round of waiting (:param:`turn_every`) completes for each menu

        Warning
        -------
        Setting :param:`turn_every` to a number that's too low exposes you to API abuse because an edit of a message will be occurring too quickly.
        It is your responsibility to make sure an appropriate/safe value is set, *especially* if the menu has a timeout of :class:`None`
        
        Parameter
        ---------
        turn_every: Union[:class:`int`, :class:`float`]
            The amount of seconds to wait before going to the next page
        
        Raises
        ------
        - `ReactionMenuException`: Parameter :param:`turn_every` was not greater than or equal to one

            .. added:: v1.0.9
        """
        if turn_every >= 1:
            auto_sessions = [session for session in cls._active_sessions if session._auto_paginator]
            for session in auto_sessions:
                session.update_turn_every(turn_every)
        else:
            raise ReactionMenuException('Parameter "turn_every" must be greater than or equal to one')

    @classmethod
    def get_all_sessions(cls):
        """|class method| Returns all active menu sessions
        
        Returns
        -------
        :class:`list`:
            A list of :class:`ReactionMenu` or :class:`TextMenu` depending on the instance. Can be an empty list if there are no active sessions

            .. added:: v1.0.9

            .. changes::
                v2.0.0
                    Changed return type from :class:`list` to :class:`None` if list is empty
        """
        return cls._active_sessions if cls._active_sessions else None
    
    @classmethod
    def get_session(cls, name: str):
        """|class method| Return a menu instance by it's name. Can return a :class:`list` of menu instances if multiple instances of the menu with the supplied name are running. 
        Can also return :class:`None` if the menu with the supplied name was not found in the list of active sessions
        
        Parameter
        ---------
        name: :class:`str`
            The name of the menu to return

            .. added:: v1.0.9

            .. note::
                Dont add a `Returns` since this is an abc. The main description above provides enough context
        """
        name = str(name)
        sessions = [session for session in cls._active_sessions if session.name == name]
        if sessions:
            if len(sessions) == 1:
                return sessions[0]
            else:
                return sessions
        else:
            return None
    
    @classmethod
    def get_sessions_count(cls) -> int:
        """|class method| Returns the number of active sessions
        
        Returns
        -------
        :class:`int`:
            The amount of active sessions

            .. added:: v1.0.2
        """
        return len(cls._active_sessions)

    @classmethod
    def set_sessions_limit(cls, limit: int, per: str='guild', message: str='Too many active reaction menus. Wait for other menus to be finished.'):
        """|class method| Sets the amount of menu sessions that can be active at the same time per guild, channel, or member. Should be set before any menus are started. Ideally this should only
        be set once. But can be set at anytime if there are no active menu sessions
            
            .. added:: v1.0.1

        Parameters
        ----------
        limit: :class:`int`
            The amount of menu sessions allowed
        
        per: :class:`str`
            (optional) How menu sessions should be limited. Options: "channel", "guild", "member" (defaults to "guild")
        
        message: :class:`str`
            (optional) Message that will be sent informing users about the menu limit when the limit is reached. Can be :class:`None` for no message

        Example
        -------
        ```
        class Example(commands.Cog):
            def __init__(self, bot):
                self.bot = bot
                Menu.set_sessions_limit(3, per='member', 'Sessions are limited to 3 per member')
        ```
            
        Raises
        ------
        - `ReactionMenuException`: Attempted to call method when there are menu sessions that are already active or attempted to set a limit of zero
        - `IncorrectType`: The :param:`limit` parameter was not of type `int`

            .. changes::
                v1.0.9
                    Replaced now removed class :meth:`_cancel_all_sessions` with class :meth:`_force_stop`
                    Added :exc:`IncorrectType`
                v2.0.0
                    Added :param:`per` and initialization of new limits
        """
        if len(cls._active_sessions) != 0:
            # because of the created task(s) when making a session, the menu is still running in the background so manually stopping them is required to stop using resources
            cls._force_stop(None)
            raise ReactionMenuException('Method "set_sessions_limit" cannot be called when any other menus have started')

        if not isinstance(limit, int):
            raise IncorrectType(f'Parameter "limit" expected int, got {limit.__class__.__name__}')
        else:
            if limit <= 0:
                raise ReactionMenuException('The session limit must be greater than or equal to one')
            
            per = str(per).lower()
            if per not in ('guild', 'channel', 'member'):
                raise ReactionMenuException('Parameter value of "per" was not recognized. Expected: "channel", "guild", or "member"')

            LimitDetails = collections.namedtuple('LimitDetails', ['limit', 'per', 'message'])
            cls._sessions_limit_details = LimitDetails(limit=limit, per=per, message=message)
            cls._sessions_limited = True
    
    @classmethod
    def _force_stop(cls, target: 'Menu'):
        """This method is basically the safe version of now removed :meth:`Menu.cancel_all_sessions()`. Since the old way of "pulling the plug" is no longer
        a safe way to shutdown the processing of all active menus. How this works is:
        
        - :attr:`_is_running` is set to `False`
        - The menu (:param:`target`) is removed from the list of active sessions
        - The :attr:`_main_session_task` is removed from the sessions task pool. It must be removed before its cancelled otherwise it can never be removed because it's cancelled
        - The :attr:`_main_session_task` is cancelled
        - From there, there being :meth:`_main_session_callback`, it stops any background tasks that may be running (timeout countdown or runtime)

        This almost does the same thing as :meth:`Menu.stop()`. The only difference is that the menu message will not be deleted and reactions will not be removed

        Parameter
        ---------
        target: Union[:class:`Menu`, :class:`None`]
            If :class:`None`, this cancels *ALL* active sessions

            .. added:: v1.0.9
        """
        if target:
            for session in cls._active_sessions:
                if session == target:
                    target._is_running = False
                    task = target._main_session_task
                    cls._active_sessions.remove(target)
                    cls._task_sessions_pool.remove(task)
                    task.cancel()
                    return
        else:
            for session in cls._active_sessions:
                session._is_running = False
                task = session._main_session_task
                task.cancel()
            cls._active_sessions.clear()
            cls._task_sessions_pool.clear()

    @classmethod
    async def stop_session(cls, name: str, include_all: bool=False):
        """|coro class method| Stop a specific menu with the supplied name
        
        Parameters
        ----------
        name: :class:`str`
            The menus name
        
        include_all: :class:`bool`
            (optional) If set to `True`, it stops all menu sessions with the supplied name. If `False`, stops only the most recently started menu with the supplied name (defaults to `False`)
        
        Raises
        ------
        - `ReactionMenuException`: The session with the supplied name was not found

            .. added:: v1.0.9
        """
        name = str(name)
        matched_sessions = [session for session in cls._active_sessions if name == session.name]
        if matched_sessions:
            if include_all:
                for session in matched_sessions:
                    await session.stop()
            else:
                await matched_sessions[-1].stop()
        else:
            raise ReactionMenuException(f'Menu with name {name!r} was not found in the list of active menu sessions')
    
    @classmethod
    async def stop_all_auto_sessions(cls):
        """|coro class method| Stops all auto-paginated sessions that are currently running

            .. added:: v1.0.9
        """
        auto_sessions = [session for session in cls._active_sessions if session._auto_paginator]
        for session in auto_sessions:
            await session.stop()

    @classmethod
    async def stop_all_sessions(cls):
        """|coro class method| Stops all sessions that are currently running

            .. added:: v1.0.9
        """
        while cls._active_sessions:
            session = cls._active_sessions[0]
            await session.stop()

    async def _handle_session_limits(self) -> bool:
        """|coro| Determine if the menu session is currently limited, if so, send the error message and return `False` indicating that further code execution (starting the menu) should be cancelled
        
            .. added:: v2.0.0

            .. note:: use to be :meth:`_is_currently_limited`
        """
        cls = self.__class__
        details: 'NamedTuple' = cls._sessions_limit_details
        can_proceed = True
        
        # if the menu is in a DM, handle it seperatly
        if self._ctx.guild is None:
            dm_sessions = cls.get_all_dm_sessions()
            if dm_sessions:
                user_dm_sessions = [session for session in dm_sessions if session.owner.id == self._ctx.author.id]
                if len(user_dm_sessions) >= details.limit:
                    can_proceed = False
        else:
            if details.per == 'guild':
                guild_sessions = [session for session in cls._active_sessions if session.message.guild is not None]
                if len(guild_sessions) >= details.limit:
                    can_proceed = False
            
            elif details.per == 'member':
                member_sessions = [session for session in cls._active_sessions if session.owner.id == self._ctx.author.id]
                if len(member_sessions) >= details.limit:
                    can_proceed = False
            
            elif details.per == 'channel':
                channel_sessions = [session for session in cls._active_sessions if session.message.channel.id == self._ctx.channel.id]
                if len(channel_sessions) >= details.limit:
                    can_proceed = False
        
        if can_proceed:
            return True
        else:
            await self._ctx.send(details.message)
            return False
    
    async def _handle_fast_navigation(self):
        """|coro| If either of the below events are dispatched, return the result (reaction, user) of the coroutine object. Used in :meth:`Menu._execute_session` for :attr:`Menu.FAST`.
        Can timeout, `.result()` raises :class:`asyncio.TimeoutError` but is caught in :meth:`Menu._execute_session` for proper cleanup. This is the core function as to how the 
        navigation speed system works
        
            .. added:: v1.0.5

                .. Note :: Handling of aws's 
                    The additional time (+ 0.1) is needed because the items in :var:`wait_for_aws` timeout at the exact same time. Meaning that there will never be an object in :var:`pending` (which is what I want)
                    which renders the ~return_when param useless because the first event that was dispatched is stored in :var:`done`. Since they timeout at the same time,
                    both aws are stored in :var:`done` upon timeout. 
                    
                    The goal is to return the result of a single :meth:`discord.Client.wait_for`, the result is returned but the :exc:`asyncio.TimeoutError`
                    exception that was raised in :meth:`asyncio.wait` (because of the timeout by the other aws) goes unhandled and the exception is raised. The additional time allows the 
                    cancellation of the task before the exception (Task exception was never retrieved) is raised 
            
            .. changes::
                v1.0.7
                    Added :func:`_proper_timeout` and replaced the ~`reaction_remove` ~`timeout` value to a function that handles cases where there is a timeout vs no timeout
        """
        def _proper_timeout():
            """In :var:`wait_for_aws`, if the menu does not have a timeout (`Menu.timeout = None`), :class:`None` + :class:`float`, the float being "`self._timeout + 0.1`" from v1.0.5, will fail for obvious reasons. This checks if there is no timeout, 
            and instead of adding those two together, simply return :class:`None` to avoid :exc:`TypeError`. This would happen if the menu's :attr:`Menu.navigation_speed` was set to :attr:`Menu.FAST` and
            the :attr:`Menu.timeout` was set to :class:`None`
                
                .. added:: v1.0.7
            """
            if self._timeout is not None:
                return self._timeout + 0.1
            else:
                return None

        wait_for_aws = (
            self._bot.wait_for('reaction_add', check=self._wait_check, timeout=self._timeout),
            self._bot.wait_for('reaction_remove', check=self._wait_check, timeout=_proper_timeout()) 
        )
        done, pending = await asyncio.wait(wait_for_aws, return_when=asyncio.FIRST_COMPLETED)

        temp_pending = list(pending)
        temp_pending[0].cancel()

        temp_done = list(done)
        return temp_done[0].result()

    def _duplicate_emoji_check(self):
        """Since it's possible for the user to change the emoji of a :class:`Button` after an instance has been created and added to a :class:`Menu` instance. Before the menu starts, make sure there are no duplicates because if there are,
        it essentially renders that :class:`Button` useless because discord only allows unique reactions to be added.
        
            .. added:: v1.0.5
        """
        counter = collections.Counter(self._extract_all_emojis())
        if max(counter.values()) != 1:
            raise ReactionMenuException('There cannot be duplicate emojis when using Buttons. All emojis must be unique')

    def _duplicate_name_check(self):
        """Since it's possible for the user to change the name of a :class:`Button` after an instance has been created and added to a :class:`Menu` instance. Before the menu starts, make sure there are no duplicates because if there are,
        methods such as :meth:`Menu.get_button_by_name` could return the wrong :class:`Button` object.
        
            .. added:: v1.0.5

            .. changes::
                v1.0.9
                    Added if check for `counter.values()`. This was added because by default, the :class:`ReactionMenu` constuctor parameters `back_button` and `next_button` already have a name. If the buttons were all removed and more
                    buttons were added, it is possible for those buttons to not have a name, thus resulting in an empty sequence error when checked in `max()`. This checks if all/any the new buttons have a name and if not, ignore this check
        """
        counter = collections.Counter([btn.name.lower() for btn in self._all_buttons if btn.name is not None])
        if counter.values():
            if max(counter.values()) != 1:
                raise ReactionMenuException('There cannot be duplicate names when using Buttons. All names must be unique')

    def _maybe_new_style(self, counter, total_pages) -> str: 
        """Sets custom page director styles"""
        if self._style:
            if self._style.count('$') == 1 and self._style.count('&') == 1:
                temp = self._style # copy it to a new variable so its not being changed in every call
                temp = temp.replace('$', str(counter))
                temp = temp.replace('&', str(total_pages))
                return temp
            else:
                raise ImproperStyleFormat
        else:
            return f'Page {counter}/{total_pages}'
    
    async def _contact_relay(self, user, button):
        """|coro abc| Calls the relay function that was set

            .. added:: v1.0.9
        """
        if self._relay_function:
            RelayPayload = collections.namedtuple('RelayPayload', ['member', 'button', 'time', 'menu'])
            relay = RelayPayload(member=user, button=button, time=datetime.utcnow(), menu=self)
            try:
                if asyncio.iscoroutinefunction(self._relay_function):
                    await self._relay_function(relay)
                else:
                    self._relay_function(relay)
            except TypeError:
                raise ReactionMenuException('When setting a relay, the relay function must have exactly one positional argument')
    
    async def _track_runtime(self):
        """|coro abc| Track how long (in seconds) the menu session has been active 
        
            .. added:: v1.0.9
        """
        while self._is_running:
            self._run_time += 1
            await asyncio.sleep(1)
    
    async def _auto_countdown(self):
        """|coro abc| Start the countdown until the auto-pagination process ends. This also handles if :attr:`_delete_on_timeout`
            
            .. added:: v1.0.9
        """
        if self._timeout:
            timeout = self._timeout # make a copy so im not actually changing the value of self._timeout in the loop
            while timeout and self._is_running:
                await asyncio.sleep(1)
                timeout -= 1
            await self.stop(delete_menu_message=self._delete_on_timeout)

    def _wait_check(self, reaction, user) -> bool:
        """|abc| Predicate for :meth:`discord.Client.wait_for`. This also handles :attr:`_all_can_react`
        
            .. changes::
                v1.0.9
                    Added handling for :attr:`_only_roles`
                    Added handling for :attr:`_menu_owner`
        """
        not_bot = False
        correct_msg = False
        correct_user = False

        if not user.bot:
            not_bot = True
        
        if reaction.message.id == self._msg.id:
            correct_msg = True

        if self._only_roles:
            if self._all_can_react:
                self._all_can_react = False
            for role in self._only_roles:
                if role in user.roles:
                    self._ctx.author = user
                    correct_user = True
                    break

        if self._all_can_react:
            self._ctx.author = user
            correct_user = True
        
        if user == self._menu_owner and not correct_user:
            self._ctx.author = user
            correct_user = True

        return all((not_bot, correct_msg, correct_user))

    def _extract_all_emojis(self) -> List[str]:
        """Returns a list of the emojis that represents the button"""
        return [button.emoji for button in self._all_buttons]
    
    def _verify_dm_usage(self, send_to):
        """|abc| If the session is going to start in a DM, override the attributes with the necessary values in order for the menu to function properly in a DM environment
            
            .. added:: v1.0.9
        """
        if self._ctx.guild is None:
            self._is_dm_session = True

            # disable everything that is related to removing reactions. bots cannot remove reactions from users in DMs
            self._clear_reactions_after = False
            self._navigation_speed = Menu.FAST
            self._delete_interactions = False

            # in a DM, users don't have roles
            self._only_roles = None

            # if the :attr:`Menu._timeout` is :class:`None`, set it back to the default value. there's simply no need for a menu created in a DM to be
            # running indefinitely. more than likely, the user will be accessing the menu for a short duration of time. afterwards, its safe to assume they
            # could close the DM. if they close the DM and have no intention of coming back to it, that particular menu instance will be stuck in the `discord.Client.wait_for` state.
            # with nothing to wait for and the menu running indefinitely, the menu instance becomes literally useless
            if self._timeout is None:
                self._timeout = 60.0

            # if the :attr:`Menu._auto_paginator` is `True`, set it back to the default value. DM use of an auto-pagination menu is not what it is intended for,
            # but most importantly, is risky. i want all auto-pagination menus to be created, controlled, and be known to the user. if a member of a guild was to spam
            # DM the users bot and start numerous amounts of auto-pagination menus in a single DM channel, the user could end up abusing the API because there would be multiple messages being
            # edited in rapid succession in the same channel. to avoid this all together, just disable auto-pagination menus in DMs
            if self._auto_paginator:
                self._auto_paginator = False
            
            # in a DM, send_to cannot function
            if send_to:
                self._send_to_channel = None
    
    def _determine_location(self, path):
        """Set the text channel where the menu should start
            
            .. added:: v1.0.6

            .. changes::
                v1.0.9
                    Added if check for :attr:`Menu._is_dm_session`
        """
        if not self._is_dm_session:
            text_channels = self._ctx.guild.text_channels
            # channel name
            if isinstance(path, str):
                path = path.lower()
                channel = [ch for ch in text_channels if ch.name == path]
                if len(channel) == 1:
                    self._send_to_channel = channel[0]
                else:
                    NO_CHANNELS_ERROR = f'When using parameter "send_to" in ReactionMenu.start(), there were no channels with the name {path!r}'
                    MULTIPLE_CHANNELS_ERROR = f'When using parameter "send_to" in ReactionMenu.start(), there were {len(channel)} channels with the name {path!r}. With multiple channels having the same name, the intended channel is unknown'  
                    raise ReactionMenuException(NO_CHANNELS_ERROR if len(channel) == 0 else MULTIPLE_CHANNELS_ERROR)

            # channel ID
            elif isinstance(path, int):
                channel = [ch for ch in text_channels if ch.id == path]
                if len(channel) == 1:
                    guild = self._ctx.guild
                    channel = guild.get_channel(path)
                    self._send_to_channel = channel
                else:
                    raise ReactionMenuException(f'When using parameter "send_to" in ReactionMenu.start(), the channel ID {path} was not found')

            # channel object
            elif isinstance(path, discord.TextChannel):
                # it's safe to just set it as the channel object because if the user was to use :meth:`discord.Guild.get_channel`, discord.py would return the obj or :class:`None`
                # which if :class:`None` is sent to :meth:`ReactionMenu.start`, it would be handled in the the "default" elif below
                self._send_to_channel = path
            
            # default 
            elif isinstance(path, type(None)):
                pass

            else:
                raise IncorrectType(f'When setting the "send_to" in ReactionMenu.start(), the value must be the name of the channel (str), the channel ID (int), or the channel object (discord.TextChannel), got {path.__class__.__name__}') 

    def _main_session_callback(self, task: asyncio.Task):
        """|abc| Used for "handling" unhandled exceptions in :meth:`Menu._execute_session`. Because that method is running in the background (asyncio.create_task), a callback is needed
        when an exception is raised or else all exceptions are suppressed/lost until the program terminates, which it won't because it's a bot. This re-raises those exceptions
        if any so proper debugging can occur both on my end and the users end (using :attr:`ButtonType.CALLER`)
            
            .. added:: v1.0.3

            .. changes::
                v1.0.5
                    Added try/except to properly handle/display the appropriate tracebacks for when tasks are cancelled
                v1.0.9
                    - Moved from :class:`ReactionMenu` to abc. Was "_asyncio_exception_callback"
                    - Added handling for background tasks
        """
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        finally:
            # if this executes, the main session task ended because of an exception
            if not task.cancelled():
                # 1 - set the true state of `_is_running`
                # 2 - setting this to `False` stops the run time tracking task
                # 3 - if its an auto-pagination menu, setting this to `False` stops the auto countdown task
                self._is_running = False
                
                # removing the session/session task from the list of active sessions/task pool is needed here because the menu did not end gracefully.
                # meaning a call to :meth:`Menu.stop` was not made so the task and sessions are still in their associated lists
                cls = self.__class__
                cls._remove_session(self, task)
    
    def set_on_timeout(self, func: object):
        """Set the function to be called when the menu times out

        Parameters
        ----------
        func: :class:`object`
            The function object that will be called when the menu times out. The function should contain a single positional argument
            and should not return anything. The argument passed to that function is an instance of the menu.
        
        Raises
        ------
        - `ReactionMenuException`: Parameter "func" was not a callable object

            ..added:: v2.0.0
        """
        if not callable(func): raise ReactionMenuException('Parameter "func" must be callable')
        self._on_timeout_details = func
    
    def set_relay(self, func):
        """Set a function to be called with a given set of information when a reaction is pressed on the menu. The information passed is `RelayPayload`, a named tuple object. The
        named tuple contains the following attributes:

        - `member`: The :class:`discord.Member` object of the member who pressed the reaction. Could be :class:`discord.User` if the menu reaction was pressed in a direct message
        - `button`: The :class:`Button` object of the reaction that was pressed
        - `time`: The :class:`datetime` object of when the reaction was pressed. The time is in UTC
        - `menu`: Depending on the instance, the :class:`ReactionMenu` or :class:`TextMenu` object

        Parameter
        ---------
        func: Callable[[:class:`NamedTuple`], :class:`None`]
            The function should only contain a single positional argument. Discord.py command functions (`@bot.command()`) not supported
        
        Raises
        ------
        - `IncorrectType`: The argument provided was not callable
        
            .. added:: v1.0.9
        """
        if callable(func):
            self._relay_function = func
        else:
            raise IncorrectType('When setting the relay, argument "func" must be callable')
    
    def remove_relay(self):
        """Remove the relay that's been set

            .. added:: v2.0.1
        """
        self._relay_function = None
    
    @ensure_not_primed
    def set_as_auto_paginator(self, turn_every: Union[int, float]):
        """Set the menu to turn pages on it's own every x seconds. If this is set, reactions will not be applied to the menu
        
        Warning
        -------
        Setting :param:`turn_every` to a number that's too low exposes you to API abuse because an edit of a message will be occurring too quickly.
        It is your responsibility to make sure an appropriate/safe value is set, *especially* if the menu has a timeout of :class:`None`
        
        Parameter
        ---------
        turn_every: Union[:class:`int`, :class:`float`]
            The amount of seconds to wait before going to the next page
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call this method after the menu has started
        - `ReactionMenuException`: Parameter :param:`turn_every` was not greater than or equal to one

            .. added:: v1.0.9
        """
        if turn_every >= 1:
            self._auto_paginator = True
            self._auto_turn_every = turn_every
        else:
            raise ReactionMenuException('Parameter "turn_every" must be greater than or equal to one')
            
    def update_turn_every(self, turn_every: Union[int, float]):
        """Change the amount of seconds to wait before going to the next page. When updated, the new value doesn't go into effect until the last round of waiting (:param:`turn_every`) completes

        Warning
        -------
        Setting :param:`turn_every` to a number that's too low exposes you to API abuse because an edit of a message will be occurring too quickly.
        It is your responsibility to make sure an appropriate/safe value is set, *especially* if the menu has a timeout of :class:`None`
        
        Parameter
        ---------
        turn_every: Union[:class:`int`, :class:`float`]
            The amount of seconds to wait before going to the next page
        
        Raises
        ------
        - `ReactionMenuException`: Parameter :param:`turn_every` was not greater than or equal to one or this method was called from a menu that was not set as an auto-pagination menu

            .. added:: v1.0.9
        """
        if self._auto_paginator:
            if turn_every >= 1:
                self._auto_turn_every = turn_every
            else:
                raise ReactionMenuException('Parameter "turn_every" must be greater than or equal to one')
        else:
            raise ReactionMenuException('Menu is not set as auto-paginator')
    
    def get_button_by_name(self, name: str) -> Button:
        """Retrieve a :class:`Button` object by its name if the kwarg "name" for that :class:`Button` was set

        Parameter
        ---------
        name: :class:`str`
            The :class:`Button` name
        
        Returns
        -------
        :class:`Button`:
           The :class:`Button` that matched the name. Could be :class:`None` if the :class:`Button` was not found
        """
        name = str(name).lower()
        for btn in self._all_buttons:
            if btn.name == name:
                return btn
        return None
    
    async def stop(self, *, delete_menu_message=False, clear_reactions=False):
        """|coro| Stops the process of the menu with the option of deleting the menu's message or clearing reactions upon stop
        
		Parameters
		----------
		delete_menu_message: :class:`bool`
			(optional) Delete the menu message when stopped (defaults to `False`)

		clear_reactions: :class:`bool`
			(optional) Clear the reactions on the menu's message when stopped (defaults to `False`)

                .. changes::
                    v1.0.5
                        Added ID handling for static/dynamic task names
                    v1.0.9
                        .. container:: Breakdown of Change

                            Added try/except/finally for handling of :param:`delete_menu_message` and :param:`clear_reactions`. If any exception was to occur during the message deletion or reaction removal
                            process, the most important thing is to still cancel the session [finally]. 

                            Before, the call to [session_task.cancel()] was the first execution in this method; and in <= v1.0.8, that was okay because a call to this method would only happen externally. Meaning only the user
                            could call this method. Now in v1.0.9, this method can be called internally. The main internal call is from the [asyncio.TimeoutError] section in :meth:`_execute_session`. Now that
                            this method is called from :meth:`_execute_session`, that means this method is now being kept alive by the main session task. Before, [asyncio.TimeoutError] would do its own thing, that thing being
                            handling the removal of reactions/deleting the menu message from a *seperate task*.
                            
                            Now in v1.0.9, this method is apart of the [asyncio.TimeoutError] process, so if I call [session_task.cancel()] first, this method could be cancelled because it was called from a method (:meth:`_execute_session`)
                            who's life cycle is dependant on the session task (see below for a more clear explanation). The main thing that needs to occur when this method is called from :meth:`_execute_session` ([asyncio.TimeoutError])
                            is that ALL expectations are fulfilled. Those expectations are deleting the menu message or removing the reactions and more importantly, stopping the [session task]. Since stopping the [session task] is the most important,
                            it is placed in the [finally] of this method. So no matter what happens, even if deleting the message or removing the reactions failed, stopping the [session task] will always be completed

                            It is to be noted the [session_task.cancel()] is now the last thing to be executed because of a race condition. If I was to put it as the first thing, it is possible for the main session task callback to be completed
                            first, and if that happens the rest of the code will not execute. From what i've tested, I technically could put it there (at the top) because the call to class :meth:`_remove_session` and setting :attr:`_is_running` to `False`
                            happens much faster than the main session task callback takes to fully execute. But to be on the safe side, just put it at the end.

                        - Removed ID handling for static/dynamic task names (:meth:`_get_proper_task`)
                        - Moved to ABC
                    v2.0.0
                        Added handling for on_timeout setting
        """
        if self._is_running:
            try:
                if delete_menu_message:
                    await self._msg.delete()
                    return
                if clear_reactions:
                    await self._msg.clear_reactions() 
            except discord.DiscordException as dpy_error:
                raise dpy_error
            finally:
                self._is_running = False

                # since this is an abc and I haven't implemented a way to know which current class (ReactionMenu or TextMenu) is calling this method
                # the method doesnt know which class to access class :meth:`_remove_session` from. what is known though is that both classes have the class :meth:`_remove_session`
                # so access the class and in turn, access the class method
                cls = self.__class__
                cls._remove_session(self, self._main_session_task)

                # handle `on_timeout`
                if self._on_timeout_details and self._menu_timed_out:
                    func = self._on_timeout_details
                    
                    # call the timeout function but ignore any and all exceptions that may occur during the function timeout call.
                    # the most important thing here is to ensure the menu is properly shutdown (task is cancelled) upon timeout and if an exception occurs
                    # the process will not complete
                    try:
                        if asyncio.iscoroutinefunction(func): await func(self)
                        else: func(self)
                    except Exception as error:
                        warnings.formatwarning = lambda msg, *args, **kwargs: f'{msg}'
                        
                        # NOTE" inspect imported with "from .errors import *"
                        warnings.warn(inspect.cleandoc(
                            f"""
                            UserWarning: The function you have set in method ReactionMenu.set_on_timeout() raised on error

                            -> {error.__class__.__name__}: {error}
                            
                            This error has been ignored so the menu timeout process can complete
                            """
                        ))
                self._main_session_task.cancel()

    @ensure_not_primed
    def clear_all_buttons(self):
        """Delete all buttons that have been added
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        
            .. changes::
                v1.0.9
                    Added instantiation of :attr:`Menu._all_buttons_removed`
        """
        self._all_buttons.clear()
        self._all_buttons_removed = True

    @ensure_not_primed
    def remove_button(self, identity: Union[str, Button]):
        """Remove a button by its name or its object

        Parameter
        ---------
        identity: Union[:class:`str`, :class:`Button`]
            Name of the button or the button object itself

        Raises
        ------
        - `ButtonNotFound`: Button with given identity was not found

            .. changes::
                v1.0.9
                    Added if check for :attr:`_all_buttons` and instantiation for :attr:`_all_buttons_removed`
        """
        if isinstance(identity, str):
            btn_name = identity.lower()
            for btn in self._all_buttons:
                if btn.name == btn_name:
                    self._all_buttons.remove(btn)
                    break
            else:
                raise ButtonNotFound(f'Button "{btn_name}" was not found')

        elif isinstance(identity, Button):
            if identity in self._all_buttons:
                self._all_buttons.remove(identity)
            else:
                raise ButtonNotFound(f'Button {identity}, ({repr(identity)}) Could not be found in the list of active buttons')

        else:
            raise IncorrectType(f'parameter "identity" expected str or Button, got {identity.__class__.__name__}')
        
        if len(self._all_buttons) == 0:
            self._all_buttons_removed = True

    def help_appear_order(self): 
        """Prints all button emojis you've added before this method was called to the console for easy copy and pasting of the desired order. 
        
        Note: If using Visual Studio Code, if you see a question mark as the emoji, you need to resize the console in order for it to show up. 
        """
        print(f'Registered button emojis: {self._extract_all_emojis()}')

    @ensure_not_primed
    def change_appear_order(self, *emoji_or_button: Union[str, Button]):
        """Change the order of the reactions you want them to appear in on the menu
        
        Parameter
        ---------
        *emoji_or_button: Union[:class:`str`, :class:`Button`]
            An argument list of the emojis themselves or :class:`Button` object
        
        Raises
        ------
        - `ImproperButtonOrderChange`: Missing or extra buttons 
        - `IncorrectType`: All values in the argument list were not of type :class:`str` or :class:`Button`
        - `NoButtons`: Attempted to change the appear order when no buttons were registered
        - `MenuAlreadyRunning`: Attempted to call this method after the menu has started

            .. changes::
                v1.0.9
                    - Moved method `sort_key` to here as a local function since this is the only place its used
                    - Slight revamp to this method
                    - Raise :exc:`NoButtons` if there are no registered buttons
                    - Raise :exc:`IncorrectType` if all values in the argument list were not of type :class:`str` or :class:`Button`
        """
        # NOTE: don't raise an exception if the user doesn't provide an argument list because :exc:`ImproperButtonOrderChange` already takes care of that

        if not self._all_buttons:
            raise NoButtons('You cannot change the appear order when no buttons have been registered')
        
        new_emoji_order = []
        original_emoji_order = self._extract_all_emojis()
        for item in emoji_or_button:
            if isinstance(item, str):       new_emoji_order.append(item)
            elif isinstance(item, Button):  new_emoji_order.append(item.emoji)
            else:   raise IncorrectType(f'When changing the button order, all values in the argument list must be of type str or Button, got {item.__class__.__name__}')
        
        if collections.Counter(new_emoji_order) == collections.Counter(original_emoji_order):
            
            def sort_key(item: Button):
                """Sort key for :attr:`_all_buttons`"""
                nonlocal new_emoji_order
                idx = new_emoji_order.index(item.emoji)
                return idx

            self._all_buttons.sort(key=sort_key)
        else:
            original_s = set(original_emoji_order)
            new_s = set(new_emoji_order)
            
            extras = new_s.difference(original_s)
            missing = original_s.difference(new_s)
            
            raise ImproperButtonOrderChange(missing, extras)

    @abc.abstractmethod
    async def _execute_navigation_type(self, *args, **kwargs):
        raise NotImplementedError
    
    @abc.abstractmethod
    async def _execute_session(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    async def _execute_auto_session(self, *args, **kwargs):
        raise NotImplementedError
    
    @abc.abstractmethod
    def refresh_auto_pagination_data(self, *args, **kwargs):
        raise NotImplementedError
    
    @abc.abstractmethod
    def add_button(self, button: Button):
        raise NotImplementedError

    @abc.abstractmethod
    async def start(self, *, send_to: Union[str, int, discord.TextChannel]=None):
        raise NotImplementedError
    