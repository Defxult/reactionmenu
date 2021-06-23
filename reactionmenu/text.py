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

import asyncio
import collections
import inspect
import itertools
import re
from typing import List, Union

from discord import AllowedMentions, Member, Role, TextChannel
from discord.ext.commands import Context

from . import abc
from .buttons import Button, ButtonType
from .decorators import ensure_not_primed, menu_verification
from .errors import DuplicateButton, IncorrectType, MenuAlreadyRunning, MissingSetting, ReactionMenuException, TooManyButtons


class TextMenu(abc.Menu):
    """A class to create a discord.py text pagination menu using reactions

    Parameters
    ----------
    ctx: :class:`discord.ext.commands.Context`
        The Context object. You can get this using a command or if in `discord.on_message`

    back_button: :class:`str`
        Button used to go to the previous page of the menu

    next_button: :class:`str`
        Button used to go to the next page of the menu

    Options [kwargs]
    ----------------
    clear_reactions_after: :class:`bool`
        If the menu times out, remove all reactions (defaults to `True`)

    timeout: Union[:class:`float`, :class:`None`]
        Timer for when the menu should end. Can be :class:`None` for no timeout (defaults to 60.0)

    show_page_director: :class:`bool`
        Shown at the botttom of each embed page. "Page 1/20" (defaults to `True`)

    name: :class:`str`
        A name you can set for the menu (defaults to :class:`None`)

    style: :class:`str`
        A custom page director style you can select. "$" represents the current page, "&" represents the total amount of pages (defaults to "Page $/&") Example: `TextMenu(ctx, ..., style='On $ out of &')`

    all_can_react: :class:`bool`
        Sets if everyone is allowed to control when pages are 'turned' when buttons are pressed (defaults to `False`)

    delete_interactions: :class:`bool`
        Delete the prompt message by the bot and response message by the user when asked what page they would like to go to when using `ButtonType.GO_TO_PAGE` (defaults to `True`)

    navigation_speed: :class:`str`
        Sets if the user needs to wait for the reaction to be removed by the bot before "turning" the page. Setting the speed to :attr:`TextMenu.FAST` makes it so that there is no need to wait (reactions are not removed on each press) and can
        navigate lengthy menu's more quickly (defaults to `TextMenu.NORMAL`)

    delete_on_timeout: :class:`bool`
        When the menu times out, delete the menu message. This overrides :attr:`clear_reactions_after` (defaults to `False`)
    
    only_roles: List[:class:`discord.Role`]
        Members with any of the provided roles are the only ones allowed to control the menu. The member who started the menu will always be able to control it. This overrides :attr:`all_can_react` (defaults to :class:`None`)
    
    allowed_mentions: :class:`discord.AllowedMentions`
        Controls the mentions being processed in the menu message (defaults to :class:`discord.AllowedMentions(everyone=True, users=True, roles=True, replied_user=True)`)

        .. added:: v1.0.9

        .. changes ::
            v1.1.0
                Added initialization of :attr:`_menu_owner` to the `__init__` instead of the execute session method, etc.
                Added :attr:_on_timeout_details
                Added :attr:_menu_timed_out
    """
    _active_sessions: List['TextMenu'] = []

    def __init__(self, ctx: Context, *, back_button: str, next_button: str, **options):
        self._ctx = ctx
        self._bot = ctx.bot
        self._default_back_button: Button = Button(emoji=back_button, linked_to=ButtonType.PREVIOUS_PAGE, name='default back button')
        self._default_next_button: Button = Button(emoji=next_button, linked_to=ButtonType.NEXT_PAGE, name='default next button')
        self._all_buttons: List[Button] = [self._default_back_button, self._default_next_button]
        self._contents: List[str] = []
        self._loop = ctx.bot.loop
        self._send_to_channel = None
        self._msg = None
        self._is_running = False
        self._page_number = 0
        self._run_time = 0
        self._all_buttons_removed = False
        self._is_dm_session = False
        self._relay_function = None
        self._on_timeout_details: 'function' = None
        self._menu_timed_out = False
        
        # auto-pagination
        self._menu_owner = ctx.author
        self._auto_paginator = False
        self._auto_turn_every = None
        self._auto_worker = None

        # tasks
        self._main_session_task: asyncio.Task = None
        self._runtime_tracking_task: asyncio.Task = None
        self._countdown_task: asyncio.Task = None

        # basic options (also ABC properties)
        self._allowed_mentions = options.get('allowed_mentions', AllowedMentions())
        self._only_roles: List[Role] = options.get('only_roles')
        self._style: str = options.get('style')
        self._clear_reactions_after: bool = options.get('clear_reactions_after', True)
        self._timeout: Union[float, None] = options.get('timeout', 60.0)
        self._show_page_director: bool = options.get('show_page_director', True)
        self._name: str = options.get('name')
        self._all_can_react: bool = options.get('all_can_react', False)
        self._delete_interactions: bool = options.get('delete_interactions', True)
        self._delete_on_timeout: bool = options.get('delete_on_timeout', False)
        self._navigation_speed: str = options.get('navigation_speed', TextMenu.NORMAL)
    
    @property
    def total_pages(self) -> int:
        """
        Returns
        -------
        :class:`int`:
            The amount of pages on the menu

            .. note::
                ABC prop
        """
        return len(self._contents)

    @property
    def contents(self) -> List[str]:
        """
        Returns
        -------
        List[:class:`str`]:
            All the contents of a text menu. Can be :class:`None` if no content has been added
        """
        return self._contents if self._contents else None
    
    @property
    def allowed_mentions(self):
        return self._allowed_mentions
    
    @allowed_mentions.setter
    def allowed_mentions(self, value):
        """A property getter/setter for kwarg "allowed_mentions"

        Example
        -------
        ```
        menu = TextMenu(ctx, ...)
        menu.allowed_mentions = discord.AllowedMentions(roles=False, ...)

        >>> print(menu.allowed_mentions)
        AllowedMentions(roles=False, ...)
        ```

        Returns
        -------
        :class:`discord.AllowedMentions`:
            The values that were set to control the mentions of the text menu message
        """
        if isinstance(value, AllowedMentions):
            self._allowed_mentions = value
        else:
            raise IncorrectType(f'"allowed_mentions" expected discord.AllowedMentions, got {value.__class__.__name__}')

    @ensure_not_primed
    def clear_all_contents(self):
        """Delete everything that has been added to the list of contents
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call this method after the menu has started
        """
        self._contents.clear()
    
    @ensure_not_primed
    def add_content(self, content: str):
        """Add text to the pagination process. This is considered as adding a page. Each call to this method will create a new page of text with the associated content

        Parameter
        ---------
        content: :class:`str`
            The message you'd like to display
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call this method after the menu has started
        """
        self._contents.append(str(content))
    
    @ensure_not_primed
    def add_button(self, button: Button):
        """Adds a button to the menu. Since this is a :class:`TextMenu`, you are limited on what type of buttons you can add. The available :class:`ButtonType` for :class:`TextMenu` are:

        - `ButtonType.PREVIOUS_PAGE`
        - `ButtonType.NEXT_PAGE`
        - `ButtonType.GO_TO_FIRST_PAGE`
        - `ButtonType.GO_TO_LAST_PAGE`
        - `ButtonType.GO_TO_PAGE`
        - `ButtonType.END_SESSION`
        - `ButtonType.CALLER`

        Parameter
        ---------
        button: :class:`Button`
            The button to instantiate.

        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call this method after the menu has started
        - `DuplicateButton`: The emoji used is already registered as a button
        - `TooManyButtons`: More than 20 buttons were added. Discord has a reaction limit of 20
        - `ReactionMenuException`: The :class:`ButtonType` used in the :class:`Button` is not supported for a :class:`TextMenu` or a name used for the :class:`Button` is already registered
        - `MissingSetting`: Set the Button :param:`linked_to` as `ButtonType.CALLER` but did not assign the Button kwarg "details" a value
        
            .. note::
                ABC meth
        """
        if button.emoji not in self._extract_all_emojis():
            
            # if the Button has a name, make sure its not a dupliate name
            if button.name in [btn.name for btn in self._all_buttons if btn.name]:
                raise ReactionMenuException('There cannot be duplicate names when setting the name for a Button')
            
            # verify the :class:`ButtonType` that :class:`TextMenu` supports
            permitted_types = (ButtonType.PREVIOUS_PAGE, ButtonType.NEXT_PAGE, ButtonType.GO_TO_FIRST_PAGE, ButtonType.GO_TO_LAST_PAGE, ButtonType.GO_TO_PAGE, ButtonType.END_SESSION, ButtonType.CALLER)
            if button.linked_to not in permitted_types:
                raise ReactionMenuException(inspect.cleandoc(
                    """
                    ButtonType not valid for TextMenu. The only permitted ButtonTypes are
                    
                    - ButtonType.PREVIOUS_PAGE
                    - ButtonType.NEXT_PAGE
                    - ButtonType.GO_TO_FIRST_PAGE
                    - ButtonType.GO_TO_LAST_PAGE
                    - ButtonType.GO_TO_PAGE
                    - ButtonType.END_SESSION
                    - ButtonType.CALLER
                    """
                ))
            
            if button.linked_to is ButtonType.CALLER and not button.details:
                raise MissingSetting('When adding a button with the type "ButtonType.CALLER", the kwarg "details" for that Button must be set.')

            self._all_buttons.append(button)
            if len(self._all_buttons) > 20:
                raise TooManyButtons

            if self._all_buttons_removed:
                self._all_buttons_removed = False
        else:
            raise DuplicateButton(f'The emoji {tuple(button.emoji)} has already been registered as a button')

    def _page_control(self, action) -> int:
        """When the menu is in an active session, this protects the menu pagination index from going out of bounds (IndexError)"""
        if action == '+':   self._page_number += 1
        if action == '-':   self._page_number -= 1

        if self._page_number > len(self._contents) - 1:
            self._page_number = 0
        elif self._page_number < 0:
            self._page_number = len(self._contents) - 1
        
        return self._page_number
    
    def _mark_pages(self):
        """Add the page director information to the content"""
        if self._show_page_director:
            page_count = 1
            CODEBLOCK = re.compile(r'(`{3})(.*?)(`{3})', flags=re.DOTALL)
            CODEBLOCK_DATA_AFTER = re.compile(r'(`{3})(.*?)(`{3}).+', flags=re.DOTALL)
            for idx in range(len(self._contents)):
                content = self._contents[idx]
                page_info = self._maybe_new_style(page_count, len(self._contents))
                
                # the main purpose of the re is to decide if only 1 or 2 '\n' should be used. with codeblocks, at the end of the block there is already a new line, so there's no need to add an extra one except in
                # the case where there is more information after the codeblock
                
                # NOTE: with codeblocks, i already tried the f doc string version of this and it doesnt work because there is a spacing issue with page_info. using a normal f string with \n works as intended
                # f doc string version: https://github.com/Defxult/reactionmenu/blob/eb88af3a2a6dd468f7bcff38214eb77bc91b241e/reactionmenu/text.py#L288
                
                if re.search(CODEBLOCK, content):
                    if re.search(CODEBLOCK_DATA_AFTER, content):
                        self._contents[idx] = f'{content}\n\n{page_info}'
                    else:
                        self._contents[idx] = f'{content}\n{page_info}'
                else:
                    self._contents[idx] = f'{content}\n\n{page_info}'
                page_count += 1
    
    async def _execute_navigation_type(self, worker, emoji, **kwargs):
        """|abc coro| This controls whether the user has to wait until the emoji is removed from the message by the :class:`discord.Client` in order to continue 'turning' pages in the menu session. 
        :attr:`TextMenu.NORMAL` indicates the user has to wait for the :class:`discord.Client` to remove the reaction. :attr:`TextMenu.FAST` indicates no wait is needed and is 
        processed on each `reaction_add` and `reaction_remove`. In v1.0.0 - v1.0.4, the handling of each button press was processed in :meth:`TextMenu._execute_session`. This replaces that
        so each button press is also handled through here now as :attr:`TextMenu.NORMAL`, as well as the handling of :attr:`TextMenu.FAST`

        Kwargs
        ------
        - from_caller_button: :class:`bool` Handles the editing process with interactions from :attr:`ButtonType.CALLER`
            
            .. added:: v1.0.5
        """
        from_caller_button = kwargs.get('from_caller_button', False)

        # NOTE: :param:`worker` is the current contents for the associated page
        if self._navigation_speed == TextMenu.NORMAL:
            if from_caller_button:
                await self._msg.remove_reaction(emoji, self._ctx.author)
            else:
                await self._msg.edit(content=worker, allowed_mentions=self._allowed_mentions)
                await self._msg.remove_reaction(emoji, self._ctx.author)
        
        elif self._navigation_speed == TextMenu.FAST:
            # return if from_caller_button. This is needed because if calling from a ButtonType.CALLER, :param:`worker` is :class:`None` (as a placeholder)
            # and you cannot edit a discord message with a content type of :class:`None`
            if from_caller_button:
                return
            await self._msg.edit(content=worker, allowed_mentions=self._allowed_mentions)

    def refresh_auto_pagination_data(self, *contents: str):
        """Update the contents displayed in the auto-pagination menu. When refreshed, the new contents don't go into effect until the last round of waiting (what you set for `turn_every`) completes

        Parameters
        ----------
        *contents: :class:`str`
            An argument list of :class:`str` values

            .. note::
                ABC meth
        
        Raises
        ------
        - `ReactionMenuException`: The menu was not set as an auto-paginator menu
        - `IncorrectType`: All values in the argument list were not of type :class:`str`
        """
        if self._auto_paginator:
            if all([isinstance(item, str) for item in contents]):
                self._auto_worker = itertools.cycle(contents)
            else:
                raise IncorrectType('Parameter "contents" expected only str values. One or more values were not of type str')
        else:
            raise ReactionMenuException('Menu is not set as auto-paginator')
    
    async def _execute_auto_session(self):
        """|abc coro| Begin the auto-pagination process"""
        self._auto_worker = itertools.cycle(self._contents)
        next(self._auto_worker)
        self._all_buttons.clear()
        self._countdown_task = self._loop.create_task(self._auto_countdown())
        while self._is_running:
            await asyncio.sleep(self._auto_turn_every)
            await self._msg.edit(content=next(self._auto_worker), allowed_mentions=self._allowed_mentions)
    
    async def _execute_session(self):
        """|abc coro| Begin the pagination process"""
        while self._is_running:
            try:
                if self._navigation_speed == TextMenu.NORMAL:
                    reaction, user = await self._bot.wait_for('reaction_add', check=self._wait_check, timeout=self._timeout)
                elif self._navigation_speed == TextMenu.FAST:
                    reaction, user = await self._handle_fast_navigation()
                else:
                    raise ReactionMenuException(f'Navigation speed {self._navigation_speed!r} is not recognized')
            except asyncio.TimeoutError:
                self._menu_timed_out = True
                await self.stop(delete_menu_message=self._delete_on_timeout, clear_reactions=self._clear_reactions_after)
            else:
                emoji = str(reaction.emoji)

                for btn in self._all_buttons:
                    # back
                    if emoji == btn.emoji and btn.linked_to is ButtonType.PREVIOUS_PAGE:
                        worker = self._contents[self._page_control('-')]
                        await self._execute_navigation_type(worker, btn.emoji)
                        await self._contact_relay(user, btn)
                        break

                    # next
                    elif emoji == btn.emoji and btn.linked_to is ButtonType.NEXT_PAGE:
                        worker = self._contents[self._page_control('+')]
                        await self._execute_navigation_type(worker, btn.emoji)
                        await self._contact_relay(user, btn)
                        break

                    # first page
                    elif emoji == btn.emoji and btn.linked_to is ButtonType.GO_TO_FIRST_PAGE:
                        self._page_number = 0
                        worker = self._contents[self._page_number]
                        await self._execute_navigation_type(worker, btn.emoji)
                        await self._contact_relay(user, btn)
                        break

                    # last page
                    elif emoji == btn.emoji and btn.linked_to is ButtonType.GO_TO_LAST_PAGE:
                        self._page_number = len(self._contents) - 1
                        worker = self._contents[self._page_number]
                        await self._execute_navigation_type(worker, btn.emoji)
                        await self._contact_relay(user, btn)
                        break

                    # go to page
                    elif emoji == btn.emoji and btn.linked_to is ButtonType.GO_TO_PAGE:
                        def check(m):
                            not_bot = False
                            author_pass = False
                            channel_pass = False

                            if not m.author.bot:
                                not_bot = True
                            if self._ctx.author.id == m.author.id:
                                author_pass = True

                            if self._send_to_channel is None:
                                if self._ctx.channel.id == m.channel.id:
                                    channel_pass = True
                            else:
                                if self._send_to_channel.id == m.channel.id:
                                    channel_pass = True
                            
                            return all((author_pass, channel_pass, not_bot))

                        bot_prompt = await self._msg.channel.send(f'{self._ctx.author.name}, what page would you like to go to?')
                        try:
                            msg = await self._ctx.bot.wait_for('message', check=check, timeout=self._timeout)
                        except asyncio.TimeoutError:
                            break
                        else:
                            try:
                                requested_page = int(msg.content)
                            except ValueError:
                                break
                            else:
                                if requested_page >= 1 and requested_page <= self.total_pages:
                                    self._page_number = requested_page - 1
                                    worker = self._contents[self._page_number]
                                    await self._execute_navigation_type(worker, btn.emoji)
                                    await self._contact_relay(user, btn)
                                    if self._delete_interactions:
                                        await bot_prompt.delete()
                                        await msg.delete()
                                    break

                    # caller button
                    elif emoji == btn.emoji and btn.linked_to is ButtonType.CALLER:	
                        func = btn.details[0]
                        args = btn.details[1]
                        kwargs = btn.details[2]
                        ERROR_MESSAGE = 'When using class method ButtonType.caller_details(), an improper amount of arguments were passed'
                        if asyncio.iscoroutinefunction(func):
                            try:
                                await func(*args, **kwargs)
                            except TypeError as invalid_args:
                                raise ReactionMenuException(f'{ERROR_MESSAGE}: {invalid_args}')
                        else:
                            try:
                                func(*args, **kwargs)
                            except TypeError as invalid_args:
                                raise ReactionMenuException(f'{ERROR_MESSAGE}: {invalid_args}')

                        # worker param is :class:`None` just as a placeholder. It is not handled in the call			
                        await self._execute_navigation_type(None, btn.emoji, from_caller_button=True)
                        await self._contact_relay(user, btn)
                        break
                    
                    # end session
                    elif emoji == btn.emoji and btn.linked_to is ButtonType.END_SESSION:
                        await self._contact_relay(user, btn)
                        await self.stop(delete_menu_message=True)

    @ensure_not_primed
    @menu_verification
    async def start(self, *, send_to: Union[str, int, TextChannel]=None):
        """|coro| Starts the text menu

        Parameter
        ---------
        send_to: Union[:class:`str`, :class:`int`, :class:`discord.TextChannel`]
            (optional) The channel you'd like the menu to start in. Use the channel name, ID, or it's object. Please note that if you intend to use a text channel object, using
            method :meth:`discord.Client.get_channel`, that text channel should be in the same list as if you were to use `ctx.guild.text_channels`. This only works on a context guild text channel basis. That means a menu instance cannot be
            created in one guild and the menu itself (:param:`send_to`) be sent to another. Whichever guild context the menu was instantiated in, the text channels of that guild are the only options for :param:`send_to` (defaults to :class:`None`)

        Example for :param:`send_to`
        ---------------------------
        ```
        menu = TextMenu(...)
        # channel name
        await menu.start(send_to='bot-commands')

        # channel ID
        await menu.start(send_to=1234567890123456)

        # channel object
        channel = guild.get_channel(1234567890123456)
        await menu.start(send_to=channel)
        ```

        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call this method after the menu has started
        - `ReactionMenuException`: The menu was started before content was added
        - `NoButtons`: Attempted to start the menu when no Buttons have been registered
        - `ReactionMenuException`: A duplicate Button emoji/name was used

            .. note::
                ABC meth
        """
        # check if the menu is limited
        if TextMenu._sessions_limited:
            can_proceed = await self._handle_session_limits()
            if not can_proceed:
                return

        # determine the channel to send the menu to (if any)
        self._determine_location(send_to)

        if len(self._contents) == 0:
            raise ReactionMenuException("You cannot start a TextMenu when you haven't added any content")
        
        # the only difference between this and else is since its only 1 page, theres no need to add reactions to the message
        elif len(self._contents) == 1:
            self._mark_pages()
            if self._send_to_channel is None:
                self._msg = await self._ctx.send(self._contents[0], allowed_mentions=self._allowed_mentions)
            else:
                self._msg = await self._send_to_channel.send(self._contents[0], allowed_mentions=self._allowed_mentions)
            
        else:
            self._mark_pages()
            if self._send_to_channel is None:
                self._msg = await self._ctx.send(self._contents[0], allowed_mentions=self._allowed_mentions)
            else:
                self._msg = await self._send_to_channel.send(self._contents[0], allowed_mentions=self._allowed_mentions)
            
            if not self._auto_paginator:
                for btn in self.all_buttons:
                    await self._msg.add_reaction(btn.emoji)
            
        TextMenu._active_sessions.append(self)
        self._is_running = True

        if self._auto_paginator:
            self._main_session_task = self._loop.create_task(self._execute_auto_session())
        else:
            self._main_session_task = self._loop.create_task(self._execute_session())

        TextMenu._task_sessions_pool.append(self._main_session_task)
        self._main_session_task.add_done_callback(self._main_session_callback)

        self._runtime_tracking_task = self._loop.create_task(self._track_runtime())
