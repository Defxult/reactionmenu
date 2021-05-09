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
from typing import Union, List

import discord

from .buttons import Button, ButtonType
from .decorators import ensure_not_primed
from .errors import *

class Menu(metaclass=abc.ABCMeta):
    """Abstract base class for :class:`ReactionMenu` and :class:`TextMenu`
    
        .. added:: v1.0.9
    """
    NORMAL = 'NORMAL'
    FAST = 'FAST'

    EMOJI_BACK_BUTTON = u'\U000025c0'
    EMOJI_NEXT_BUTTON = u'\U000025b6'
    EMOJI_FIRST_PAGE = u'\U000023ea'
    EMOJI_LAST_PAGE = u'\U000023e9'
    EMOJI_GO_TO_PAGE = u'\U0001f522'
    EMOJI_END_SESSION = u'\U0000274c'

    @property
    @abc.abstractmethod
    def total_pages(self):
        raise NotImplementedError
    
    @property
    @abc.abstractmethod
    def navigation_speed(self):
        raise NotImplementedError

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def default_next_button(self) -> Button:
        return self._all_buttons[1]

    @property
    def default_back_button(self) -> Button:
        return self._all_buttons[0]

    @property
    def all_buttons(self) -> List[Button]:
        return self._all_buttons

    @property
    def next_buttons(self) -> List[Button]:
        return [button for button in self._all_buttons if button.linked_to is ButtonType.NEXT_PAGE]

    @property
    def back_buttons(self) -> List[Button]:
        return [button for button in self._all_buttons if button.linked_to is ButtonType.PREVIOUS_PAGE]

    @property
    def first_page_buttons(self) -> List[Button]:
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.GO_TO_FIRST_PAGE]
        return temp if temp else None

    @property
    def last_page_buttons(self) -> List[Button]:
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.GO_TO_LAST_PAGE]
        return temp if temp else None

    @property
    def caller_buttons(self) -> List[Button]:
        """ .. added:: v1.0.3"""
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.CALLER]
        return temp if temp else None

    @property
    def end_session_buttons(self) -> List[Button]:
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.END_SESSION]
        return temp if temp else None

    @property
    def go_to_page_buttons(self) -> List[Button]:
        """.. added:: v1.0.1"""
        temp = [button for button in self._all_buttons if button.linked_to is ButtonType.GO_TO_PAGE]
        return temp if temp else None

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
        >>> On 1 out of 5
        ```
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
        """
        if isinstance(value, bool):
            self._clear_reactions_after = value
        else:
            raise TypeError(f'"clear_reactions_after" expected bool, got {value.__class__.__name__}')

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
        """
        if isinstance(value, (int, float, type(None))):
            self._timeout = value
        else:
            raise TypeError(f'"timeout" expected float, int, or None, got {value.__class__.__name__}')

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
        """
        if isinstance(value, bool):
            self._show_page_director = value
        else:
            raise TypeError(f'"show_page_director" expected bool, got {value.__class__.__name__}')

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
            .. added:: v1.0.2
        """
        if isinstance(value, bool):
            self._delete_interactions = value
        else:
            raise TypeError(f'"delete_interactions" expected bool, got {value.__class__.__name__}')

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
        """
        if isinstance(value, bool):
            self._all_can_react = value
        else:
            raise TypeError(f'"all_can_react" expected bool, got {value.__class__.__name__}')

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
            .. added:: v1.0.8
        """
        if isinstance(value, bool):
            self._delete_on_timeout = value
        else:
            raise TypeError(f'"delete_on_timeout" expected bool, got {value.__class__.__name__}')

    @classmethod
    def _remove_session(cls, menu):
        """|class method| Upon session completion, remove it from the list of active sessions
        
            .. added:: v1.0.1
        """
        if menu in cls._active_sessions:
            cls._active_sessions.remove(menu)
    
    @classmethod
    def _is_currently_limited(cls) -> bool:
        """|class method| Check if there is a limit on reaction menus
        
            .. added:: v1.0.1
        """
        if cls._sessions_limit:
            if len(cls._active_sessions) < cls._sessions_limit:
                return False
            else:
                return True
        else:
            return False

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
    def set_sessions_limit(cls, limit: int, message: str='Too many active reaction menus. Wait for other menus to be finished.'):
        """|class method| Sets the amount of menu sessions that can be concurrently active. Should be set before any menus are started and cannot be called more than once
            
            .. added:: v1.0.1

        Parameters
        ----------
        limit: :class:`int`
            The amount of menu sessions allowed
        
        message: :class:`str`
            (optional) Message that will be sent informing users about the menu limit when the limit is reached. Can be :class:`None` for no message

        Example
        -------
        ```
        class Example(commands.Cog):
            def __init__(self, bot):
                self.bot = bot
                Menu.set_sessions_limit(3, 'Sessions are limited')
        ```
            
        Raises
        ------
        - `ReactionMenuException`: Attempted to call method when there are menu sessions that are already active or attempted to set a limit of zero
        """
        if len(cls._active_sessions) != 0:
            # because of the created task(s) when making a session, the menu is still running in the background so manually stopping them is required to stop using resources
            cls.cancel_all_sessions() 
            raise ReactionMenuException('Method "set_sessions_limit" cannot be called when any other menus have started')

        if not isinstance(limit, int):
            raise ReactionMenuException(f'Limit type cannot be {limit.__class__.__name__}, int is required')
        else:
            if limit <= 0:
                raise ReactionMenuException('The session limit must be greater than or equal to one')
            cls._sessions_limit = limit
            cls._limit_message = message

    @classmethod
    def cancel_all_sessions(cls):
        """|class method| Immediately cancel all sessions that are currently running from the menu sessions task pool. Using this method does not allow the normal operations of :meth:`Menu.stop()`. This
        stops all session processing with no regard to changing the status of :attr:`Menu.is_running` amongst other things. Should only be used if you have an excess amount of menus running and it has an affect on 
        your bots performance

            .. added:: v1.0.1

            .. changes::
                v1.0.9
                    Clearing of the task pool as well
        """
        for tsk_session in cls._task_sessions_pool:
            tsk_session.cancel()
        cls._active_sessions.clear()
        cls._task_sessions_pool.clear()
    
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

            .. changes::
                v1.0.9
                    Added if check for :var:`values`. if the sequence does not contains items, :exc:`ValueError` is raised on empty sequence
        """
        counter = collections.Counter(self._extract_all_emojis())
        values = counter.values() 
        # if this results to `False`, that means the user probaly used :meth:`clear_all_buttons`, and if thats the case, another error will arise before executing
        if values: 
            if max(values) != 1:
                raise ReactionMenuException('There cannot be duplicate emojis when using Buttons. All emojis must be unique')

    def _duplicate_name_check(self):
        """Since it's possible for the user to change the name of a :class:`Button` after an instance has been created and added to a :class:`Menu` instance. Before the menu starts, make sure there are no duplicates because if there are,
        methods such as :meth:`Menu.get_button_by_name` could return the wrong :class:`Button` object.
        
            .. added:: v1.0.5

            .. changes::
                v1.0.9
                    Added if check for :var:`values`. if the sequence does not contains items, :exc:`ValueError` is raised on empty sequence
        """
        counter = collections.Counter([btn.name.lower() for btn in self._all_buttons if btn.name is not None])
        values = counter.values()
        if values:
            if max(values) != 1:
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
    
    def _wait_check(self, reaction, user) -> bool:
        """Predicate for :meth:`discord.Client.wait_for`. This also handles :attr:`_all_can_react`"""
        not_bot = False
        correct_msg = False
        correct_user = False

        if not user.bot:
            not_bot = True
        if reaction.message.id == self._msg.id:
            correct_msg = True
        if self._all_can_react:
            self._ctx.author = user
            correct_user = True
        else:
            if self._ctx.author.id == user.id:
                correct_user = True

        return all((not_bot, correct_msg, correct_user))

    def _extract_all_emojis(self) -> List[str]:
        """Returns a list of the emojis that represents the button"""
        return [button.emoji for button in self._all_buttons]

    def _sort_key(self, item: Button):
        """Sort key for :attr:`_all_buttons`"""
        idx = self._emoji_new_order.index(item.emoji)
        return idx
        
    def _determine_location(self, path):
        """Set the text channel where the menu should start
            
            .. added:: v1.0.6
        """
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
            raise TypeError(f'When setting the "send_to" in ReactionMenu.start(), the value must be the name of the channel (str), the channel ID (int), or the channel object (discord.TextChannel), got {path.__class__.__name__}') 

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

    @ensure_not_primed
    def clear_all_buttons(self):
        """Delete all buttons that have been added
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        """
        self._all_buttons.clear()

    @ensure_not_primed
    def remove_button(self, identity: Union[str, Button]):
        """Remove a button by its name or its object

        Parameter
        ---------
        identity: Union[:class:`str`, :class:`Button`]
            Name of the button or the button object itself

        Raises
        ------
        - `ButtonNotFound` - Button with given identity was not found
        """
        if isinstance(identity, str):
            btn_name = identity.lower()
            for btn in self._all_buttons:
                if btn.name == btn_name:
                    self._all_buttons.remove(btn)
                    return
            raise ButtonNotFound(f'Button "{btn_name}" was not found')

        elif isinstance(identity, Button):
            if identity in self._all_buttons:
                self._all_buttons.remove(identity)
            else:
                raise ButtonNotFound(f'Button {identity}, ({repr(identity)}) Could not be found in the list of active buttons')

        else:
            raise TypeError(f'parameter "identity" expected str or Button, got {identity.__class__.__name__}')

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
        emoji_or_button: Union[:class:`str`, :class:`Button`]
            The emoji itself or Button object
        
        Raises
        ------
        - `ImproperButtonOrderChange`: Missing or extra buttons 
        - `MenuAlreadyRunning`: Attempted to call this method after the menu has started
        """
        temp = []
        for item in emoji_or_button:
            if isinstance(item, str):
                if item in self._extract_all_emojis():
                    temp.append(item)
            elif isinstance(item, Button):
                if item.emoji in self._extract_all_emojis():
                    temp.append(item.emoji)
            else:
                raise TypeError('When changing the appear order, parameters must be of type str or Button')
        
        if collections.Counter(temp) == collections.Counter(self._extract_all_emojis()):
            self._emoji_new_order = temp
            self._all_buttons.sort(key=self._sort_key) 
        else:
            def _new_order_extracted():
                """If the item in :param:`emoji_or_button` isinstance of :class:`Button`, convert it to the emoji it represents, then add it to the list"""
                new = []
                for item in emoji_or_button:
                    if isinstance(item, str):
                        new.append(item)
                    elif isinstance(item, Button):
                        new.append(item.emoji)
                return new

            official = set(self._extract_all_emojis())
            new_order = set(_new_order_extracted())
            extra = new_order.difference(official) 
            missing = official.difference(new_order)
            raise ImproperButtonOrderChange(missing, extra)

    @abc.abstractmethod
    async def _execute_navigation_type(self, *args, **kwargs):
        raise NotImplementedError
    
    @abc.abstractmethod
    async def _execute_session(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def add_button(self, button: Button):
        raise NotImplementedError

    @abc.abstractmethod
    async def stop(self, *, delete_menu_message=False, clear_reactions=False):
        raise NotImplementedError

    @abc.abstractmethod
    async def start(self, *, send_to: Union[str, int, discord.TextChannel]=None):
        raise NotImplementedError
    