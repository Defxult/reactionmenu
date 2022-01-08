"""
MIT License

Copyright (c) 2021-present Defxult#8269

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
    Final,
    Generic,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union
)

if TYPE_CHECKING:
    from .buttons import ReactionButton, ViewButton
    from . import ReactionMenu, ViewMenu
    M = TypeVar('M', bound=Union[ReactionMenu, ViewMenu])

import abc
import asyncio
import collections
import inspect
import re
import warnings
from collections.abc import Sequence
from datetime import datetime

import discord
from discord.ext.commands import Context

from .decorators import ensure_not_primed
from .errors import *

_DYNAMIC_EMBED_LIMIT = 4096
_DEFAULT_STYLE = 'Page $/&'
GB = TypeVar('GB')


class _PageController:
    """A helper class to control the pagination process"""

    def __init__(self, pages: List[Union[discord.Embed, str]]):
        self.pages = pages
        self.index = 0

    @property
    def current_page(self) -> Union[discord.Embed, str]:
        """Return the current page in the pagination process"""
        return self.pages[self.index]
    
    @property
    def total_pages(self) -> int:
        """Return the total amount of pages registered to the menu"""
        return len(self.pages) - 1
    
    def skip_loop(self, action: str, amount: int) -> None:
        """Using `self.index += amount` does not work because this library is used to operating on a +-1 basis. This loop
        provides a simple way to still operate on the +-1 standard.
        """
        while (amount != 0):
            if action == '+':
                self.index += 1
            elif action == '-':
                self.index -= 1
            
            self.validate_index()
            amount -= 1
    
    def skip(self, skip: _BaseButton.Skip) -> Union[discord.Embed, str]:
        """Return the page that the skip value was set to"""
        self.skip_loop(skip.action, skip.amount)
        return self.validate_index()
    
    def validate_index(self) -> Union[discord.Embed, str]:
        """If the index is out of bounds, assign the appropriate values so the pagination process can continue and return the associated page"""
        try:
            _ = self.pages[self.index]
        except IndexError:
            if self.index > self.total_pages:
                self.index = 0
            
            elif self.index < 0:
                self.index = self.total_pages
        finally:
            return self.pages[self.index]

    def next(self) -> Union[discord.Embed, str]:
        """Return the next page in the pagination process"""
        self.index += 1
        return self.validate_index()
    
    def prev(self) -> Union[discord.Embed, str]:
        """Return the previous page in the pagination process"""
        self.index -= 1
        return self.validate_index()
    
    def first_page(self) -> Union[discord.Embed, str]:
        """Return the first page in the pagination process"""
        self.index = 0
        return self.pages[self.index]

    def last_page(self) -> Union[discord.Embed, str]:
        """Return the last page in the pagination process"""
        self.index = self.total_pages
        return self.pages[self.index]

class PaginationEmojis:
    """A set of basic emojis for your convenience to use for your buttons emoji
    - ◀️ as `BACK_BUTTON`
    - ▶️ as `NEXT_BUTTON`
    - ⏪ as `FIRST_PAGE`
    - ⏩ as `LAST_PAGE`
    - 🔢 as `GO_TO_PAGE`
    - ⏹️ as `END_SESSION`
    """
    BACK_BUTTON: Final[str] = 	'◀️'
    NEXT_BUTTON: Final[str] = 	'▶️'
    FIRST_PAGE: Final[str] =  	'⏪'
    LAST_PAGE: Final[str] =   	'⏩'
    GO_TO_PAGE: Final[str] =  	'🔢'
    END_SESSION: Final[str] = 	'⏹️'

class _BaseButton(Generic[GB], metaclass=abc.ABCMeta):

    Emojis: Final[PaginationEmojis] = PaginationEmojis

    def __init__(self, name: str, event: _BaseButton.Event, skip: _BaseButton.Skip):
        self.name: str = name
        self.event: _BaseButton.Event = event
        self.skip: _BaseButton.Skip = skip
        self.__clicked_by = set()
        self.__total_clicks = 0
        self.__last_clicked: datetime = None
    
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
    def last_clicked(self) -> datetime:
        """
        Returns
        -------
        :class:`datetime.datetime`: The time in UTC for when the button was last clicked. Can be :class:`None` if the button has not been clicked
        """
        return self.__last_clicked

    def _update_statistics(self, user: Union[discord.Member, discord.User]) -> None:
        self.__clicked_by.add(user)
        self.__total_clicks += 1
        self.__last_clicked = datetime.utcnow()

    class Skip:
        """Initialize a skip button with the appropriate values
        
        Parameters
        ----------
        action: :class:`str`
            Whether to go forward in the pagination process ("+") or backwards ("-")
        
        amount: :class:`int`
            The amount of pages to skip. Must be >= 1. If value is <= 0, it is implicitly set to 1
        """
        def __init__(self, action: str, amount: int):
            if amount <= 0: amount = 1
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
        
        _disable = 'disable'
        _remove = 'remove'

        def __init__(self, event_type: str, value: int):
            if value <= 0: value = 1
            event_type = str(event_type).lower()
            
            if event_type in ('disable', 'remove'):
                self.event_type = event_type
                self.value = value
            else:
                raise MenuException('The value for parameter "event_type" was not recognized')

class _BaseMenu(metaclass=abc.ABCMeta):
    TypeEmbed: Final[int] = 1
    TypeEmbedDynamic: Final[int] = 2
    TypeText: Final[int] = 3

    _active_sessions = []
    _sessions_limited = False
    _sessions_limit_details = None

    def __init__(self, ctx: Context, menu_type: int, **kwargs):
        self._ctx = ctx
        self._menu_type = menu_type

        self._msg: discord.Message = None
        self._pc: _PageController = None
        self._buttons: List[Union[ReactionButton, ViewButton]] = []
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
        self.style: Union[str, None] = kwargs.get('style', _DEFAULT_STYLE)
        self.all_can_click: bool = kwargs.get('all_can_click', False)
        self.delete_interactions: bool = kwargs.get('delete_interactions', True)

        #+ NOTE - I might have to remove this because d.py 2.0 for whatever reason doesn't have a `allowed_mentions` kwarg for :meth:`inter.response.edit_message()`
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
    def stop(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    async def start(self):
        raise NotImplementedError
    
    @staticmethod
    def separate(values: Sequence[Any]) -> Tuple[List[discord.Embed], List[str]]:
        """|static method|
        
        Sorts all embeds and strings into a single tuple

        Parameters
        ----------
        values: Sequence[:class:`Any`]
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
        values: Sequence[:class:`Any`]
            The values to test
        
        Returns
        -------
        :class:`bool`: Can return `False` if the sequence is empty
        """
        return all([isinstance(item, discord.Embed) for item in values]) if values else False
    
    @staticmethod
    def all_strings(values: Sequence[Any]) -> bool:
        """|static method|
        
        Tests to see if all items in the sequence are of type :class:`str`
        
        Parameters
        ----------
        values: Sequence[:class:`Any`]
            The values to test
        
        Returns
        -------
        :class:`bool`: Can return `False` if the sequence is empty
        """
        return all([isinstance(item, str) for item in values]) if values else False
    
    @classmethod
    def _all_menu_types(cls) -> Tuple[int, int, int]:
        return (cls.TypeEmbed, cls.TypeEmbedDynamic, cls.TypeText)
    
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
    def get_menu_from_message(cls: Type[M], message_id: int, /) -> M:
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
            if menu._msg.id == message_id:
                return menu
        return None
    
    @classmethod
    def remove_limit(cls) -> None:
        """|class method|
        
        Remove the limits currently set for menu's
        """
        cls._sessions_limited = False
        cls._sessions_limit_details = None
    
    @classmethod
    def get_all_dm_sessions(cls: Type[M]) -> List[M]:
        """|class method|
        
        Retrieve all active DM menu sessions
        
        Returns
        -------
        A :class:`list` of ALL active DM menu sessions (both :class:`ReactionMenu` & :class:`ViewMenu`) that are currently running. Can be an empty list if there are no active DM sessions
        """
        return [session for session in cls._active_sessions if session.message.guild is None]
    
    @classmethod
    def get_all_sessions(cls) -> List[M]:
        """|class method|
        
        Retrieve all active menu sessions
        
        Returns
        -------
        A :class:`list` of ALL menu sessions (both :class:`ReactionMenu` & :class:`ViewMenu`) that are currently running. Can be an empty list if there are no active sessions
        """
        return cls._active_sessions
    
    @classmethod
    def get_session(cls, name: str) -> List[M]:
        """|class method|
        
        Get a menu instance by it's name
        
        Parameters
        ----------
        name: :class:`str`
            The name of the menu to return
        
        Returns
        -------
        A :class:`list` of ALL menu sessions (both :class:`ReactionMenu` & :class:`ViewMenu`) that are currently running that match the supplied name. Can be an empty list if there are no active sessions that matched the name
        """
        name = str(name)
        return [session for session in cls._active_sessions if session.name == name]
    
    @classmethod
    def split_sessions(cls) -> Tuple[List[ReactionMenu], List[ViewMenu]]:
        """|class method|
        
        Separate ALL menu sessions (both :class:`ReactionMenu` & :class:`ViewMenu`) into two different lists accessible from a single :class:`tuple`

        Returns
        -------
        Tuple[List[:class:`ReactionMenu`], List[:class:`ViewMenu`]]: Can be a :class:`tuple` with two empty lists if there are no active sessions

        Example
        -------
        >>> reaction_menus, view_menus = .split_sessions()
        """
        rm = []
        vm = []
        for session in cls._active_sessions:
            if session.__class__.__name__ == 'ReactionMenu': rm.append(session)
            elif  session.__class__.__name__ == 'ViewMenu':  vm.append(session)
        return (rm, vm)
    
    @classmethod
    def get_sessions_count(cls) -> int:
        """|class method|
        
        Returns the number of active sessions
        
        Returns
        -------
        :class:`int`: The amount of ALL menu sessions (both :class:`ReactionMenu` & :class:`ViewMenu`) that are active
        """
        return len(cls._active_sessions)
    
    @classmethod
    def set_sessions_limit(cls, limit: int, per: str='guild', message: str='Too many active menus. Wait for other menus to be finished.') -> None:
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
            
            per = str(per).lower()
            if per not in ('guild', 'channel', 'member'):
                raise MenuException('Parameter value of "per" was not recognized. Expected: "channel", "guild", or "member"')

            LimitDetails = collections.namedtuple('LimitDetails', ['limit', 'per', 'message'])
            cls._sessions_limit_details = LimitDetails(limit=limit, per=per, message=message)
            cls._sessions_limited = True
    
    @classmethod
    async def stop_session(cls, name: str, include_all: bool=False) -> None:
        """|coro class method|
        
        Stop a specific menu with the supplied name
        
        Parameters
        ----------
        name: :class:`str`
            The menus name
        
        include_all: :class:`bool`
            If set to `True`, it stops all menu sessions (both :class:`ReactionMenu` & :class:`ViewMenu`) with the supplied name. If `False`, stops only the most recently started menu with the supplied name
        
        Raises
        ------
        - `MenuException`: The session with the supplied name was not found
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
            raise MenuException(f'Menu with name {name!r} was not found in the list of active menu sessions')

    @classmethod
    async def stop_only(cls, session_type: str) -> None:
        """|coro class method|

        Stops all :class:`ReactionMenu`'s or :class:`ViewMenu`'s that are currently running

        Parameters
        ----------
        session_type: :class:`str`
            Can be "reaction" to stop all :class:`ReactionMenu`'s or "view" to stop all :class:`ViewMenu`'s
        
        Raises
        ------
        - `MenuException`: The parameter given was not recognized
        """
        session_type = session_type.lower()
        if session_type in ('reaction', 'view'):
            rms, vms = cls.split_sessions()
            if session_type == 'reaction':
                for rm in rms:
                    await rm.stop()
            else:
                for vm in vms:
                    await vm.stop() 
        else:
            raise MenuException(f'Parameter "session_type" not recognized. Expected "reaction" or "view", got {session_type!r}')
    
    @classmethod
    async def stop_all_sessions(cls) -> None:
        """|coro class method|
        
        Stops ALL menu sessions (both :class:`ReactionMenu` & :class:`ViewMenu`) that are currently running
        """
        while cls._active_sessions:
            session = cls._active_sessions[0]
            await session.stop()
    
    @property
    def last_viewed(self) -> Union[discord.Embed, str]:
        """
        Returns
        -------
        Union[:class:`discord.Member`, :class:`str`]: The last page that was viewed in the pagination process. Can be :class:`None` if the menu has not been started
        """
        return self._pc.current_page if self._pc is not None else None
    
    @property
    def owner(self) -> Union[discord.Member, discord.User]:
        """
        Returns
        -------
        Union[:class:`discord.Member`, :class:`discord.User`]: The owner of the menu (the person that started the menu). If the menu was started in a DM, this will return :class:`discord.User`
        """
        return self._ctx.author
    
    @property
    def total_pages(self) -> int:
        """
        Returns
        -------
        :class:`int`: The amount of pages that have been added to the menu. If the `menu_type` is :attr:`TypeEmbedDynamic`, the amount of pages is not known until after the menu has started and will return a value of 0
        """
        if self._menu_type == _BaseMenu.TypeEmbedDynamic:
            return len(self._pages) if self._is_running else 0
        else:
            return len(self._pages)
    
    @property
    def pages(self) -> List[Union[discord.Embed, str]]:
        """
        Returns
        -------
        List[Union[:class:`discord.Embed`, :class:`str`]]: The pages currently applied to the menu. Depending on the `menu_type`, it will return a list of :class:`discord.Embed` if the menu type is :attr:`TypeEmbed`
        or :attr:`TypeEmbedDynamic`. If :attr:`TypeText`, it will return a list of :class:`str`. Can return :class:`None` if there are no pages
        
        Note: If the `menu_type` is :attr:`TypeEmbedDynamic`, the pages aren't known until after the menu has started
        """
        return self._pages if self._pages else None

    @property
    def message(self) -> discord.Message:
        """
        Returns
        -------
        :class:`discord.Message`: The menu's message object. Can be :class:`None` if the menu has not been started
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
    def buttons(self: GB) -> List[GB]:
        """
        Returns
        -------
        :class:`list`: A list of all the buttons that have been added to the menu
        """
        return self._buttons
    
    @property
    def buttons_most_clicked(self: GB) -> List[GB]:
        """
        Returns
        -------
        :class:`list`: The list of buttons on the menu ordered from highest (button with the most clicks) to lowest (button with the least clicks). Can be an empty list if there are no buttons registered to the menu
        """
        return sorted(self._buttons, key=lambda btn: btn.total_clicks, reverse=True)
    
    @property
    def in_dms(self) -> bool:
        """
        Returns
        -------
        :class:`bool`: If the menu was started in a DM
        """
        return self._ctx.guild is None
    
    def _chunks(self, list_, n) -> None:
        """Yield successive n-sized chunks from list. Core component of a dynamic menu"""
        for i in range(0, len(list_), n):
            yield list_[i:i + n]
    
    async def _build_dynamic_pages(self, send_to) -> None:
        for data_clump in self._chunks(self._dynamic_data_builder, self.rows_requested):
            joined_data = '\n'.join(data_clump)
            if len(joined_data) <= _DYNAMIC_EMBED_LIMIT:
                possible_block = f"```{self.wrap_in_codeblock}\n{joined_data}```"
                embed = discord.Embed() if self.custom_embed is None else self.custom_embed.copy()
                embed.description = joined_data if not self.wrap_in_codeblock else possible_block
                self._pages.append(embed)
            else:
                raise DescriptionOversized('With the amount of data that was received, the embed description is over discords size limit. Lower the amount of "rows_requested" to solve this problem')
        else:
            # set the main/last pages if any
            if any([self._main_page_contents, self._last_page_contents]):
                
                # convert to deque
                self._pages = collections.deque(self._pages)
                
                if self._main_page_contents:
                    self._main_page_contents.reverse()
                    self._pages.extendleft(self._main_page_contents)
                
                if self._last_page_contents:
                    self._pages.extend(self._last_page_contents)
            
            self._refresh_page_director_info(_BaseMenu.TypeEmbedDynamic, self._pages)
            cls = self.__class__

            # make sure data has been added to create at least 1 page
            if not self._pages: raise NoPages(f'You cannot start a {cls.__name__} when no data has been added')
            
            if cls.__name__ == 'ViewMenu':
                self._msg = await self._handle_send_to(send_to).send(embed=self._pages[0], view=self._view)
            else:
                self._msg = await self._handle_send_to(send_to).send(embed=self._pages[0])
    
    def _display_timeout_warning(self, error: Exception) -> None:
        warnings.formatwarning = lambda msg, *args, **kwargs: f'{msg}'
        warnings.warn(inspect.cleandoc(
            f"""
            UserWarning: The function you have set in method {self.__class__.__name__}.set_on_timeout() raised an error
            -> {error.__class__.__name__}: {error}
            
            This error has been ignored so the menu timeout process can complete
            """
        ))
    
    async def _handle_on_timeout(self) -> None:
        if self._on_timeout_details and self._menu_timed_out:
            func = self._on_timeout_details
            
            # call the timeout function but ignore any and all exceptions that may occur during the function timeout call.
            # the most important thing here is to ensure the menu is gracefully stopped while displaying a formatted
            # error message to the user
            try:
                if asyncio.iscoroutinefunction(func): await func(self)
                else: func(self)
            except Exception as error:
                self._display_timeout_warning(error)
    
    def _determine_kwargs(self, content: Union[discord.Embed, str]) -> dict:
        """Determine the `inter.response.edit_message()` and :meth:`_msg.edit()` kwargs for the pagination process. Used in :meth:`ViewMenu._paginate()` and :meth:`ReactionMenu._paginate()`"""
        kwargs = {
            'embed' if self._menu_type in (_BaseMenu.TypeEmbed, _BaseMenu.TypeEmbedDynamic) else 'content' : content
            # Note to self: Take a look at the note below as to why the following item in this dict is commented out
            #'view' : self._view
        }
        if self.__class__.__name__ != 'ViewMenu' and self._menu_type == _BaseMenu.TypeText:
            kwargs['allowed_mentions'] = self.allowed_mentions
        return kwargs
        """
        Note ::
            I thought everytime a message was edited, the `view` had to be present but that's not the case. Each button stays on the message
            even if the message is edited. The view shouldn't be passed in again because it already exists on the message. This seems to have fixed
            the error:
                    discord.errors.HTTPException: 400 Bad Request (error code: 50035): Invalid Form Body
                    In components.0.components.5: The specified component exceeds the maximum width
            that I was having
        """
    
    def _refresh_page_director_info(self, type_: int, pages: List[Union[discord.Embed, str]]) -> None:
        """Sets the page count at the bottom of embeds/text if set
        
        Parameters
        ----------
        type_: :class:`str`
            Either :attr:`ViewMenu.TypeEmbed`, :attr:`ViewMenu.TypeEmbedDynamic` or :attr:`ViewMenu.TypeText`
        
        pages: List[Union[:class:`discord.Embed`, :class:`str`]]
            The pagination contents
        """
        if self.show_page_director:
            if type_ not in (_BaseMenu.TypeEmbed, _BaseMenu.TypeEmbedDynamic, _BaseMenu.TypeText): raise Exception('Needs to be of type _BaseMenu.TypeEmbed, _BaseMenu.TypeEmbedDynamic or _BaseMenu.TypeText')
            
            if type_ == _BaseMenu.TypeEmbed or type_ == _BaseMenu.TypeEmbedDynamic:
                page = 1
                outof = len(pages)
                for embed in pages:
                    embed.set_footer(text=f'{self._maybe_new_style(page, outof)}{":" if embed.footer.text else ""} {embed.footer.text if embed.footer.text else ""}', icon_url=embed.footer.icon_url)
                    page += 1
            else:
                page_count = 1
                CODEBLOCK = re.compile(r'(`{3})(.*?)(`{3})', flags=re.DOTALL)
                CODEBLOCK_DATA_AFTER = re.compile(r'(`{3})(.*?)(`{3}).+', flags=re.DOTALL)
                for idx in range(len(pages)):
                    content = pages[idx]
                    page_info = self._maybe_new_style(page_count, len(pages))
                    
                    # the main purpose of the re is to decide if only 1 or 2 '\n' should be used. with codeblocks, at the end of the block there is already a new line, so there's no need to add an extra one except in
                    # the case where there is more information after the codeblock
                    
                    # Note: with codeblocks, i already tried the f doc string version of this and it doesnt work because there is a spacing issue with page_info. using a normal f string with \n works as intended
                    # f doc string version: https://github.com/Defxult/reactionmenu/blob/eb88af3a2a6dd468f7bcff38214eb77bc91b241e/reactionmenu/text.py#L288
                    
                    if re.search(CODEBLOCK, content):
                        if re.search(CODEBLOCK_DATA_AFTER, content):
                            pages[idx] = f'{content}\n\n{page_info}'
                        else:
                            pages[idx] = f'{content}\n{page_info}'
                    else:
                        pages[idx] = f'{content}\n\n{page_info}'
                    page_count += 1
    
    async def _handle_session_limits(self) -> bool:
        """|coro| Determine if the menu session is currently limited, if so, send the error message and return `False` indicating that further code execution (starting the menu) should be cancelled"""
        cls = self.__class__
        details: 'NamedTuple' = cls._sessions_limit_details
        can_proceed = True
        
        # if the menu is in a DM, handle it separately
        if self.in_dms:
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
    
    async def _contact_relay(self, member: discord.Member, button: _BaseButton) -> None:
        """|coro| Dispatch the information to the relay function if a relay has been set"""
        if self._relay_info:
            func: Callable = self._relay_info.func
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
    
    def _handle_reply_kwargs(self, send_to, reply: bool) -> dict:
        """Used to determine the mentions for the `reply` parameter in :meth:`.start()`"""
        # sometimes users do `.start(send_to=ctx.channel)`. its not needed but handle it just in case
        if isinstance(send_to, discord.TextChannel) and send_to == self._ctx.channel:
            send_to = None
        return {
            'reference' : self._ctx.message if all([send_to is None, reply is True]) else None,
            'mention_author' : self.allowed_mentions.replied_user
        }
    
    def _handle_send_to(self, send_to) -> discord.abc.Messageable:
        """For the :param:`send_to` kwarg in :meth:`Menu.start()`. Determine what channel the menu should start in"""
        if self.in_dms:
            return self._ctx
        else:
            if send_to is None:
                return self._ctx
            else:
                if not isinstance(send_to, (str, int, discord.TextChannel, discord.Thread)):
                    raise IncorrectType(f'Parameter "send_to" expected str, int, discord.TextChannel, or discord.Thread, got {send_to.__class__.__name__}')
                else:
                    class_name = self.__class__.__name__
                    all_messageable_channels: List[Union[discord.TextChannel, discord.Thread]] = self._ctx.guild.text_channels + self._ctx.guild.threads
                    
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
                                return channel
                        
                        elif isinstance(send_to, int):
                            if channel.id == send_to:
                                return channel

                        elif isinstance(send_to, discord.TextChannel):
                            if channel == send_to:
                                return channel
                        
                        elif isinstance(send_to, discord.Thread):
                            if channel == send_to:
                                return channel

                    else:
                        raise MenuException(f'When using parameter "send_to" in {class_name}.start(), the channel {send_to} was not found')

    def set_page_director_style(self, style_id: int) -> None:
        """Set how the page numbers dictating what page you are on (in the footer of an embed/regular message) are displayed

        Parameters
        ----------
        style_id: :class:`int`
            Varying formats of how the page director can be presented. The following ID's are available:

            - `1` = Page 1/10
            - `2` = Page 1 out of 10
            - `3` = 1 • 10
            - `4` = 1 » 10
            - `5` = 1 | 10
            - `6` = 1 : 10
            - `7` = 1 - 10
            - `8` = 1 / 10
        
        Raises
        ------
        - `MenuException`: The :param:`style_id` value was not valid 
        """
        if style_id == 1:   self.style = _DEFAULT_STYLE
        elif style_id == 2: self.style = 'Page $ out of &'
        elif style_id == 3: self.style = '$ • &'
        elif style_id == 4: self.style = '$ » &'
        elif style_id == 5: self.style = '$ | &'
        elif style_id == 6: self.style = '$ : &'
        elif style_id == 7: self.style = '$ - &'
        elif style_id == 8: self.style = '$ / &'
        else:
            raise MenuException(f'Parameter "style_id" expected a number 1-8, got {style_id!r}')
    
    @ensure_not_primed
    async def add_from_messages(self, messages: Sequence[discord.Message]) -> None:
        """|coro|
        
        Add pages to the menu using the message object itself
        
        Parameters
        ----------
        messages: Sequence[:class:`discord.Message`]
            A sequence of discord message objects
        
        Raises
        ------
        - `MenuSettingsMismatch`: The messages provided did not have the correct values. For example, the `menu_type` was set to `TypeEmbed`, but the messages you've provided only contains text. If the `menu_type` is `TypeEmbed`, only messages with embeds should be provided
        - `MenuException`: All messages were not of type :class:`discord.Message`
        """
        if all([isinstance(msg, discord.Message) for msg in messages]):
            if self._menu_type == _BaseMenu.TypeEmbed:
                embeds = []
                for m in messages:
                    if m.embeds:
                        embeds.extend(m.embeds)
                if embeds:
                    self.add_pages(embeds)
                else:
                    raise MenuSettingsMismatch(f'The menu is set to {self._get_menu_type(self._menu_type)} but no embeds were found in the messages provided')
            
            elif self._menu_type == _BaseMenu.TypeText:
                content = []
                for m in messages:
                    if m.content:
                        content.append(m.content)
                if content:
                    self.add_pages(content)
                else:
                    raise MenuSettingsMismatch(f'The menu is set to {self._get_menu_type(self._menu_type)} but no text (discord.Message.content) was found in the messages provided')
        else:
            raise MenuException('All messages were not of type discord.Message')
    
    @ensure_not_primed
    async def add_from_ids(self, messageable: discord.abc.Messageable, message_ids: Sequence[int]) -> None:
        """|coro|
        
        Add pages to the menu using the IDs of messages
        
        Parameters
        ----------
        messageable: :class:`discord.abc.Messageable`
            A discord `Messageable` object (`discord.TextChannel`, `commands.Context`, etc.)
        
        message_ids: Sequence[:class:`int`]
            The messages to fetch

        Raises
        ------
        - `MenuSettingsMismatch`: The message IDs provided did not have the correct values when fetched. For example, the `menu_type` was set to `TypeEmbed`, but the messages you've provided for the library to fetch only contains text. If the `menu_type` is `TypeEmbed`, only messages with embeds should be provided
        - `MenuException`: An error occurred when attempting to fetch a message or not all :param:`message_ids` were of type int
        """
        if all([isinstance(ID, int) for ID in message_ids]):
            to_paginate: List[discord.Message] = []            
            for msg_id in message_ids:
                try:
                    result = await messageable.fetch_message(msg_id)
                    to_paginate.append(result)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException) as error:
                    raise MenuException(f'An error occurred when attempting to retreive message with the ID {msg_id}: {error}')
            
            if self._menu_type == _BaseMenu.TypeEmbed:
                embeds_to_paginate = []
                for msg in to_paginate:
                    if msg.embeds:
                        embeds_to_paginate.extend(msg.embeds)
                if embeds_to_paginate:
                    for embed in embeds_to_paginate:
                        self.add_page(embed)
                else:
                    raise MenuSettingsMismatch(f'The menu is set to {self._get_menu_type(self._menu_type)} but no embeds were found in the messages provided')
            
            elif self._menu_type == _BaseMenu.TypeText:
                content_to_paginate = []
                for msg in to_paginate:
                    if msg.content:
                        content_to_paginate.append(msg.content)
                if content_to_paginate:
                    for content in content_to_paginate:
                        self.add_page(content)
                else:
                    raise MenuSettingsMismatch(f'The menu is set to {self._get_menu_type(self._menu_type)} but no text (discord.Message.content) was found in the messages provided')
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
    def add_page(self, page: Union[discord.Embed, str]) -> None:
        """Add a page to the menu
        
        Parameters
        ----------
        page: Union[:class:`discord.Embed`, :class:`str`]
            The page to add. Can only be used when the menus `menu_type` is :attr:`TypeEmbed` (adding a :class:`discord.Embed`)
            or :attr:`TypeText` (adding a :class:`str`)
        
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
        for page in pages:
            self.add_page(page)
    
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
    
    def set_on_timeout(self, func: Callable[[Any], None]) -> None:
        """Set the function to be called when the menu times out

        Parameters
        ----------
        func: Callable[[Any], :class:`None`]
            The function object that will be called when the menu times out. The function should contain a single positional argument
            and should not return anything. The argument passed to that function is an instance of the menu.
        
        Raises
        ------
        - `MenuException`: Parameter "func" was not a callable object
        """
        if not callable(func): raise MenuException('Parameter "func" must be callable')
        self._on_timeout_details = func
    
    def remove_on_timeout(self) -> None:
        """Remove the timeout call to the function you have set when the menu times out"""
        self._on_timeout_details = None
    
    def set_relay(self, func: Callable[[NamedTuple], None], *, only: Optional[List[Union[ReactionButton, ViewButton]]]=None) -> None:
        """Set a function to be called with a given set of information when a button is pressed on the menu. The information passed is `RelayPayload`, a named tuple.
        The named tuple contains the following attributes:

        - `member`: The :class:`discord.Member` object of the person who pressed the button. Could be :class:`discord.User` if the menu was started in a DM
        - `button`: Depending on the menu instance, the :class:`ReactionButton` or :class:`ViewButton` object of the button that was pressed

        Parameters
        ----------
        func: Callable[[:class:`NamedTuple`], :class:`None`]
            The function should only contain a single positional argument. Command functions (`@bot.command()`) not supported
        
        only: Optional[List[Union[:class:`ReactionButton`, :class:`ViewButton`]]]
            A list of buttons associated with the current menu instance. If this is :class:`None`, all buttons on the menu will be relayed. If
            set, only button presses from those specified buttons will be relayed
        
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
