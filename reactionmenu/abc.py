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

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Final,
    Generic,
    Iterable,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    overload
)

if TYPE_CHECKING:
    from datetime import datetime
    from typing_extensions import Self

import abc
import asyncio
import collections
import inspect
import re
import warnings
from collections.abc import Sequence
from enum import Enum, auto
from typing import NamedTuple, Union

import discord
from discord.ext.commands import Context
from discord.utils import MISSING

from .decorators import ensure_not_primed
from .errors import *

# Constants
_DYNAMIC_EMBED_LIMIT: Final[int] = 4096
_DEFAULT_STYLE: Final[str] = 'Page $/&'
DEFAULT_BUTTONS = None
DEFAULT = MISSING

GB = TypeVar('GB', bound='_BaseButton')
M = TypeVar('M', bound='_BaseMenu')

class Page:
    """Represents a single "page" in the pagination process
    
        .. added:: v3.1.0
    """
    __slots__ = ("content", "embed", "files", "_go_to")
    
    def __init__(self, *, content: Optional[str]=None, embed: Optional[discord.Embed]=MISSING, files: Optional[List[discord.File]]=MISSING) -> None:
        self.content = content
        self.embed = embed
        self.files = files
        self._go_to: Optional[int] = None
    
    def __repr__(self) -> str:
        return f"<Page {' '.join([f'{attr_name}={getattr(self, attr_name)!r}' for attr_name in self.__class__.__slots__ if type(getattr(self, attr_name)) not in (type(None), type(MISSING))])}>"
    
    def _shallow(self) -> Self:
        from copy import copy
        return copy(self)
    
    @staticmethod
    def from_embeds(embeds: Sequence[discord.Embed]) -> List[Page]:
        """|static method|
        
        Converts a sequence of embeds into a list of :class:`Page`
        """
        pages: List[Page] = []
        for e in embeds:
            pages.append(Page(embed=discord.Embed.copy(e)))
        return pages

class PaginationEmojis:
    """A set of basic emojis for your convenience to use for your buttons emoji
    - ◀️ as `BACK_BUTTON`
    - ▶️ as `NEXT_BUTTON`
    - ⏪ as `FIRST_PAGE`
    - ⏩ as `LAST_PAGE`
    - 🔢 as `GO_TO_PAGE`
    - ⏹️ as `END_SESSION`
    """
    BACK_BUTTON: ClassVar[str] = '◀️'
    NEXT_BUTTON: ClassVar[str] = '▶️'
    FIRST_PAGE: ClassVar[str]  = '⏪'
    LAST_PAGE: ClassVar[str]   = '⏩'
    GO_TO_PAGE: ClassVar[str]  = '🔢'
    END_SESSION: ClassVar[str] = '⏹️'

class _PageController:
    def __init__(self, pages: List[Page]) -> None:
        self.ALL_PAGES: Final[List[Page]] = pages
        self.index = 0

    @property
    def current_page(self) -> Page:
        return self.ALL_PAGES[self.index]
    
    @property
    def total_pages(self) -> int:
        """Return the total amount of pages registered to the menu"""
        return len(self.ALL_PAGES) - 1
    
    def validate_index(self) -> Page:
        """If the index is out of bounds, assign the appropriate values so the pagination process can continue and return the associated page"""
        try:
            _ = self.ALL_PAGES[self.index]
        except IndexError:
            if self.index > self.total_pages:
                self.index = 0
            
            elif self.index < 0:
                self.index = self.total_pages
        finally:
            return self.ALL_PAGES[self.index]
    
    def skip_loop(self, action: str, amount: int) -> None:
        """Using `self.index += amount` does not work because this library is used to operating on a +-1 basis. This loop
        provides a simple way to still operate on the +-1 standard.
        """
        while amount != 0:
            if action == '+':
                self.index += 1
            elif action == '-':
                self.index -= 1
            
            self.validate_index()
            amount -= 1
    
    def skip(self, skip: _BaseButton.Skip) -> Page:
        """Return the page that the skip value was set to"""
        self.skip_loop(skip.action, skip.amount)
        return self.validate_index()

    def next(self) -> Page:
        """Return the next page in the pagination process"""
        self.index += 1
        return self.validate_index()
    
    def prev(self) -> Page:
        """Return the previous page in the pagination process"""
        self.index -= 1
        return self.validate_index()
    
    def first_page(self) -> Page:
        """Return the first page in the pagination process"""
        self.index = 0
        return self.ALL_PAGES[self.index]

    def last_page(self) -> Page:
        """Return the last page in the pagination process"""
        self.index = self.total_pages
        return self.ALL_PAGES[self.index]

class _MenuType(Enum):
    TypeEmbed = auto()
    TypeEmbedDynamic = auto()
    TypeText = auto()

MenuType = _MenuType

class _LimitDetails(NamedTuple):
    limit: int
    per: str
    message: str
    set_by_user: bool = False

    @classmethod
    def default(cls) -> Self:
        return cls(0, "", "")

class _BaseButton(Generic[GB], metaclass=abc.ABCMeta):

    Emojis: ClassVar[PaginationEmojis] = PaginationEmojis()

    def __init__(self, name: str, event: Optional[_BaseButton.Event], skip: _BaseButton.Skip):
        self.name: str = name
        self.event: Optional[_BaseButton.Event] = event
        self.skip: _BaseButton.Skip = skip
        self.__clicked_by = set()
        self.__total_clicks = 0
        self.__last_clicked: Optional[datetime] = None
    
    @property
    @abc.abstractmethod
    def menu(self):
        raise NotImplementedError
    
    @property
    def clicked_by(self) -> Set[discord.Member]:
        """
        Returns
        -------
        Set[:class:`discord.Member`]: The members who clicked the button
        """
        return self.__clicked_by
    
    @property
    def total_clicks(self) -> int:
        """
        Returns
        -------
        :class:`int`: The amount of clicks on the button
        """
        return self.__total_clicks

    @property
    def last_clicked(self) -> Optional[datetime]:
        """
        Returns
        -------
        Optional[:class:`datetime.datetime`]: The time in UTC for when the button was last clicked. Can be :class:`None` if the button has not been clicked
        """
        return self.__last_clicked

    def _update_statistics(self, user: Union[discord.Member, discord.User]) -> None:
        self.__clicked_by.add(user)
        self.__total_clicks += 1
        self.__last_clicked = discord.utils.utcnow()

    class Skip:
        """Initialize a skip button with the appropriate values
        
        Parameters
        ----------
        action: :class:`str`
            Whether to go forward in the pagination process ("+") or backwards ("-")
        
        amount: :class:`int`
            The amount of pages to skip. Must be >= 1. If value is <= 0, it is implicitly set to 2
        """
        def __init__(self, action: Literal['+', '-'], amount: int):
            if amount <= 0: amount = 2
            if action in ('+', '-'):
                self.action = action
                self.amount = amount
            else:
                raise MenuException('The action given was not recognized. Expected "+" or "-"')

    class Event:
        """Set a button to be disabled or removed when it has been pressed a certain amount of times. If the button is a :class:`ReactionButton`, only the "remove" event is available
        
        Parameters
        ----------
        event: :class:`str`
            The action to take. Can either be "disable" or "remove"
        
        value: :class:`int`
            The amount set for the specified event. Must be >= 1. If value is <= 0, it is implicitly set to 1"""
        
        _DISABLE = 'disable'
        _REMOVE = 'remove'

        def __init__(self, event_type: Literal['disable', 'remove'], value: int):
            if value <= 0: value = 1
            event_type = str(event_type).lower() # type: ignore
            cls = self.__class__
            
            if event_type in (cls._DISABLE, cls._REMOVE):
                self.event_type = event_type
                self.value = value
            else:
                raise MenuException('The value for parameter "event_type" was not recognized')

class _BaseMenu(metaclass=abc.ABCMeta):
    TypeEmbed: Final[_MenuType] = _MenuType.TypeEmbed
    TypeEmbedDynamic: Final[_MenuType] = _MenuType.TypeEmbedDynamic
    TypeText: Final[_MenuType] = _MenuType.TypeText

    _sessions_limit_details = _LimitDetails.default()
    _active_sessions: List[Self] # initialized in child classes

    def __init__(self, method: Union[Context, discord.Interaction], /, menu_type: _MenuType, **kwargs):
        # `Context` has an `interaction` attribute. If that attribute is `None`,
        # it's not an application command, if so, it's an application command so access
        # and set the interaction attribute so a `ViewMenu` can be used.
        if isinstance(method, Context) and method.interaction is None:
            self._method = method
        elif isinstance(method, Context) and method.interaction is not None:
            self._method = method.interaction
        else:
            self._method = method # will be an interaction

        self._menu_type = menu_type

        self._msg: Union[discord.Message, discord.InteractionMessage] # initialized in child classes
        self._pc:_PageController # initialized in child classes
        self._is_running = False
        self._stop_initiated = False
        self._page_director_separator = ":"

        # dynamic session
        self._main_page_contents = collections.deque()
        self._last_page_contents = collections.deque()
        self._dynamic_data_builder: List[str] = []
        self.wrap_in_codeblock: Optional[str] = kwargs.get('wrap_in_codeblock')
        self.rows_requested: int = kwargs.get('rows_requested', 0)
        self.custom_embed: Optional[discord.Embed] = kwargs.get('custom_embed')

        self._relay_info: Optional[NamedTuple] = None
        self._on_timeout_details: Optional[Callable[[_BaseMenu], None]] = None
        self._menu_timed_out = False
        self._bypass_primed = False # used in :meth:`update()`
        self._pages: List[Page] = []
        self._on_close_event = asyncio.Event() # used for :meth:`wait_until_close()`

        # kwargs
        self.delete_on_timeout: bool = kwargs.get('delete_on_timeout', False)
        self.only_roles: Optional[List[discord.Role]] = kwargs.get('only_roles')
        self.show_page_director: bool = kwargs.get('show_page_director', True)
        self.name: Optional[str] = kwargs.get('name')
        self.style: Optional[str] = kwargs.get('style', _DEFAULT_STYLE)
        self.all_can_click: bool = kwargs.get('all_can_click', False)
        self.delete_interactions: bool = kwargs.get('delete_interactions', True)
        self.allowed_mentions: discord.AllowedMentions = kwargs.get('allowed_mentions', discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True))
    
    @abc.abstractmethod
    def _handle_event(self):
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
    def add_buttons(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def _override_dm_settings(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    async def start(self):
        raise NotImplementedError
    
    # ABC class methods
    
    @abc.abstractmethod
    async def quick_start(cls):
        raise NotImplementedError
    
    @staticmethod
    def separate(values: Sequence[Any]) -> Tuple[List[discord.Embed], List[str]]:
        """|static method|
        
        Sorts all embeds and strings into a single tuple

        Parameters
        ----------
        values: Sequence[`Any`]
            The values to separate
        
        Returns
        -------
        Tuple[List[:class:`discord.Embed`], List[:class:`str`]]
        
        Example
        -------
        >>> embeds, strings = .separate([...])
        """
        all_embeds = list(filter(lambda item: isinstance(item, discord.Embed), values))
        all_strings = list(filter(lambda item: isinstance(item, str), values))
        return (all_embeds, all_strings)
    
    @staticmethod
    def all_embeds(values: Sequence[Any]) -> bool:
        """|static method|
        
        Tests to see if all items in the sequence are of type :class:`discord.Embed`
        
        Parameters
        ----------
        values: Sequence[`Any`]
            The values to test
        
        Returns
        -------
        :class:`bool`: Can return `False` if the sequence is empty
        """
        return all([isinstance(item, discord.Embed) for item in values]) if values else False
    
    @staticmethod
    def _sort_buttons(buttons: List[GB]) -> List[GB]:
        return sorted(buttons, key=lambda btn: btn.total_clicks, reverse=True)
    
    @staticmethod
    def all_strings(values: Sequence[Any]) -> bool:
        """|static method|
        
        Tests to see if all items in the sequence are of type :class:`str`
        
        Parameters
        ----------
        values: Sequence[`Any`]
            The values to test
        
        Returns
        -------
        :class:`bool`: Can return `False` if the sequence is empty
        """
        return all([isinstance(item, str) for item in values]) if values else False
    
    @staticmethod #* Don't make this an instance method. It would be better as one, but it's main intended use is for :meth:`_check` in "views_menu.py"
    def _extract_proper_user(method: Union[Context, discord.Interaction]) -> Union[discord.Member, discord.User]:
        """|static method| Get the proper :class:`discord.User` / :class:`discord.Member` from the attribute depending on the instance

            .. added v3.1.0
        """
        return method.author if isinstance(method, Context) else method.user
    
    @classmethod
    def _quick_check(cls, pages: Sequence[Union[discord.Embed, str]]) -> _MenuType:
        """|class method| Verification for :meth:`quick_start()`
        
            .. added v3.1.0
        """
        if cls.all_embeds(pages):  return cls.TypeEmbed
        if cls.all_strings(pages): return cls.TypeText
        raise IncorrectType(f'All items in the sequence were not of type discord.Embed or str')
    
    @classmethod
    def _all_menu_types(cls) -> Tuple[_MenuType, _MenuType, _MenuType]:
        return (cls.TypeEmbed, cls.TypeEmbedDynamic, cls.TypeText)
    
    @classmethod
    def remove_limit(cls) -> None:
        """|class method|
        
        Remove the limits currently set for menu's
        """
        cls._sessions_limit_details = _LimitDetails.default()
    
    @classmethod
    def get_all_dm_sessions(cls) -> List[Self]:
        """|class method|
        
        Retrieve all active DM menu sessions
        
        Returns
        -------
        A :class:`list` of active DM menu sessions that are currently running. Can be an empty list if there are no active DM sessions
        """
        return [session for session in cls._active_sessions if session._msg.guild is None] # type: ignore
    
    @classmethod
    def get_all_sessions(cls) -> List[Self]:
        """|class method|
        
        Retrieve all active menu sessions
        
        Returns
        -------
        A :class:`list` of menu sessions that are currently running. Can be an empty list if there are no active sessions
        """
        return cls._active_sessions
    
    @classmethod
    def get_session(cls, name: str) -> List[Self]:
        """|class method|
        
        Get a menu instance by it's name
        
        Parameters
        ----------
        name: :class:`str`
            The name of the menu to return
        
        Returns
        -------
        A :class:`list` of menu sessions that are currently running that match the supplied :param:`name`. Can be an empty list if there are no active sessions that matched the :param:`name`
        """
        name = str(name)
        return [session for session in cls._active_sessions if session.name == name]
    
    @classmethod
    def get_sessions_count(cls) -> int:
        """|class method|
        
        Returns the number of active sessions
        
        Returns
        -------
        :class:`int`: The amount of menu sessions that are active
        """
        return len(cls._active_sessions)
    
    @classmethod
    def set_sessions_limit(cls, limit: int, per: Literal['channel', 'guild', 'member']='guild', message: str='Too many active menus. Wait for other menus to be finished.') -> None:
        """|class method|
        
        Sets the amount of menu sessions that can be active at the same time per guild, channel, or member. This applies to both :class:`ReactionMenu` & :class:`ViewMenu`

        Parameters
        ----------
        limit: :class:`int`
            The amount of menu sessions allowed
        
        per: :class:`str`
            How menu sessions should be limited. Options: "channel", "guild", or "member"
        
        message: :class:`str`
            Message that will be sent informing users about the menu limit when the limit is reached. Can be :class:`None` for no message
                    
        Raises
        ------
        - `IncorrectType`: The :param:`limit` parameter was not of type :class:`int`
        - `MenuException`: The value of :param:`per` was not valid or the limit was not greater than or equal to one
        """
        if not isinstance(limit, int):
            raise IncorrectType(f'Parameter "limit" expected int, got {limit.__class__.__name__}')
        else:
            if limit <= 0:
                raise MenuException('The session limit must be greater than or equal to one')
            
            per = str(per).lower() # type: ignore
            if per not in ('guild', 'channel', 'member'):
                raise MenuException('Parameter value of "per" was not recognized. Expected: "channel", "guild", or "member"')

            cls._sessions_limit_details = _LimitDetails(limit, per, message, set_by_user=True)
    
    @classmethod
    async def stop_session(cls, name: str, include_all: bool=False) -> None:
        """|coro class method|
        
        Stop a specific menu with the supplied name
        
        Parameters
        ----------
        name: :class:`str`
            The menus name
        
        include_all: :class:`bool`
            If set to `True`, it stops all menu sessions with the supplied :param:`name`. If `False`, stops only the most recently started menu with the supplied :param:`name`
        
        Raises
        ------
        - `MenuException`: The session with the supplied name was not found
        """
        name = str(name)

        async def determine_include_all(sessions_to_stop: List[Self]) -> None:
            """|coro| Ensures if :param:`include_all` is `True`, all sessions with the specified name will be stopped"""
            if sessions_to_stop:
                if include_all:
                    for session in sessions_to_stop:
                        await session.stop()
                else:
                    await sessions_to_stop[-1].stop()
            else:
                MESSAGE = f'Menu with name {name!r} was not found in the list of active {cls.__name__} sessions'
                raise MenuException(MESSAGE)

        matched_sessions = [session for session in cls._active_sessions if name == session.name]
        await determine_include_all(matched_sessions)
    
    @classmethod
    async def stop_all_sessions(cls) -> None:
        """|coro class method|

        Stops all menu sessions that are currently running
        """
        while cls._active_sessions:
            session = cls._active_sessions[0]
            await session.stop()
    
    @classmethod
    def get_menu_from_message(cls, message_id: int, /) -> Optional[Self]:
        """|class method|

        Return the menu object associated with the message with the given ID

        Parameters
        ----------
        message_id: :class:`int`
            The `discord.Message.id` from the menu message

        Returns
        -------
        The menu object. Can be :class:`None` if the menu was not found in the list of active menu sessions
        """
        for menu in cls._active_sessions:
            if menu._msg.id == message_id: # type: ignore
                return menu
        return None

    @property
    def rows(self) -> Optional[List[str]]:
        """
        Returns
        -------
        Optional[List[:class:`str`]]: All rows that's been added to the menu. Can return `None` if the menu has not started or the `menu_type` is not `TypeEmbedDynamic`
        
            .. added: v3.1.0
        """
        return None if self._is_running is False or self._menu_type != _MenuType.TypeEmbedDynamic else self._dynamic_data_builder.copy()
    
    @property
    def menu_type(self) -> str:
        """
        Returns
        -------
        :class:`str`: The `menu_type` you set via the constructor. This will either be `TypeEmbed`, `TypeEmbedDynamic`, or `TypeText`

            .. added:: v3.1.0
        """
        return self._menu_type.name
    
    @property
    def last_viewed(self) -> Optional[Page]:
        """
        Returns
        -------
        Optional[:class:`Page`]: The last page that was viewed in the pagination process. Can be :class:`None` if the menu has not been started
        """
        return self._pc.current_page._shallow() if self._pc is not None else None
    
    @property
    def owner(self) -> Union[discord.Member, discord.User]:
        """
        Returns
        -------
        Union[:class:`discord.Member`, :class:`discord.User`]: The owner of the menu (the person that started the menu). If the menu was started in a DM, this will return :class:`discord.User`
        """
        return self._extract_proper_user(self._method)
    
    @property
    def total_pages(self) -> int:
        """
        Returns
        -------
        :class:`int`: The amount of pages that have been added to the menu. If the `menu_type` is :attr:`TypeEmbedDynamic`, the amount of pages is not known until AFTER the menu has started. 
        If attempted to retrieve the value before a dynamic menu has started, this will return a value of -1
        """
        if self._menu_type == _BaseMenu.TypeEmbedDynamic:
            return len(self._pages) if self._is_running else -1
        else:
            return len(self._pages)
    
    @property
    def pages(self) -> Optional[List[Page]]:
        """
        Returns
        -------
        Optional[List[:class:`Page`]]: The pages currently applied to the menu. Can return :class:`None` if there are no pages
        
        Note: If the `menu_type` is :attr:`TypeEmbedDynamic`, the pages aren't known until after the menu has started
        """
        return self._pages.copy() if self._pages else None # Return a copy so the core list of pages cannot be manipulated

    @property
    def message(self) -> Optional[Union[discord.Message, discord.InteractionMessage]]:
        """
        Returns
        -------
        Optional[Union[:class:`discord.Message`, :class:`discord.InteractionMessage`]]: The menu's message object. Can be :class:`None` if the menu has not been started
        """
        return self._msg
    
    @property
    def is_running(self) -> bool:
        """
        Returns
        -------
        :class:`bool`: `True` if the menu is currently running, `False` otherwise
        """
        return self._is_running
    
    @property
    def in_dms(self) -> bool:
        """
        Returns
        -------
        :class:`bool`: If the menu was started in a DM
        """
        return self._method.guild is None
    
    def _chunks(self, list_: List[str], n: int) -> Iterable:
        """Yield successive n-sized chunks from list. Core component of a dynamic menu"""
        for i in range(0, len(list_), n):
            yield list_[i:i + n]
    
    async def _build_dynamic_pages(self, send_to, view: Optional[discord.ui.View]=None, payload: Optional[dict]=None) -> None:
        """|coro| Compile all the information that was given via :meth:`add_row`"""
        for data_clump in self._chunks(self._dynamic_data_builder, self.rows_requested):
            joined_data = '\n'.join(data_clump)
            if len(joined_data) <= _DYNAMIC_EMBED_LIMIT:
                possible_block = f"```{self.wrap_in_codeblock}\n{joined_data}```"
                embed = discord.Embed() if self.custom_embed is None else self.custom_embed.copy()
                embed.description = joined_data if not self.wrap_in_codeblock else possible_block
                self._pages.append(Page(embed=embed))
            else:
                raise DescriptionOversized('With the amount of data that was received, the embed description is over discords size limit. Lower the amount of "rows_requested" to solve this problem')
        else:
            def convert_to_page(main_last: Iterable[discord.Embed]) -> List[Page]:
                """Initializing the :class:`deque` only supports :class:`discord.Embed`. This converts those embed objects to the supported :class:`Page` type for proper pagination
                
                    .. added:: v3.1.0
                """
                return [Page(embed=item) for item in main_last]
            
            # set the main/last pages if any
            if any([self._main_page_contents, self._last_page_contents]):
                
                # convert to :class:`deque`
                self._pages = collections.deque(self._pages) # type: ignore (only temporary to use extend methods of :class:`deque`)
                
                if self._main_page_contents:
                    self._main_page_contents.reverse()
                    self._pages.extendleft(convert_to_page(self._main_page_contents)) # type: ignore (converted to deque above)
                
                if self._last_page_contents:
                    self._pages.extend(convert_to_page(self._last_page_contents))
            
            # convert back to `list`
            self._pages = list(self._pages)

            self._refresh_page_director_info(_BaseMenu.TypeEmbedDynamic, self._pages)
            cls = self.__class__

            # make sure data has been added to create at least 1 page
            if not self._pages: raise NoPages(f'You cannot start a {cls.__name__} when no data has been added')
            
            payload['embed'] = self._pages[0].embed # type: ignore / - / reassign the first page to show to director information
            
            if view is None:
                await self._handle_send_to(send_to, payload) # type: ignore
            else:
                await self._handle_send_to(send_to, payload) # type: ignore ("embed=" can still be `None`)
    
    def _display_timeout_warning(self, error: Exception) -> None:
        """Simply displays a warning message to the user notifying them an error has occurred in the function they have set for when the menu times out"""
        warnings.formatwarning = lambda msg, *args, **kwargs: f'{msg}'
        warnings.warn(inspect.cleandoc(
            f"""
            UserWarning: The function you have set in method {self.__class__.__name__}.set_on_timeout() raised an error
            -> {error.__class__.__name__}: {error}
            
            This error has been ignored so the menu timeout process can complete
            """
        ))
    
    async def _handle_on_timeout(self) -> None:
        """|coro| Call the function the user has set for when the menu times out"""
        if self._on_timeout_details and self._menu_timed_out:
            func = self._on_timeout_details
            
            # call the timeout function but ignore any and all exceptions that may occur during the function timeout call.
            # the most important thing here is to ensure the menu is gracefully stopped while displaying a formatted
            # error message to the user
            try:
                if asyncio.iscoroutinefunction(func):
                    await func(self) # type: ignore (`iscoroutinefunction` will still return `False` if func is `None` (i want that to happen))
                else: func(self)
            except Exception as error:
                self._display_timeout_warning(error)
    
    def _determine_kwargs(self, page: Page) -> dict:
        """Determine the `inter.response.edit_message()` and :meth:`_msg.edit()` kwargs for the pagination process. Used in :meth:`ViewMenu._paginate()` and :meth:`ReactionMenu._paginate()`"""
        
        # create a copy of the files if they are set because once paginated, they are only visible once
        maybe_new_files = [discord.File(f.filename) for f in page.files] if page.files else [] # type: ignore
        
        kwargs = {
            "content" : page.content, # `content` will always be present because even with TypeEmbed menu's, pagination with the addition of text is possible
            "allowed_mentions" : self.allowed_mentions,
            "attachments" : maybe_new_files, # the `edit_message` method for this has an "attachment" kwarg instead of a "files" parameter
            "allowed_mentions" : self.allowed_mentions
        }

        # only add the "embed" key if its an embed type menu
        if self._menu_type in (_BaseMenu.TypeEmbed, _BaseMenu.TypeEmbedDynamic):
            kwargs["embed"] = page.embed
        return kwargs
    
    def _refresh_page_director_info(self, type_: _MenuType, pages: List[Page]) -> None:
        """Sets the page count at the bottom of embeds/text if set
        
        Parameters
        ----------
        type_: :class:`_MenuType`
            Either :attr:`_BaseMenu.TypeEmbed`, :attr:`_BaseMenu.TypeEmbedDynamic` or :attr:`_BaseMenu.TypeText`
        
        pages: List[:class:`Page`]
            The pagination contents
        """
        if self.show_page_director:
            if type_ not in (_BaseMenu.TypeEmbed, _BaseMenu.TypeEmbedDynamic, _BaseMenu.TypeText):
                raise Exception('Needs to be of type _BaseMenu.TypeEmbed, _BaseMenu.TypeEmbedDynamic or _BaseMenu.TypeText') 
            
            page_number = 1

            if type_ in (_BaseMenu.TypeEmbed, _BaseMenu.TypeEmbedDynamic):
                page_number = 1
                OUTOF: Final[int] = len(pages)
                all_embeds = [p.embed for p in pages]
                for embed in all_embeds:
                    embed.set_footer(text=f'{self._maybe_new_style(page_number, OUTOF)}{self._page_director_separator if embed.footer.text else ""} {embed.footer.text if embed.footer.text else ""}', icon_url=embed.footer.icon_url) # type: ignore
                    page_number += 1
            else:
                # TypeText Only

                CODEBLOCK = re.compile(r'(`{3})(.*?)(`{3})', flags=re.DOTALL)
                CODEBLOCK_DATA_AFTER = re.compile(r'(`{3})(.*?)(`{3}).+', flags=re.DOTALL)
                for idx in range(len(pages)):
                    page: Page = pages[idx]
                    page_info = self._maybe_new_style(page_number, len(pages))
                    
                    # the main purpose of the re is to decide if only 1 or 2 '\n' should be used. with codeblocks, at the end of the block there is already a new line, so there's no need to add an extra one except in
                    # the case where there is more information after the codeblock
                    
                    # Note: with codeblocks, i already tried the f doc string version of this and it doesnt work because there is a spacing issue with page_info. using a normal f string with \n works as intended
                    # f doc string version: https://github.com/Defxult/reactionmenu/blob/eb88af3a2a6dd468f7bcff38214eb77bc91b241e/reactionmenu/text.py#L288
                    
                    if re.search(CODEBLOCK, page.content): # type: ignore
                        if re.search(CODEBLOCK_DATA_AFTER, page.content): # type: ignore
                            page.content = f'{page.content}\n\n{page_info}'
                        else:
                            page.content = f'{page.content}\n{page_info}'
                    else:
                        page.content = f'{page.content}\n\n{page_info}'
                    page_number += 1
    
    async def _handle_session_limits(self) -> bool:
        """|coro| Determine if the menu session is currently limited, if so, send the error message and return `False` indicating that further code execution (starting the menu) should be cancelled
        
            .. note::
                This method is only called if `_LimitDetails.set_by_user` has been set externally (by the public method)
        """
        cls = self.__class__
        details = cls._sessions_limit_details
        can_proceed = True

        # if the menu is in a DM, handle it separately
        if self.in_dms:
            dm_sessions = cls.get_all_dm_sessions()
            if dm_sessions:
                user_dm_sessions = [session for session in dm_sessions if session.owner.id == self._extract_proper_user(self._method).id]
                if len(user_dm_sessions) >= details.limit:
                    can_proceed = False
        else:
            if details.per == 'guild':
                guild_sessions = [session for session in cls._active_sessions if session.message.guild is not None] # type: ignore
                if len(guild_sessions) >= details.limit:
                    can_proceed = False
            
            elif details.per == 'member':
                member_sessions = [session for session in cls._active_sessions if session.owner.id == self._extract_proper_user(self._method).id]
                if len(member_sessions) >= details.limit:
                    can_proceed = False
            
            elif details.per == 'channel':
                channel_sessions = [session for session in cls._active_sessions if session.message.channel.id == self._method.channel.id] # type: ignore
                if len(channel_sessions) >= details.limit:
                    can_proceed = False
        
        if can_proceed:
            return True
        else:
            await self._method.channel.send(details.message) # type: ignore
            return False
    
    def _maybe_new_style(self, counter: int, total_pages: int) -> str: 
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
    
    async def _contact_relay(self, member: Union[discord.Member, discord.User], button: GB) -> None: # type: ignore
        """|coro| Dispatch the information to the relay function if a relay has been set"""
        if self._relay_info:
            func: Callable = self._relay_info.func # type: ignore
            only = self._relay_info.only # type: ignore
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
                async def call() -> None:
                    """|coro| Dispatch the information to the relay function. If any errors occur during the call, report it to the user"""
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
    
    def _handle_reply_kwargs(self, send_to, reply: bool) -> dict:
        """Used to determine the mentions for the `reply` parameter in :meth:`.start()`"""
        if isinstance(send_to, (discord.TextChannel, discord.VoiceChannel, discord.Thread)) and send_to == self._method.channel:
            send_to = None
        return {
            'reference' : self._method.message if all([send_to is None, reply is True]) else None,
            'mention_author' : self.allowed_mentions.replied_user
        }
    
    async def _handle_send_to(self, send_to: Union[str, int, discord.TextChannel, discord.VoiceChannel, discord.Thread, None], menu_payload: dict) -> None:
        """|coro| For the :param:`send_to` kwarg in :meth:`Menu.start()`. Determine what channel the menu should start in"""
        if isinstance(self._method, Context):

            async def register_message(channel: discord.abc.Messageable) -> None:
                """|coro| Set :attr:`_msg` to the :class:`discord.Message` that the menu is operating from"""
                self._msg = await channel.send(**menu_payload) # type: ignore
            
            if self.in_dms:
                await register_message(self._method.channel)
            else:
                if send_to is None:
                    await register_message(self._method.channel)
                else:
                    if not isinstance(send_to, (str, int, discord.TextChannel, discord.VoiceChannel, discord.Thread)):
                        raise IncorrectType(f'Parameter "send_to" expected str, int, discord.TextChannel, discord.VoiceChannel, or discord.Thread, got {send_to.__class__.__name__}')
                    else:
                        class_name = self.__class__.__name__                    # converted to list because its a sequence proxy
                        all_messageable_channels = self._method.guild.text_channels + list(self._method.guild.threads) + self._method.guild.voice_channels # type: ignore
                        
                        # before we continue, check if there are any duplicate named text channels or threads/no matching names found if a str was provided
                        if isinstance(send_to, str):
                            matched_channels = [ch for ch in all_messageable_channels if ch.name == send_to]
                            if len(matched_channels) == 0:
                                raise MenuException(f'When using parameter "send_to" in {class_name}.start(), there were no channels/threads with the name {send_to!r}')
                            
                            elif len(matched_channels) >= 2:
                                raise MenuException(f'When using parameter "send_to" in {class_name}.start(), there were {len(matched_channels)} channels/threads with the name {send_to!r}. With multiple channels/threads having the same name, the intended channel is unknown')
                        
                        for channel in all_messageable_channels:
                            if isinstance(send_to, str):
                                if channel.name == send_to:
                                    await register_message(channel)
                                    break
                            
                            elif isinstance(send_to, int):
                                if channel.id == send_to:
                                    await register_message(channel)
                                    break
                            
                            # it should be a discord.TextChannel, discord.VoiceChannel, or discord.Thread
                            else:
                                if channel == send_to:
                                    await register_message(channel)
                                    break

                        else:
                            raise MenuException(f'When using parameter "send_to" in {class_name}.start(), the channel {send_to} was not found')
        
        elif isinstance(self._method, discord.Interaction):
            if self._method.response.is_done():
                await self._method.followup.send(**menu_payload)
            else:
                await self._method.response.send_message(**menu_payload)
            self._msg = await self._method.original_response()
        
        else:
            raise IncorrectType('Parameter "method" was not of the correct type')

    def randomize_embed_colors(self) -> None:
        """Randomize the color of all the embeds that have been added to the menu
        
        Raises
        ------
        - `MenuException`: The `menu_type` was not of `TypeEmbed`
        
            .. added:: v3.1.0
        """
        if self._menu_type == _BaseMenu.TypeEmbed:
            for page in self._pages:
                if page.embed:
                    page.embed.color = discord.Color.random()
        else:
            raise MenuException("Randomizing embed colors can only be used when the menu_type is TypeEmbed")
    
    def set_page_director_style(self, style_id: int, separator: str=DEFAULT) -> None:
        """Set how the page numbers dictating what page you are on (in the footer of an embed/regular message) are displayed

        Parameters
        ----------
        style_id: :class:`int`
            Varying formats of how the page director can be presented. The following ID's are available:

            - `1` = Page 1/10
            - `2` = Page 1 out of 10
            - `3` = 1 out of 10
            - `4` = 1 • 10
            - `5` = 1 » 10
            - `6` = 1 | 10
            - `7` = 1 : 10
            - `8` = 1 - 10
            - `9` = 1 / 10
            - `10` = 1 🔹 10
            - `11` = 1 🔸 10
        
        separator: :class:`str`
            The separator between the page director and any text you may have in the embed footer. The default separator is ":". It should be noted that whichever separator you assign,
            if you wish to have spacing between the page director and the separator, you must place the space inside the string yourself as such: " :"
        
        Raises
        ------
        - `MenuException`: The :param:`style_id` value was not valid 
        """
        if separator:
            self._page_director_separator = str(separator)
        
        if style_id == 1:   self.style = _DEFAULT_STYLE
        elif style_id == 2: self.style = 'Page $ out of &'
        elif style_id == 3: self.style = '$ out of &'
        elif style_id == 4: self.style = '$ • &'
        elif style_id == 5: self.style = '$ » &'
        elif style_id == 6: self.style = '$ | &'
        elif style_id == 7: self.style = '$ : &'
        elif style_id == 8: self.style = '$ - &'
        elif style_id == 9: self.style = '$ / &'
        elif style_id == 10: self.style = '$ 🔹 &'
        elif style_id == 11: self.style = '$ 🔸 &'
        else:
            raise MenuException(f'Parameter "style_id" expected a number 1-11, got {style_id!r}')
    
    async def wait_until_closed(self) -> None:
        """|coro|
        
        Waits until the menu session ends using `.stop()` or when the menu times out. This should not be used inside relays
        
            .. added:: v3.0.1
        """
        await self._on_close_event.wait()
    
    @ensure_not_primed
    def add_from_messages(self, messages: Sequence[discord.Message]) -> None:
        """Add pages to the menu using the message object itself
        
        Parameters
        ----------
        messages: Sequence[:class:`discord.Message`]
            A sequence of discord message objects
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: The messages provided did not have the correct values. For example, the `menu_type` was set to `TypeEmbed`, but the messages you've provided only contains text. If the `menu_type` is `TypeEmbed`, only messages with embeds should be provided
        - `IncorrectType`: All messages were not of type :class:`discord.Message`
        """
        if all([isinstance(msg, discord.Message) for msg in messages]):
            if self._menu_type == _BaseMenu.TypeEmbed:
                embeds: List[discord.Embed] = []
                for m in messages:
                    if m.embeds:
                        embeds.extend(m.embeds)
                if embeds:
                    self.add_pages(embeds)
                else:
                    raise MenuSettingsMismatch(f'The menu is set to {self._menu_type.name} but no embeds were found in the messages provided')
            
            elif self._menu_type == _BaseMenu.TypeText:
                content: List[str] = []
                for m in messages:
                    if m.content:
                        content.append(m.content)
                if content:
                    self.add_pages(content)
                else:
                    raise MenuSettingsMismatch(f'The menu is set to {self._menu_type.name} but no text (discord.Message.content) was found in the messages provided')
        else:
            raise IncorrectType('All messages were not of type discord.Message')
    
    @ensure_not_primed
    async def add_from_ids(self, messageable: discord.abc.Messageable, message_ids: Sequence[int]) -> None:
        """|coro|
        
        Add pages to the menu using the IDs of messages. This only grabs embeds (if the `menu_type` is :attr:`TypeEmbed`) or the content (if the `menu_type` is :attr:`TypeText`) from the message
        
        Parameters
        ----------
        messageable: :class:`discord.abc.Messageable`
            A discord :class:`Messageable` object (:class:`discord.TextChannel`, :class:`commands.Context`, etc.)
        
        message_ids: Sequence[:class:`int`]
            The messages to fetch

        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: The message IDs provided did not have the correct values when fetched. For example, the `menu_type` was set to `TypeEmbed`, but the messages you've provided for the library to fetch only contains text. If the `menu_type` is `TypeEmbed`, only messages with embeds should be provided
        - `MenuException`: An error occurred when attempting to fetch a message or not all :param:`message_ids` were of type int
        """
        if all([isinstance(ID, int) for ID in message_ids]):
            to_paginate: List[discord.Message] = []            
            for msg_id in message_ids:
                try:
                    fetched_message = await messageable.fetch_message(msg_id)
                    to_paginate.append(fetched_message)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException) as error:
                    raise MenuException(f'An error occurred when attempting to retrieve message with the ID {msg_id}: {error}')
            
            if self._menu_type == _BaseMenu.TypeEmbed:
                embeds_to_paginate: List[discord.Embed] = []
                for msg in to_paginate:
                    if msg.embeds:
                        embeds_to_paginate.extend(msg.embeds)
                if embeds_to_paginate:
                    for embed in embeds_to_paginate:
                        self.add_page(embed)
                else:
                    raise MenuSettingsMismatch(f'The menu is set to {self._menu_type.name} but no embeds were found in the messages provided')
            
            elif self._menu_type == _BaseMenu.TypeText:
                content_to_paginate: List[str] = []
                for msg in to_paginate:
                    if msg.content:
                        content_to_paginate.append(msg.content)
                if content_to_paginate:
                    for content in content_to_paginate:
                        self.add_page(content=content)
                else:
                    raise MenuSettingsMismatch(f'The menu is set to {self._menu_type.name} but no text (discord.Message.content) was found in the messages provided')
        else:
            raise MenuException('Not all message IDs were of type int')
    
    @ensure_not_primed
    def clear_all_row_data(self) -> None:
        """Delete all the data thats been added using :meth:`add_row()`
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: This method was called but the menus `menu_type` was not :attr:`TypeEmbedDynamic`
        """
        if self._menu_type == _BaseMenu.TypeEmbedDynamic:
            self._dynamic_data_builder.clear()
        else:
            raise MenuSettingsMismatch('Cannot clear all row data when the menu_type is not set as TypeEmbedDynamic')
    
    @ensure_not_primed
    def add_row(self, data: str) -> None:
        """Add text to the embed page by rows of data
        
        Parameters
        ----------
        data: :class:`str`
            The data to add
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: This method was called but the menus `menu_type` was not :attr:`TypeEmbedDynamic`
        - `MissingSetting`: The kwarg "rows_requested" (int) has not been set for the menu
        """
        if self._menu_type == _BaseMenu.TypeEmbedDynamic:
            if self.rows_requested:
                self._dynamic_data_builder.append(str(data))
            else:
                raise MissingSetting('The kwarg "rows_requested" (int) has not been set for the menu')
        else:
            raise MenuSettingsMismatch('add_row() can only be used with a menu_type of TypeEmbedDynamic')
    
    @ensure_not_primed
    def set_main_pages(self, *embeds: discord.Embed) -> None:
        """On a menu with a `menu_type` of :attr:`TypeEmbedDynamic`, set the pages you would like to show first. These embeds will be shown before the embeds that contain your data
        
        Parameters
        ----------
        *embeds: :class:`discord.Embed`
            An argument list of :class:`discord.Embed` objects
        
        Raises
        ------
        - `MenuSettingsMismatch`: Tried to use method on a menu that was not of `menu_type` :attr:`TypeEmbedDynamic`
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuException`: The "embeds" parameter was empty. At least one value is needed
        - `IncorrectType`: All values in the argument list were not of type :class:`discord.Embed`
        """
        if not embeds: raise MenuException('The argument list when setting main pages was empty')
        if not all([isinstance(e, discord.Embed) for e in embeds]): raise IncorrectType('All values in the argument list when setting main pages were not of type discord.Embed')
        if self._menu_type != _BaseMenu.TypeEmbedDynamic: raise MenuSettingsMismatch('Method set_main_pages is only available for menus with menu_type TypeEmbedDynamic')
        
        # if they've set any values, remove it. Each set should be from the call and should not stack
        self._main_page_contents.clear()
        
        for embed in embeds:
            self._main_page_contents.append(embed)

    @ensure_not_primed
    def set_last_pages(self, *embeds: discord.Embed) -> None:
        """On a menu with a `menu_type` of :attr:`TypeEmbedDynamic`, set the pages you would like to show last. These embeds will be shown after the embeds that contain your data
        
        Parameters
        ----------
        *embeds: :class:`discord.Embed`
            An argument list of :class:`discord.Embed` objects
        
        Raises
        ------
        - `MenuSettingsMismatch`: Tried to use method on a menu that was not of `menu_type` :attr:`TypeEmbedDynamic`
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuException`: The "embeds" parameter was empty. At least one value is needed
        - `IncorrectType`: All values in the argument list were not of type :class:`discord.Embed`
        """
        if not embeds: raise MenuException('The argument list when setting last pages was empty')
        if not all([isinstance(e, discord.Embed) for e in embeds]): raise IncorrectType('All values in the argument list when setting last pages were not of type discord.Embed')
        if self._menu_type != _BaseMenu.TypeEmbedDynamic: raise MenuSettingsMismatch('Method set_last_pages is only available for menus with menu_type TypeEmbedDynamic')
        
        # if they've set any values, remove it. Each set should be from the call and should not stack
        self._last_page_contents.clear()
        
        for embed in embeds:
            self._last_page_contents.append(embed)
    
    @ensure_not_primed
    def add_page(self, embed: Optional[discord.Embed]=MISSING, content: Optional[str]=None, files: Optional[List[discord.File]]=MISSING) -> None:
        """Add a page to the menu

        Parameters
        ----------
        embed: Optional[:class:`discord.Embed`]
            The embed of the page
        
        content: Optional[:class:`str`]
            The text that appears above an embed in a message
        
        files: Optional[Sequence[:class:`discord.File`]]
            Files you'd like to attach to the page
        
        Raises
        ------
        - `MenuException`: Attempted to add a page with no parameters
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: The page being added does not match the menus `menu_type` 
        
            .. changes::
                v3.1.0
                    Added parameter content
                    Added parameter embed
                    Added parameter files
                    Removed parameter "page"
        """
        if all([content is None, embed is None, files is None]):
            raise MenuException("When adding a page, at lease one parameter must be set")
        
        cls = self.__class__
        if self._menu_type == cls.TypeEmbed:
            if isinstance(embed, discord.Embed):
                self._pages.append(Page(content=content, embed=embed, files=files))
            else:
                raise MenuSettingsMismatch(f'When adding a page with a menu_type of TypeEmbed, the "embed" parameter cannot be None')
        
        elif self._menu_type == cls.TypeText:
            if content:
                self._pages.append(Page(content=str(content), files=files))
            else:
                raise MenuSettingsMismatch(f'When adding a page with a menu_type of TypeText, the "content" parameter cannot be None')
        
        else:
            raise MenuSettingsMismatch('add_page method cannot be used with the current menu_type')
    
    @overload
    def add_pages(self, pages: Sequence[discord.Embed]) -> None:
        ...
    
    @overload
    def add_pages(self, pages: Sequence[str]) -> None:
        ...

    @ensure_not_primed
    def add_pages(self, pages: Sequence[Union[discord.Embed, str]]) -> None:
        """Add multiple pages to the menu at once
        
        Parameters
        ----------
        pages: Sequence[Union[:class:`discord.Embed`, :class:`str`]]
            The pages to add. Can only be used when the menus `menu_type` is :attr:`TypeEmbed` (adding a :class:`discord.Embed`)
            or :attr:`TypeText` (adding a :class:`str`)
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: The page being added does not match the menus `menu_type` 
        """
        for embed_or_str in pages:
            if isinstance(embed_or_str, str):
                self.add_page(content=embed_or_str)
            else:
                self.add_page(embed_or_str) # type: ignore
    
    @ensure_not_primed
    def remove_all_pages(self) -> None:
        """Remove all pages from the menu
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        """
        self._pages.clear()
    
    @ensure_not_primed
    def remove_page(self, page_number: int) -> None:
        """Remove a page from the menu
        
        Parameters
        ----------
        page_number: :class:`int`
            The page to remove
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `InvalidPage`: The page associated with the given page number was not valid
        """
        if self._pages:
            if page_number > 0 and page_number <= len(self._pages):
                page_to_delete = page_number - 1
                del self._pages[page_to_delete]
            else:
                raise InvalidPage(f'Page number invalid. Must be from 1 - {len(self._pages)}')
    
    def set_on_timeout(self, func: Callable[[M], None]) -> None:
        """Set the function to be called when the menu times out

        Parameters
        ----------
        func: Callable[[:type:`M`]], :class:`None`]
            The function object that will be called when the menu times out. The function should contain a single positional argument
            and should not return anything. The argument passed to that function is an instance of the menu.
        
        Raises
        ------
        - `IncorrectType`: Parameter "func" was not a callable object
        """
        if not callable(func): raise IncorrectType('Parameter "func" must be callable')
        self._on_timeout_details = func # type: ignore
    
    def remove_on_timeout(self) -> None:
        """Remove the timeout call to the function you have set when the menu times out"""
        self._on_timeout_details = None
    
    def set_relay(self, func: Callable[[NamedTuple], None], *, only: Optional[List[GB]]=None) -> None:
        """Set a function to be called with a given set of information when a button is pressed on the menu. The information passed is `RelayPayload`, a named tuple.
        The named tuple contains the following attributes:

        - `member`: The :class:`discord.Member` object of the person who pressed the button. Could be :class:`discord.User` if the menu was started in a DM
        - `button`: Depending on the menu instance, the :class:`ReactionButton` or :class:`ViewButton` object of the button that was pressed

        Parameters
        ----------
        func: Callable[[:class:`NamedTuple`], :class:`None`]
            The function should only contain a single positional argument. Command functions (`@bot.command()`) not supported
        
        only: Optional[List[:generic:`GB`]]
            A list of buttons (`GB`) associated with the current menu instance. If the menu instance is :class:`ReactionMenu`, this should be a list of :class:`ReactionButton`
            and vice-versa for :class:`ViewMenu` instances. If this is :class:`None`, all buttons on the menu will be relayed. If set, only button presses from those specified buttons will be relayed
        
        Raises
        ------
        - `IncorrectType`: The :param:`func` argument provided was not callable
        """
        if callable(func):
            RelayInfo = collections.namedtuple('RelayInfo', ['func', 'only'])
            self._relay_info = RelayInfo(func=func, only=only)
        else:
            raise IncorrectType('When setting the relay, argument "func" must be callable')
    
    def remove_relay(self) -> None:
        """Remove the relay that's been set"""
        self._relay_info = None
