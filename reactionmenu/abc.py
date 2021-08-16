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

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .buttons import Button, ViewButton

import abc
import asyncio
import collections
import inspect
import warnings
from enum import Enum, IntEnum
from datetime import datetime
from typing import List, Union, Set

import discord
from discord.ext.commands import Context

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
        """Return the next page in the pagination process"""
        try:
            self.index += 1
            _ = self.pages[self.index]
        except IndexError:
            if self.index > self.total_pages:
                self.index = 0
            
            elif self.index < 0:
                self.index = self.total_pages
        finally:
            return self.pages[self.index]
    
    def prev(self) -> Union[discord.Embed, str]:
        """Return the previous page in the pagination process"""
        try:
            self.index -= 1
            _ = self.pages[self.index]
        except IndexError:
            if self.index > self.total_pages:
                self.index = 0
            
            elif self.index < 0:
                self.index = self.total_pages
        finally:
            return self.pages[self.index]
    
    def first_page(self) -> Union[discord.Embed, str]:
        """Return the first page in the pagination process
        
            .. added:: v3.0.0
        """
        self.index = 0
        return self.pages[self.index]

    def last_page(self) -> Union[discord.Embed, str]:
        """Return the last page in the pagination process
        
            .. added:: v3.0.0
        """
        self.index = self.total_pages
        return self.pages[self.index]


class DirectionalEmojis:
    """A set of basic emojis for your convenience to use as your buttons emoji
    - ◀️ as `BACK_BUTTON`
    - ▶️ as `NEXT_BUTTON`
    - ⏪ as `FIRST_PAGE`
    - ⏩ as `LAST_PAGE`
    - 🔢 as `GO_TO_PAGE`
    - ⏹️ as `END_SESSION`

        .. added:: v3.0.0
    """
    BACK_BUTTON = 	'◀️'
    NEXT_BUTTON = 	'▶️'
    FIRST_PAGE =  	'⏪'
    LAST_PAGE =   	'⏩'
    GO_TO_PAGE =  	'🔢'
    END_SESSION = 	'⏹️'


class BaseButton(metaclass=abc.ABCMeta):

    Emojis = DirectionalEmojis

    def __init__(self):
        self.name: str = None
        self.event: BaseButton.Event = None
        self._clicked_by = set()
        self._total_clicks = 0
        self._last_clicked: datetime = None
    
    @property
    @abc.abstractmethod
    def menu(self):
        raise NotImplementedError
    
    @property
    def clicked_by(self) -> Set[discord.Member]:
        """
        Returns
        -------
        Set[:class:`discord.Member`]:
            The members who clicked the button
        """
        return self._clicked_by
    
    @property
    def total_clicks(self) -> int:
        """
        Returns
        -------
        :class:`int`:
            The amount of clicks on the button
        """
        return self._total_clicks

    @property
    def last_clicked(self) -> datetime:
        """
        Returns
        -------
        :class:`datetime.datetime`:
            The time in UTC for when the button was last clicked. Can be :class:`None` if the button has not been clicked
        """
        return self._last_clicked

    def _update_statistics(self, user: Union[discord.Member, discord.User]):
        self._clicked_by.add(user)
        self._total_clicks += 1
        self._last_clicked = datetime.utcnow()

    class Event:
        """Set a to be disabled or removed when it has been clicked a certain amount of times
        
        Parameters
        ----------
        event: :class:`str`
            The action to take. Can either be "disable" or "remove"
        
        value: :class:`int`
            The amount set for the specified event. Must be >= 1. If value is <= 0, it is implicitly set to 1
            
            .. added:: v2.0.2
        """
        _disable = 'disable'
        _remove = 'remove'

        def __init__(self, event_type: str, value: int):
            if value <= 0: value = 1
            event_type = str(event_type).lower()
            
            if event_type in ('disable', 'remove'):
                self.event_type = event_type
                self.value = value
            else:
                raise ViewMenuException(f'Parameter "event_type" expected "disable" or "remove", got {event_type!r}')


class BaseMenu(metaclass=abc.ABCMeta):
    TypeEmbed = 1
    TypeEmbedDynamic = 2
    TypeText = 3

    _active_sessions = []
    _sessions_limited = False
    _sessions_limit_details = None

    def __init__(self, ctx: Context, menu_type: int, **kwargs):
        self._ctx = ctx
        self._menu_type = menu_type

        self._msg: discord.Message = None
        self._pc: _PageController = None
        self._buttons: List[Union[Button, ViewButton]] = []
        self._is_running = False

        # dynamic session
        self._main_page_contents = collections.deque()
        self._last_page_contents = collections.deque()
        self._dynamic_data_builder: List[str] = []
        self.wrap_in_codeblock: Union[str, None] = kwargs.get('wrap_in_codeblock')
        self.rows_requested: int = kwargs.get('rows_requested', 0)
        self.custom_embed: Union[discord.Embed, None] = kwargs.get('custom_embed')

        self._relay_info: NamedTuple = None
        self._on_timeout_details: 'function' = None
        self._menu_timed_out = False
        self._bypass_primed = False # used in :meth:`update()`
        self._pages: List[Union[discord.Embed, str]] = []

        # kwargs
        self.delete_on_timeout: bool = kwargs.get('delete_on_timeout', False)
        self.only_roles: Union[List[discord.Role], None] = kwargs.get('only_roles')
        self.show_page_director: bool = kwargs.get('show_page_director', True)
        self.name: Union[str, None] = kwargs.get('name')
        self.style: Union[str, None] = kwargs.get('style', 'Page $/&')
        self.all_can_click: bool = kwargs.get('all_can_click', False)
        self.delete_interactions: bool = kwargs.get('delete_interactions', True)
        self.allowed_mentions: discord.AllowedMentions = kwargs.get('allowed_mentions', discord.AllowedMentions())
    
    @abc.abstractmethod
    def _handle_event(self):
        raise NotImplementedError
    
    @property
    @abc.abstractmethod
    def timeout(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def remove_all_buttons(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_button(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def remove_button(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def add_button(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    async def start(self):
        raise NotImplementedError
    
    @classmethod
    def _get_menu_type(cls, menu_type: int) -> str:
        """Returns the :class:`str` representation of the classes `menu_type`"""
        types = {
            cls.TypeEmbed : 'TypeEmbed',
            cls.TypeEmbedDynamic : 'TypeEmbedDynamic',
            cls.TypeText : 'TypeText'
        }
        return types[menu_type]

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
        """|class method| Remove the limits currently set for reaction menu's"""
        cls._sessions_limited = False
        cls._sessions_limit_details = None
    
    @classmethod
    def get_all_dm_sessions(cls):
        """|class method| Returns all active DM menu sessions
        
        Returns
        -------
        :class:`list`:
            Can return :class:`None` if the there are no active DM sessions
        """
        dm_sessions = [session for session in cls._active_sessions if session.message.guild is None]
        return dm_sessions if dm_sessions else None
    
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
        """|class method| Get a menu instance by it's name
        
        Parameter
        ---------
        name: :class:`str`
            The name of the menu to return
        
        Returns
        -------
        The menu instance. Can return a :class:`list` of menu instances if multiple instances of the menu with the supplied name are running. 
        Can also return :class:`None` if the menu with the supplied name was not found in the list of active sessions
        """
        name = str(name)
        sessions = [session for session in cls._active_sessions if session.name and session.name == name]
        if sessions:
            return sessions[0] if len(sessions) == 1 else sessions
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
    async def stop_all_sessions(cls):
        """|coro class method| Stops all sessions that are currently running

            .. added:: v1.0.9
        """
        while cls._active_sessions:
            session = cls._active_sessions[0]
            await session.stop()
    
    @property
    def owner(self) -> Union[discord.Member, discord.User]:
        """
        Returns
        -------
        Union[:class:`discord.Member`, :class:`discord.User`]:
            The owner of the menu (the person that started the menu). If the menu was started in a DM, this will return `discord.User`
        """
        return self._ctx.author
    
    @property
    def total_pages(self) -> int:
        """
        Returns
        -------
        :class:`int`
            The amount of pages that have been added to the menu. If the `menu_type` is `TypeEmbedDynamic`, the amount of pages is not known until
            after the menu has started and will return a value of 0
        """
        if self._menu_type == BaseMenu.TypeEmbedDynamic:
            if self._is_running:
                return len(self._pages)
            else:
                return 0
        else:
            return len(self._pages)

    @property
    def message(self) -> discord.Message:
        """
        Returns
        -------
        :class:`discord.Message`:
            The menu's message object. Can be :class:`None` if the menu has not been started
        """
        return self._msg
    
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
    def buttons(self):
        return self._buttons if self._buttons else None
    
    @property
    def buttons_most_clicked(self):
        if self._buttons:
            return sorted(self._buttons, key=lambda btn: btn.total_clicks, reverse=True)
        else:
            return None
    
    @property
    def in_dms(self) -> bool:
        """
        Returns
        -------
        :class:`bool`:
            If the menu was started in a DM
        """
        return self._ctx.guild is None
    
    def _chunks(self, list_, n):
        """Yield successive n-sized chunks from list. Core component of a dynamic menu"""
        for i in range(0, len(list_), n):
            yield list_[i:i + n]
    
    def _update_button_statistics(self, button: Button, member: discord.Member):
        """Update the statistical attributes associated with the button

            .. added:: v2.0.3
        """
        button._Button_clicked_by.add(member)
        button._Button_total_clicks += 1
        button._Button_last_clicked = datetime.utcnow()
    
    async def _handle_session_limits(self) -> bool:
        """|coro| Determine if the menu session is currently limited, if so, send the error message and return `False` indicating that further code execution (starting the menu) should be cancelled
        
            .. added:: v2.0.0

            .. note:: use to be :meth:`_is_currently_limited`
        """
        cls = self.__class__
        details: 'NamedTuple' = cls._sessions_limit_details
        can_proceed = True
        
        # if the menu is in a DM, handle it separately
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
    
    def _maybe_new_style(self, counter, total_pages) -> str: 
        """Sets custom page director styles"""
        if self.style:
            if self.style.count('$') == 1 and self.style.count('&') == 1:
                temp = self.style # copy it to a new variable so its not being changed in every call
                temp = temp.replace('$', str(counter))
                temp = temp.replace('&', str(total_pages))
                return temp
            else:
                raise ImproperStyleFormat
        else:
            return f'Page {counter}/{total_pages}'
    
    async def _contact_relay(self, member: discord.Member, button: Union[Button, ViewButton]):
        """Dispatch the information to the relay function if a relay has been set"""
        if self._relay_info:
            func: object = self._relay_info.func
            only = self._relay_info.only
            RelayPayload = collections.namedtuple('RelayPayload', ['member', 'button'])
            payload = RelayPayload(member=member, button=button)

            # before the information is relayed, ensure the relay function contains a single positional argument
            spec = inspect.getfullargspec(func)
            if all([
                len(spec.args) == 1,
                not spec.varargs,
                not spec.varkw,
                not spec.defaults,
                not spec.kwonlyargs,
                not spec.kwonlydefaults
            ]):
                async def call():
                    """Dispatch the information to the relay function. If any errors occur during the call, report it to the user"""
                    try:
                        if asyncio.iscoroutinefunction(func):
                            await func(payload)
                        else:
                            func(payload)
                    except Exception as error:
                        error_msg = inspect.cleandoc(
                            f"""When dispatching the information to your relay function ("{func.__name__}"), that function raised an error during it's execution
                            -> {error.__class__.__name__}: {error}
                            """
                        )
                        raise MenuException(error_msg)

                if only:
                    if button in only:
                        await call()
                else:
                    await call()
            else:
                raise MenuException('When setting a relay, the relay function must have exactly one positional argument')
    
    def _handle_send_to(self, send_to):
        """For the `send_to` kwarg in :meth:`Menu.start()`. Determine what channel the menu should start in"""
        # in DMs
        if self._ctx.guild is None:
            return self._ctx
        
        # in guild
        else:
            if send_to is None:
                return self._ctx
            else:
                if not isinstance(send_to, (str, int, discord.TextChannel)):
                    raise IncorrectType(f'Parameter "send_to" expected str, int, or discord.TextChannel, got {send_to.__class__.__name__}')
                else:
                    class_name = self.__class__.__name__
                    # before we continue, check if there are any duplicate named channels/no matching names found if a str was provided
                    if isinstance(send_to, str):
                        matched_channels = [ch for ch in self._ctx.guild.text_channels if ch.name == send_to]
                        if len(matched_channels) == 0:
                            raise MenuException(f'When using parameter "send_to" in {class_name}.start(), there were no channels with the name {send_to!r}')
                        
                        elif len(matched_channels) >= 2:
                            raise MenuException(f'When using parameter "send_to" in {class_name}.start(), there were {len(matched_channels)} channels with the name {send_to!r}. With multiple channels having the same name, the intended channel is unknown')
                    
                    for channel in self._ctx.guild.text_channels:
                        if isinstance(send_to, str):
                            if channel.name == send_to:
                                return channel
                        
                        elif isinstance(send_to, int):
                            if channel.id == send_to:
                                return channel

                        elif isinstance(send_to, discord.TextChannel):
                            if channel == send_to:
                                return channel
                    else:
                        raise MenuException(f'When using parameter "send_to" in {class_name}.start(), the channel {send_to} was not found')

    @ensure_not_primed
    def clear_all_row_data(self):
        """Delete all the data thats been added using :meth:`ViewMenu.add_row()`
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: This method was called but the menus `menu_type` was not `ViewMenu.TypeEmbedDynamic`
        """
        if self._menu_type == ViewMenu.TypeEmbedDynamic:
            self._dynamic_data_builder.clear()
        else:
            raise MenuSettingsMismatch('Cannot use method ViewMenu.clear_all_row_data() when the menu_type is not set as ViewMenu.TypeEmbedDynamic')
    
    @ensure_not_primed
    def add_row(self, data: str):
        """Add text to the embed page by rows of data
        
        Parameters
        ----------
        data: :class:`str`
            The data to add
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: This method was called but the menus `menu_type` was not `ViewMenu.TypeEmbedDynamic`
        - `MissingSetting`: :class:`ViewMenu` kwarg "rows_requested" (int) has not been set
        """
        if self._menu_type == ViewMenu.TypeEmbedDynamic:
            if self.__rows_requested:
                self._dynamic_data_builder.append(str(data))
            else:
                raise MissingSetting(f'ViewMenu kwarg "rows_requested" (int) has not been set')
        else:
            raise MenuSettingsMismatch('add_row can only be used with a menu_type of ViewMenu.TypeEmbedDynamic')
    
    @ensure_not_primed
    def set_main_pages(self, *embeds: discord.Embed):
        """On a menu with a menu_type of `ViewMenu.TypeEmbedDynamic`, set the pages you would like to show first. These embeds will be shown before the embeds that contain your data
        
        Parameter
        ---------
        *embeds: :class:`discord.Embed`
            An argument list of :class:`discord.Embed` objects
        
        Raises
        ------
        - `MenuSettingsMismatch`: Tried to use method on a menu that was not of menu_type `ViewMenu.TypeEmbedDynamic`
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `ViewMenuException`: The "embeds" parameter was empty. At least one value is needed
        - `IncorrectType`: All values in the argument list were not of type :class:`discord.Embed`
        """
        if not embeds: raise ViewMenuException('The argument list when setting main pages was empty')
        if not all([isinstance(e, discord.Embed) for e in embeds]): raise IncorrectType('All values in the argument list when setting main pages were not of type discord.Embed')
        if self._menu_type != ViewMenu.TypeEmbedDynamic: raise MenuSettingsMismatch('Method set_main_pages is only available for menus with menu_type ViewMenu.TypeEmbedDynamic')
        
        # if they've set any values, remove it. Each set should be from the call and should not stack
        self._main_page_contents.clear()
        
        for embed in embeds:
            self._main_page_contents.append(embed)

    @ensure_not_primed
    def set_last_pages(self, *embeds: discord.Embed):
        """On a menu with a menu_type of `ViewMenu.TypeEmbedDynamic`, set the pages you would like to show last. These embeds will be shown after the embeds that contain your data
        
        Parameter
        ---------
        *embeds: :class:`discord.Embed`
            An argument list of :class:`discord.Embed` objects
        
        Raises
        ------
        - `MenuSettingsMismatch`: Tried to use method on a menu that was not of menu_type `ViewMenu.TypeEmbedDynamic`
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `ViewMenuException`: The "embeds" parameter was empty. At least one value is needed
        - `IncorrectType`: All values in the argument list were not of type :class:`discord.Embed`
        """
        if not embeds: raise ViewMenuException('The argument list when setting main pages was empty')
        if not all([isinstance(e, discord.Embed) for e in embeds]): raise IncorrectType('All values in the argument list when setting main pages were not of type discord.Embed')
        if self._menu_type != ViewMenu.TypeEmbedDynamic: raise MenuSettingsMismatch('Method set_last_pages is only available for menus with menu_type ViewMenu.TypeEmbedDynamic')
        
        # if they've set any values, remove it. Each set should be from the call and should not stack
        self._last_page_contents.clear()
        
        for embed in embeds:
            self._last_page_contents.append(embed)
    
    @ensure_not_primed
    def add_page(self, page: Union[discord.Embed, str]):
        """Add a page to the menu
        
        Parameters
        ----------
        page: Union[:class:`discord.Embed`, :class:`str`]
            The page to add. Can only be used when the menus `menu_type` is :attr:`TypeEmbed` (adding a :class:`discord.Embed`)
            or :class:`TypeText` (adding a :class:`str`)
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: The page being added does not match the menus `menu_type` 
        """
        cls = self.__class__
        if self._menu_type == cls.TypeEmbed:
            if isinstance(page, discord.Embed):
                self._pages.append(page)
            else:
                raise MenuSettingsMismatch(f'menu_type was set as TypeEmbed but got {page.__class__.__name__} when adding a page')
        
        elif self._menu_type == cls.TypeText:
            self._pages.append(str(page))
        
        else:
            raise MenuSettingsMismatch('add_page method cannot be used with the current menu_type')
    
    @ensure_not_primed
    def remove_all_pages(self):
        """Remove all pages from the menu
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        """
        self._pages.clear()
    
    @ensure_not_primed
    def remove_page(self, page_number: int):
        """Remove a page from the menu
        
        Parameters
        ----------
        page_number: :class:`int`
            The page to remove
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `ViewMenuException`: The page associated with the given page number was not valid
        """
        if self._pages:
            if page_number > 0 and page_number <= len(self._pages):
                page_to_delete = page_number - 1
                del self._pages[page_to_delete]
            else:
                raise ViewMenuException(f'Page number invalid. Must be from 1 - {len(self._pages)}')
    
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

            .. added:: v2.0.0
        """
        if not callable(func): raise ReactionMenuException('Parameter "func" must be callable')
        self._on_timeout_details = func
    
    def remove_on_timeout(self):
        """Remove the timeout call to the function you have set when the menu times out
        
            .. added:: v3.0.0
        """
        self._on_timeout_details = None
    
    def set_relay(self, func: object, *, only: List[Union[Button, ViewButton]]=None):
        """Set a function to be called with a given set of information when a button is pressed on the menu. The information passed is `RelayPayload`, a named tuple.
        The named tuple contains the following attributes:

        - `member`: The :class:`discord.Member` object of the person who pressed the button. Could be :class:`discord.User` if the menu was started in a DM
        - `button`: Depending on the menu instance, the :class:`Button` or :class:`ViewButton` object of the button that was pressed

        Parameters
        ----------
        func: Callable[[:class:`NamedTuple`], :class:`None`]
            The function should only contain a single positional argument. Discord.py command functions (`@bot.command()`) not supported
        
        only: List[Union[:class:`Button`, :class:`ViewButton`]]
            (optional) A list of buttons associated with the current menu instance (defaults to :class:`None`)
        
        Raises
        ------
        - `IncorrectType`: The :param:`func` argument provided was not callable
        """
        if callable(func):
            RelayInfo = collections.namedtuple('RelayInfo', ['func', 'only'])
            self._relay_info = RelayInfo(func=func, only=only)
        else:
            raise IncorrectType('When setting the relay, argument "func" must be callable')
    
    def remove_relay(self):
        """Remove the relay that's been set"""
        self._relay_info = None
    
