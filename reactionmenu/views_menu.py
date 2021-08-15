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

import asyncio
import collections
import inspect
import re
import warnings
from typing import List, NamedTuple, Union

import discord
from discord.ext.commands import Context

from . import ViewButton
from .abc import _PageController
from .decorators import ensure_not_primed
from .errors import (
    ButtonNotFound,
    DescriptionOversized,
    ImproperStyleFormat,
    IncorrectType,
    MenuSettingsMismatch,
    MissingSetting,
    NoButtons,
    NoPages,
    TooManyButtons,
    ViewMenuException
)


class ViewMenu:
    TypeEmbed = 1
    TypeEmbedDynamic = 2
    TypeText = 3

    _active_sessions: List[ViewMenu] = []

    def __init__(self, ctx: Context, *, menu_type: int, **kwargs):
        # kwargs
        self.delete_on_timeout: bool = kwargs.get('delete_on_timeout', False)
        self.disable_buttons_on_timeout: bool = kwargs.get('disable_buttons_on_timeout', True)
        self.remove_buttons_on_timeout: bool = kwargs.get('remove_buttons_on_timeout', False)
        self.all_can_click: bool = kwargs.get('all_can_click', False)
        self.timeout: Union[int, float, None] = kwargs.get('timeout', 60.0) # property get/set

        # view
        self._view = discord.ui.View(timeout=self.timeout)
        self._view.on_timeout = self._on_dpy_view_timeout
    
    async def _on_dpy_view_timeout(self):
        self._menu_timed_out = True
        await self.stop(delete_menu_message=self.delete_on_timeout, remove_buttons=self.remove_buttons_on_timeout, disable_buttons=self.disable_buttons_on_timeout)
    
    @classmethod
    async def stop_session(cls, name: str, include_all: bool=False):
        """|coro class method| Stop a menu session by it's name
        
        Parameters
        ----------
        name: :class:`str`
            Menu name to search for
        
        include_all: :class:`bool`
            (optional) If all menu's that match the given name should be stopped. If `False`, only the most recently started menu that matched the given name will be stopped (defaults to `False`)
        """
        sessions_to_stop = [session for session in cls._active_sessions if session.name == name]
        if sessions_to_stop:
            if include_all:
                for session in sessions_to_stop:
                    await session.stop()
            else:
                await sessions_to_stop[-1].stop()
    
    @classmethod
    async def stop_all_sessions(cls):
        """|coro class method| Stop all active menu sessions"""
        while cls._active_sessions:
            menu = cls._active_sessions[0]
            await menu.stop()
    
    @classmethod
    def get_menu_from_message(cls, message_id: int) -> Union[ViewMenu, None]:
        """|class method| Return the :class:`ViewMenu` object associated with the message with the given ID
        
        Parameters
        ----------
        message_id: :class:`int`
            The message ID from the menu message
        
        Returns
        -------
        :class:`ViewMenu`:
           Can be :class:`None` if the menu is not found in the list of active menu sessions
        """
        for menu in cls._active_sessions:
            if menu._msg.id == message_id:
                return menu
        return None
        
    @classmethod
    def get_all_sessions(cls) -> Union[List[ViewMenu], None]:
        """|class method| Get all active menu sessions
        
        Returns
        -------
        List[:class:`ViewMenu`]:
            Can be :class:`None` if there are no active menu sessions
        """
        return cls._active_sessions if cls._active_sessions else None
    
    @classmethod
    def get_sessions_count(cls) -> int:
        """|class method| Get the amount of active menu sessions
        
        Returns
        -------
        :class:`int`
        """
        return len(cls._active_sessions)
    
    @classmethod
    def get_session(cls, name: str) -> Union[ViewMenu, List[ViewMenu], None]:
        """|class method| Get a :class:`ViewMenu` instance by its name
        
        Parameters
        ----------
        name: :class:`str`
            :class:`ViewMenu` instance name
        
        Returns
        -------
        Union[:class:`ViewMenu`, List[:class:`ViewMenu`]]:
            The :class:`ViewMenu` instance that was found. Can return a list of :class:`ViewMenu` if multiple instances are running that matched the provided name. Can also return :class:`None` if the menu with the provided
            name was not found
        """
        name = str(name)
        matched_sessions = [session for session in cls._active_sessions if session.name == name]
        if matched_sessions:
            if len(matched_sessions) == 1:
                return matched_sessions[0]
            else:
                return matched_sessions
        else:
            return None
    
    @property
    def timeout(self):
        """.. added:: v3.0.0"""
        return self.__timeout
    
    @timeout.setter
    def timeout(self, value):
        """A property getter/setter for kwarg `timeout`
        
            .. added:: v3.0.0
        """
        if isinstance(value, (int, float)):
            self._view.timeout = value
        else:
            raise IncorrectType(f'"timeout" expected int or float, got {value.__class__.__name__}')

    @property
    def is_running(self) -> bool:
        """
        Returns
        -------
        :class:`bool`:
            If the menu is currently active
        """
        return self._is_running
    
    @property
    def owner(self) -> Union[discord.Member, discord.User]:
        """
        Returns
        -------
        Union[:class:`discord.Member`, :class:`discord.User`]:
            The person who started the menu. Will be :class:`discord.User` if the menu was started in DM's
        """
        return self._ctx.author
    
    @property
    def message(self) -> discord.Message:
        """
        Returns
        -------
        :class:`discord.Message`:
            The message the :class:`ViewMenu` is operating from
        """
        return self._msg
    
    @property
    def buttons(self) -> List[ViewButton]:
        """
        Returns
        -------
        List[:class:`ViewButton`]: The buttons that have been added to the menu. Can be :class:`None` if there are no buttons registered to the menu
        """
        return self._buttons if self._buttons else None
    
    @property
    def buttons_most_clicked(self) -> List[ViewButton]:
        """
        Returns
        -------
        List[:class:`ViewButton`]:
            The buttons on the menu ordered from highest (button with the most clicks) to lowest (button with the least clicks). Can be :class:`None` if there are no buttons registered to the menu
        """
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
    
    @property
    def pages(self) -> List[Union[discord.Embed, str]]:
        """
        Returns
        -------
        A list of either :class:`discord.Embed` if the menu_type is :attr:`ViewMenu.TypeEmbed` / :attr:`ButtonsEmbed.TypeEmbedDynamic`. Or :class:`str` if :attr:`ViewMenu.TypeText`. Can return :class:`None` if there are no pages
        """
        return self.__pages if self.__pages else None
    
    def _handle_send_to(self, send_to):
        """For the `send_to` kwarg in :meth:`ViewMenu.start()`, determine what channel the menu should start in"""
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
                    # before we continue, check if there are any duplicate named channels/no matching names found if a str was provided
                    if isinstance(send_to, str):
                        matched_channels = [ch for ch in self._ctx.guild.text_channels if ch.name == send_to]
                        if len(matched_channels) == 0:
                            raise ViewMenuException(f'When using parameter "send_to" in ViewMenu.start(), there were no channels with the name {send_to!r}')
                        
                        elif len(matched_channels) >= 2:
                            raise ViewMenuException(f'When using parameter "send_to" in ViewMenu.start(), there were {len(matched_channels)} channels with the name {send_to!r}. With multiple channels having the same name, the intended channel is unknown')
                    
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
                        raise ViewMenuException(f'When using parameter "send_to" in ViewMenu.start(), the channel {send_to} was not found')
    
    def _check(self, inter: discord.Interaction):
        """Base menu button interaction check"""
        author_pass = False
        if self._ctx.author.id == inter.user.id: author_pass = True
        if self.only_roles: self.all_can_click = False

        if self.only_roles:
            for role in self.only_roles:
                if role in inter.user.roles:
                    author_pass = True
                    break
        if self.all_can_click:
            author_pass = True

        return author_pass
    
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
    
    def _refresh_page_director_info(self, type_: int, pages: List[Union[discord.Embed, str]]):
        """Sets the page count at the bottom of embeds/text if set
        
        Parameters
        ----------
        type_: :class:`str`
            Either `ViewMenu.TypeEmbed`/`ViewMenu.TypeEmbedDynamic` or `ViewMenu.TypeText`
        
        pages: List[Union[:class:`discord.Embed`, :class:`str`]]
            The pagination contents
        """
        if self.show_page_director:
            if type_ not in (ViewMenu.TypeEmbed, ViewMenu.TypeEmbedDynamic, ViewMenu.TypeText): raise Exception('Needs to be of type ViewMenu.TypeEmbed, ViewMenu.TypeEmbedDynamic or ViewMenu.TypeText')
            
            if type_ == ViewMenu.TypeEmbed or type_ == ViewMenu.TypeEmbedDynamic:
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

    async def _handle_event(self, button: ViewButton):
        """If an event is set, disable/remove the buttons from the menu when the click requirement has been met
            
            .. added:: v2.0.2
        """
        if button.event:
            event_type = button.event.event_type
            event_value = button.event.value
            if button.total_clicks == event_value:
                if event_type == ViewButton.Event._disable:
                    self.disable_button(button)
                    await self.refresh_menu_buttons()
                
                elif event_type == ViewButton.Event._remove:
                    self.remove_button(button)
                    await self.refresh_menu_buttons()
    
    def _chunks(self, list_, n):
        """Yield successive n-sized chunks from list. Core component of a dynamic menu"""
        for i in range(0, len(list_), n):
            yield list_[i:i + n]
    
    async def _contact_relay(self, member: discord.Member, button: ViewButton):
        """Dispatch the information to the relay function if a relay has been set
            
            .. added:: v2.0.1
        """
        if self._relay_info:
            func: object = self._relay_info.func
            only: List[ViewButton] = self._relay_info.only
            RelayPayload = collections.namedtuple('RelayPayload', ['member', 'button'])
            payload = RelayPayload(member=member, button=button)

            async def call():
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func(payload)
                    else:
                        func(payload)
                except TypeError:
                    raise ViewMenuException('When setting a relay, the relay function must have exactly one positional argument')

            if only:
                if button in only:
                    await call()
            else:
                await call()
    
    def set_relay(self, func: object, only: List[ViewButton]=None):
        """Set a function to be called with a given set of information when a button is clicked on the menu. The information passed is `RelayPayload`, a named tuple object. The named tuple contains the following attributes:
        - `member`: The :class:`discord.Member` that clicked the button. Could be :class:`discord.User` if the menu button was clicked in a direct message
        - `button`: The :class:`ViewButton` that was clicked
        
        Parameters
        ---------
        func: Callable[[:class:`NamedTuple`], :class:`None`]
            The function should only contain a single positional argument. Discord.py command functions (`@bot.command()`) not supported
        
        only: List[:class:`ViewButton`]
            (optional) If this is set, only the buttons you've set in the list will be relayed (defaults to :class:`None`)
        
        Raises
        ------
        - `IncorrectType`: The argument provided was not callable
        
            .. added:: v2.0.1

            .. changes::
                v3.0.0
                    Added :param:`only`
        """
        if callable(func):
            RelayInfo = collections.namedtuple('RelayInfo', ['func', 'only'])
            self._relay_info = RelayInfo(func=func, only=only)
        else:
            raise IncorrectType('When setting the relay, argument "func" must be callable')
    
    def remove_relay(self):
        """Remove the relay that's been set
            
            .. added:: v2.0.1
        """
        self._relay_info = None
    
    def _remove_director(self, page: Union[discord.Embed, str]):
        """Removes the page director contents from the page
        
            .. added:: v2.0.1
        """
        style = self.style
        if style is None:
            style = 'Page $/&'
        
        escaped_style = re.escape(style)
        STYLE_PATTERN = escaped_style.replace(r'\$', r'\d{1,}').replace(r'\&', r'\d{1,}')
        STYLE_STR_PATTERN = escaped_style.replace(r'\$', r'\d{1,}').replace(r'\&', r'(\d{1,}.*)')
        
        if self.show_page_director:
            if isinstance(page, discord.Embed):
                if page.footer.text:
                    DIRECTOR_PATTERN = STYLE_PATTERN + r':? '
                    if re.search(DIRECTOR_PATTERN, page.footer.text):
                        page.set_footer(text=re.sub(DIRECTOR_PATTERN, '', page.footer.text), icon_url=page.footer.icon_url)

            elif isinstance(page, str):
                if re.search(STYLE_STR_PATTERN, page):
                    return re.sub(STYLE_STR_PATTERN, '', page).rstrip('\n')
                else:
                    return page

            else:
                raise TypeError(f'_remove_director parameter "page" expected discord.Embed or str, got {page.__class__.__name__}')
        else:
            return page
    
    async def update(self, new_pages: Union[List[Union[discord.Embed, str]], None], new_buttons: Union[List[ViewButton], None]):
        """|coro| When the menu is running, update the pages or buttons 
        
        Parameters
        ----------
        new_pages: List[Union[:class:`discord.Embed`, :class:`str`]]
            Pages to *replace* the current pages with. If the menus current menu_type is `ViewMenu.TypeEmbed`, only :class:`discord.Embed` can be used. If `ViewMenu.TypeText`, only :class:`str` can be used. If you
            don't want to replace any pages, set this to :class:`None`
        
        new_buttons: List[:class:`ViewButtons`]
            Buttons to *replace* the current buttons with. Can be an empty list if you want the updated menu to have no buttons. Can also be set to :class:`None` if you don't want to replace any buttons
        
        Raises
        ------
        - `ViewMenuException`: The :class:`ViewButton` custom_id was not recognized or a :class:`ViewButton` with that ID has already been added
        - `TooManyButtons`: There are already 25 buttons on the menu
        - `IncorrectType`: The values in :param:`new_pages` did not match the :class:`ViewMenu` menu_type. An attempt to use this method when the menu_type is `ViewMenu.TypeEmbedDynamic` which is not allowed. Or
        all :param:`new_buttons` values were not of type :class:`ViewButton`
        """
        if self._is_running:
            # ----------------------- CHECKS -----------------------
            
            if new_pages is None and new_buttons is None:
                return

            if self._menu_type not in (ViewMenu.TypeEmbed, ViewMenu.TypeText):
                raise IncorrectType('Updating a menu is only valid for a menu with menu_type ViewMenu.TypeEmbed or ViewMenu.TypeText')
            
            if self._menu_type == ViewMenu.TypeEmbed and new_pages:
                if not all([isinstance(page, discord.Embed) for page in new_pages]):
                    raise IncorrectType('When updating the menu, all values must be of type discord.Embed because the current menu_type is ViewMenu.TypeEmbed')
            
            if self._menu_type == ViewMenu.TypeText and new_pages:
                if not all([isinstance(page, str) for page in new_pages]):
                    raise IncorrectType('When updating the menu, all values must be of type str because the current menu_type is ViewMenu.TypeText')
            
            if isinstance(new_pages, list) and len(new_pages) == 0:
                raise ViewMenuException('new_pages cannot be an empty list. Must be None if no new pages should be added')
            
            # ----------------------- END CHECKS -----------------------

            if new_pages is not None:
                if self._menu_type == ViewMenu.TypeEmbed:
                    for new_embed_page in new_pages:
                        self._remove_director(new_embed_page)
                    
                    self.__pages = new_pages.copy()
                    self._pc = _PageController(new_pages)
                    self._refresh_page_director_info(ViewMenu.TypeEmbed, self.__pages)
                else:
                    removed_director_info = []
                    for new_str_page in new_pages.copy():
                        removed_director_info.append(self._remove_director(new_str_page))
                    
                    self.__pages = removed_director_info.copy()
                    self._pc = _PageController(self.__pages)
                    self._refresh_page_director_info(ViewMenu.TypeText, self.__pages)
            else:
                # page controller needs to be reset because even though there are no new pages. the page index is still in the location BEFORE the update
                # EXAMPLE: 5 page menu > click Next button  (on page 2) > update menu no new pages > click Next button (on page 3)
                # that makes no sense and resetting the page controller fixes that issue 
                self._pc = _PageController(self.__pages)
            
            kwargs_to_pass = {'view' : self._view}

            if isinstance(new_buttons, list):
                if new_buttons:
                    self.remove_all_buttons()
                    for new_btn in new_buttons:
                        # this needs to be set to `True` every loop because once the decorator has been bypassed, the decorator resets that bypass back to `False`
                        # i could set the bypass values before and after the loop, but the time it takes for new buttons to be replaced *could* be enough time for other
                        # calls to methods that depend on :dec:`ensure_not_primed` to be executed, which is not good . insufficient, yes i know, but its better to prevent
                        # unwanted successful calls to methods that are decorated with :dec:`ensure_not_primed`. the benefits outweigh the costs. not to mention it's
                        # better to have this simply call :meth:`add_button()` instead of copying the contents of :meth:`add_button()` to bypass :dec:`ensure_not_primed`
                        self._bypass_primed = True
                        
                        self.add_button(new_btn)
            
            if self._menu_type == ViewMenu.TypeEmbed:
                kwargs_to_pass['embed'] = self.__pages[0]
            else:
                kwargs_to_pass['content'] = self.__pages[0]
            
            await self._msg.edit(**kwargs_to_pass)
    
    async def refresh_menu_buttons(self):
        """|coro| When the menu is running, update the message to reflect the buttons that were removed, enabled, or disabled"""
        if self._is_running:
            await self._msg.edit(view=self._view)
    
    def remove_button(self, button: ViewButton):
        """Remove a button from the menu
        
        Parameters
        ----------
        button: :class:`ViewButton`
            The button to remove
        
        Raises
        ------
        - `ButtonNotFound`: The provided button was not found in the list of buttons on the menu
        
            .. changes::
                v2.0.1
                    Added reset of button._menu (set to :class:`None`)
        """
        if button in self._buttons:
            button._menu = None
            self._buttons.remove(button)
            self._view.remove_item(button)
        else:
            raise ButtonNotFound(f'Cannot remove a button that is not registered')
    
    def remove_all_buttons(self):
        """Remove all buttons from the menu"""
        for btn in self._buttons:
            btn._menu = None
        self._buttons.clear()
        self._view.clear_items()
    
    def disable_button(self, button: ViewButton):
        """Disable a button on the menu
        
        Parameters
        ----------
        button: :class:`ViewButton`
            The button to disable
        
        Raises
        ------
        - `ButtonNotFound`: The provided button was not found in the list of buttons on the menu
        """
        if button in self._buttons:
            idx = self._buttons.index(button)
            self._buttons[idx].disabled = True
        else:
            raise ButtonNotFound(f'Cannot disable a button that is not registered')
    
    def disable_all_buttons(self):
        """Disable all buttons on the menu"""
        for btn in self._buttons:
            btn.disabled = True
    
    def enable_button(self, button: ViewButton):
        """Enable the specified button
        
        Parameters
        ----------
        button: :class:`ViewButton`
            The button to enable
        
        Raises
        ------
        - `ButtonNotFound`: The provided button was not found in the list of buttons on the menu
        """
        if button in self._buttons:
            idx = self._buttons.index(button)
            self._buttons[idx].disabled = False
        else:
            raise ButtonNotFound('Cannot enable a button that is not registered')
    
    def enable_all_buttons(self):
        """Enable all buttons on the menu"""
        for btn in self._buttons:
            btn.disabled = False
    
    def set_on_timeout(self, func: object):
        """Set the function to be called when the menu times out
        
        Parameters
        ----------
        func: :class:`object`
            The function object that will be called when the menu times out. The function should contain a single positional argument
            and should not return anything. The argument passed to that function is an instance of the menu.
        
        Raises
        ------
        - `ViewMenuException`: Parameter "func" was not a callable object
        """
        if not callable(func): raise ViewMenuException('Parameter "func" must be callable')
        self._on_timeout_details = func
    
    def remove_on_timeout(self):
        """Remove the timeout call to the function you have set when the menu times out
        
            .. added:: v3.0.0
        """
        self._on_timeout_details = None
    
    def _button_add_check(self, button: ViewButton):
        """A set of checks to ensure the proper button is being added
        
            .. changes::
                Replaced :meth:`_get_all_ids` with re handling
        """
        # ensure they are using only the ViewButton and not ReactionMenus :class:`Button` / :class:`ButtonType`
        if isinstance(button, ViewButton):

            # ensure the button custom_id is a valid one, but skip this check if its a link button because they dont have custom_ids
            if button.style == discord.ButtonStyle.link:
                pass
            else:
                # Note: this needs to be an re search because of buttons with an ID of "[ID]_[unique ID]"
                if not re.search(ViewButton._RE_IDs, button.custom_id):
                    raise ViewMenuException(f'ViewButton custom_id {button.custom_id!r} was not recognized')
            
            # ensure there are no duplicate custom_ids for the base navigation buttons
            # Note: there's no need to have a check for buttons that are not navigation buttons because they have a unique ID and duplicates of those are allowed
            active_button_ids: List[str] = [btn.custom_id for btn in self._buttons]
            if button.custom_id in active_button_ids:
                name = ViewButton._get_id_name_from_id(button.custom_id)
                raise ViewMenuException(f'A ViewButton with custom_id {name!r} has already been added')
            
            # ensure there are no more than 25 buttons
            if len(self._buttons) >= 25:
                raise TooManyButtons('ViewMenu cannot have more than 25 buttons (discord limitation)')
        else:
            raise IncorrectType(f'When adding a button to the ViewMenu, the button type must be ViewButton, got {button.__class__.__name__}')
    
    def _maybe_unique_id(self, button: ViewButton):
        """Create a unique ID if the custom_id is ViewButton.ID_SEND_MESSAGE, ViewButton.ID_CALLER, or ViewButton.ID_CUSTOM_EMBED"""
        if button.custom_id in (ViewButton.ID_CALLER, ViewButton.ID_SEND_MESSAGE, ViewButton.ID_CUSTOM_EMBED):
            button.custom_id = f'{button.custom_id}_{id(button)}'
    
    @ensure_not_primed
    def add_button(self, button: ViewButton):
        """Register a button to the menu
        
        Parameters
        ----------
        button: :class:`ViewButton`
            The button to register
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `ViewMenuException`: The custom_id for the button was not recognized. A button with that custom_id has already been added
        - `TooManyButtons`: There are already 25 buttons on the menu
        - `IncorrectType`: Parameter :param:`button` was not of type :class:`ViewButton`
        """
        self._button_add_check(button)
        self._maybe_unique_id(button)

        button._menu = self
        self._view.add_item(button)
        self._buttons.append(button)
    
    def get_button(self, identity: str, *, search_by: str='label') -> Union[ViewButton, List[ViewButton], None]:
        """Get a button that has been registered to the menu by it's label or custom_id
        
        Parameters
        ----------
        identity: :class:`str`
            The button label (case sensitive) or it's custom_id
        
        search_by: :class:`str`
            (optional) How to search for the button. If "label", it's searched by button labels, if "id", it's searched by it's custom_id (defaults to "label")
        
        Raises
        ------
        - `ViewMenuException`: Parameter :param:`search_by` was not "label" or "id"
        
        Returns
        -------
        Union[:class:`ViewButton`, List[:class:`ViewButton`]]:
            The button(s) matching the given identity. Can be :class:`None` if the button was not found
        """
        identity = str(identity)
        search_by = str(search_by).lower()

        if search_by in ('label', 'id'):
            if search_by == 'label':
                matched_labels = [btn for btn in self._buttons if btn.label == identity]
                if matched_labels:
                    if len(matched_labels) == 1: return matched_labels[0]
                    else: return matched_labels
                else:
                    return None
            else:
                matched_id = [btn for btn in self._buttons if btn.custom_id == identity]
                if matched_id: return matched_id[0]
                else: return None
        else:
            raise ViewMenuException(f'Parameter "search_by" expected "label" or "id", got {search_by!r}')
    
    @ensure_not_primed
    def clear_all_pages(self):
        """Remove all pages from the menu
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        """
        self.__pages.clear()
    
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
        if self.__pages:
            if page_number > 0 and page_number <= len(self.__pages):
                page_to_delete = page_number - 1
                del self.__pages[page_to_delete]
            else:
                raise ViewMenuException(f'Page number invalid. Must be from 1 - {len(self.__pages)}')
    
    @ensure_not_primed
    def add_page(self, page: Union[discord.Embed, str]):
        """Add a page to the menu
        
        Parameters
        ----------
        page: Union[:class:`discord.Embed`, :class:`str`]
            The page to add. Can only be used when the menus `menu_type` is `ViewMenu.TypeEmbed` (adding an embed) or `ViewMenu.TypeText` (adding a str)
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: The page being added does not match the menus `menu_type` 
        """
        if self._menu_type == ViewMenu.TypeEmbed:
            if isinstance(page, discord.Embed):
                self.__pages.append(page)
            else:
                raise MenuSettingsMismatch(f'ViewMenu menu_type was set as ViewMenu.TypeEmbed but got {page.__class__.__name__} when adding a page')
        
        elif self._menu_type == ViewMenu.TypeText:
            self.__pages.append(str(page))
        
        else:
            raise MenuSettingsMismatch('add_page method cannot be used with the current ViewMenu menu_type')
    
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

    def _determine_action(self, action) -> dict:
        kwargs = {
            'embed' if self._menu_type in (ViewMenu.TypeEmbed, ViewMenu.TypeEmbedDynamic) else 'content' : action,
            'view' : self._view
        }
        return kwargs

    async def _paginate(self, button: ViewButton, inter: discord.Interaction):
        if not self._check(inter):
            await inter.response.defer()
            return

        if button.custom_id == ViewButton.ID_PREVIOUS_PAGE:
            await inter.response.edit_message(**self._determine_action(self._pc.prev()))
        
        elif button.custom_id == ViewButton.ID_NEXT_PAGE:
            await inter.response.edit_message(**self._determine_action(self._pc.next()))
        
        elif button.custom_id == ViewButton.ID_GO_TO_FIRST_PAGE:
            await inter.response.edit_message(**self._determine_action(self._pc.first_page()))
        
        elif button.custom_id == ViewButton.ID_GO_TO_LAST_PAGE:
            await inter.response.edit_message(**self._determine_action(self._pc.last_page()))
        
        elif button.custom_id == ViewButton.ID_GO_TO_PAGE:
            await inter.response.defer()
            prompt: discord.Message = await self._msg.channel.send(f'{inter.user.display_name}, what page would you like to go to?')
            try:
                selection_message: discord.Message = await self._ctx.bot.wait_for('message', check=lambda m: all([m.channel.id == self._msg.channel.id, m.author.id == inter.user.id]), timeout=self.timeout)
                page = int(selection_message.content)
            except asyncio.TimeoutError:
                return
            except ValueError:
                return
            else:
                if 1 <= page <= len(self.__pages):
                    self._pc.index = page - 1
                    await self._msg.edit(**self._determine_action(self._pc.current_page))
                    if self.delete_interactions:
                        await prompt.delete()
                        await selection_message.delete()
        
        elif button.custom_id == ViewButton.ID_END_SESSION:
            await self.stop(delete_menu_message=True)
        
        else:
            if button.custom_id.startswith(ViewButton.ID_CALLER):
                if button.followup is None or button.followup._caller_info is None:
                    error_msg = 'ViewButton custom_id was set as ViewButton.ID_CALLER but the "followup" kwarg for that ViewButton was not set ' \
                                'or method ViewButton.Followup.set_caller_details(..) was not called to set the caller information'
                    raise ViewMenuException(error_msg)
                
                func = button.followup._caller_info.func
                args = button.followup._caller_info.args
                kwargs = button.followup._caller_info.kwargs

                # reply now because we don't know how long the users function will take to execute
                await inter.response.defer()

                try:
                    if asyncio.iscoroutinefunction(func): await func(*args, **kwargs)
                    else: func(*args, **kwargs)
                except Exception as err:
                    call_failed_error_msg = inspect.cleandoc(
                        f"""
                        The button with custom_id ViewButton.ID_CALLER with the label "{button.label}" raised an error during it's execution
                        -> {err.__class__.__name__}: {err}
                        """
                    )
                    raise ViewMenuException(call_failed_error_msg)
                else:
                    if button.followup:
                        # if this executes, the user doesn't want to respond with a message, only with the caller function (already called ^)
                        if all((button.followup.content is None, button.followup.embed is None, button.followup.file is None)):
                            pass
                        else:
                            followup_kwargs = button.followup._to_dict()

                            # inter.followup() has no attribute delete_after/_caller_info, so manually delete the key/val pairs to avoid :exc:`TypeError`, got an unexpected kwarg
                            del followup_kwargs['delete_after']
                            del followup_kwargs['_caller_info']
                            
                            # if there's no file, remove it to avoid an NoneType error
                            if followup_kwargs['file'] is None:
                                del followup_kwargs['file']
                            
                            followup_message: discord.WebhookMessage = await inter.followup.send(**followup_kwargs)
                            
                            if button.followup.delete_after:
                                await followup_message.delete(delay=button.followup.delete_after)
            
            elif button.custom_id.startswith(ViewButton.ID_SEND_MESSAGE):
                if button.followup is None:
                    raise ViewMenuException('ViewButton custom_id was set as ViewButton.ID_SEND_MESSAGE but the "followup" kwarg for that ViewButton was not set')
                
                # there must be at least 1. cannot send an empty message
                if all((button.followup.content is None, button.followup.embed is None, button.followup.file is None)):
                    raise ViewMenuException('When using a ViewButton with a custom_id of ViewButton.ID_SEND_MESSAGE, the followup message cannot be empty')
                
                followup_kwargs = button.followup._to_dict()

                # inter.followup.send() has no kwarg "_caller_info"
                del followup_kwargs['_caller_info']
                
                # files are ignored
                del followup_kwargs['file']
                
                # inter.followup.send() has no kwarg "delete_after"
                del followup_kwargs['delete_after']

                # defer instead of inter.response.send_message() so `delete_after` and `allowed_mentions` can be used
                await inter.response.defer()

                sent_message: discord.WebhookMessage = await inter.followup.send(**followup_kwargs)
                if button.followup.delete_after:
                    await sent_message.delete(delay=button.followup.delete_after)
            
            elif button.custom_id.startswith(ViewButton.ID_CUSTOM_EMBED):
                if self._menu_type != ViewMenu.TypeEmbed:
                    raise ViewMenuException('Buttons with custom_id ViewButton.ID_CUSTOM_EMBED can only be used when the menu_type is ViewMenu.TypeEmbed')
                else:
                    if button.followup is None or button.followup.embed is None:
                        raise ViewMenuException('ViewButton custom_id was set as ViewButton.ID_CUSTOM_EMBED but the "followup" kwargs for that ViewButton was not set or the "embed" kwarg for the followup was not set')
                    
                    """
                    I would have used `inter.response.edit_message`, but for whatever reason i'm getting the error:
                        
                        discord.errors.HTTPException: 400 Bad Request (error code: 50035): Invalid Form Body
                        In components.0.components.5: The specified component exceeds the maximum width
                    
                    Not sure what could be causing it when that works for all base navigation buttons
                    """
                    await inter.response.defer()
                    await self._msg.edit(embed=button.followup.embed, view=self._view)
            
            else:
                # this shouldn't execute because of :meth:`_button_add_check`, but just in case i missed something, raise the appropriate error
                raise ViewMenuException(f'ViewButton custom_id {button.custom_id!r} was not recognized')

        button._update_statistics(inter.user)
        await self._contact_relay(inter.user, button)
        await self._handle_event(button)

    async def stop(self, *, delete_menu_message: bool=False, remove_buttons: bool=False, disable_buttons: bool=False):
        """|coro| Stops the process of the menu with the option of deleting the menu's message, removing the buttons, or disabling the buttons upon stop
        
        Parameters
        ----------
        delete_menu_message: :class:`bool`
            (optional) Delete the message the menu is operating from (defaults to `False`)

        remove_buttons: :class:`bool`
            (optional) Remove the buttons from the menu (defaults to `False`)

        disable_buttons: :class:`bool`
            (optional) Disable the buttons on the menu (defaults to `False`)

        Parameter Hierarchy
        -------------------
        Only one option is available when stopping the menu. If you have multiple parameters as `True`, only one will execute
        - `delete_menu_message` > `disable_buttons`
        - `disable_buttons` > `remove_buttons`
        """
        if self._is_running:
            try:
                if delete_menu_message:
                    await self._msg.delete()
                
                elif disable_buttons:
                    if not self._buttons: return # if there are no buttons (they've all been removed) to disable, skip this step
                    self.disable_all_buttons()
                    await self._msg.edit(view=self._view)

                elif remove_buttons:
                    if not self._buttons: return # if there are no buttons to remove (they've already been removed), skip this step
                    self.disable_all_buttons()
                    await self._msg.edit(view=self._view)
            
            except discord.DiscordException as dpy_error:
                raise dpy_error
            
            finally:
                self._view.stop()
                self._is_running = False

                if self in ViewMenu._active_sessions:
                    ViewMenu._active_sessions.remove(self)
                
                # handle `on_timeout`
                if self._on_timeout_details and self._menu_timed_out:
                    func = self._on_timeout_details
                    
                    # call the timeout function but ignore any and all exceptions that may occur during the function timeout call.
                    # the most important thing here is to ensure the menu is properly gracefully while displaying a formatted error mesage
                    try:
                        if asyncio.iscoroutinefunction(func): await func(self)
                        else: func(self)
                    except Exception as error:
                        warnings.formatwarning = lambda msg, *args, **kwargs: f'{msg}'
                        warnings.warn(inspect.cleandoc(
                            f"""
                            UserWarning: The function you have set in method ViewMenu.set_on_timeout() raised an error
                            -> {error.__class__.__name__}: {error}
                            
                            This error has been ignored so the menu timeout process can complete
                            """
                        ))
    
    async def start(self, *, send_to: Union[str, int, discord.TextChannel]=None):
        # ---------------------
        # Note 1: each at least 1 page check is done in it's own if statement to avoid clashing between pages and custom embeds
        # Note 2: at least 1 page check for add_row is done in "(dynamic menu)"
        
        # ensure at least 1 button exists before starting the menu
        if not self._buttons:
            raise NoButtons('You cannot start a ViewMenu when no buttons are registered')
        
        # ensure only valid menu types have been set
        if self._menu_type not in (ViewMenu.TypeEmbed, ViewMenu.TypeEmbedDynamic, ViewMenu.TypeText):
            raise ViewMenuException('ViewMenu menu_type not recognized')
        
        # ------------------------------- END CHECKS -------------------------------

        # add page (normal menu)
        if self._menu_type == ViewMenu.TypeEmbed:
            self._refresh_page_director_info(ViewMenu.TypeEmbed, self.__pages)

            navigation_btns = [btn for btn in self._buttons if btn.custom_id in ViewButton._base_nav_buttons()]

            # an re search is required here because buttons with ID_CUSTOM_EMBED dont have a normal ID, the ID is "8_[unique ID]"
            custom_embed_btns = [btn for btn in self._buttons if btn.style != discord.ButtonStyle.link and re.search(r'8_\d+', btn.custom_id)]

            if all([not self.__pages, not custom_embed_btns]):
                raise NoPages("You cannot start a ViewMenu when you haven't added any pages")

            # normal pages, no custom embeds
            if self.__pages and not custom_embed_btns:
                self._msg = await self._handle_send_to(send_to).send(embed=self.__pages[0], view=self._view) # allowed_mentions not needed in embeds
            
            # only custom embeds
            elif not self.__pages and custom_embed_btns:
                # since there are only custom embeds, there is no need for base navigation buttons, so remove them if any
                for nav_btn in navigation_btns:
                    if nav_btn in self._buttons:
                        self._buttons.remove(nav_btn)
                
                # ensure all custom embed buttons have the proper values set
                for custom_btn in custom_embed_btns:
                    if custom_btn.followup is None or custom_btn.followup.embed is None:
                        raise ViewMenuException('ViewButton custom_id was set as ViewButton.ID_CUSTOM_EMBED but the "followup" kwargs for that ViewButton was not set or the "embed" kwarg for the followup was not set')
                
                # since there are only custom embeds, self.__pages is still set to :class:`None`, so set the embed in `.send()` to the first custom embed in the list
                self._msg = await self._handle_send_to(send_to).send(embed=custom_embed_btns[0].followup.embed, view=self._view)
            
            # normal pages and custom embeds
            else:
                # since there are custom embeds, ensure there is at least one base navigation button so they can switch between the normal pages and custom embeds
                if not navigation_btns:
                    error_msg = inspect.cleandoc(
                        """
                        Since you've added pages and custom embeds, there needs to be at least one base navigation button. Without one, there's no way to go back to the normal pages in the menu if a custom embed button is clicked.
                        The available base navigation buttons are buttons with the custom_id:
                        - ViewButton.ID_PREVIOUS_PAGE
                        - ViewButton.ID_NEXT_PAGE
                        - ViewButton.ID_GO_TO_FIRST_PAGE
                        - ViewButton.ID_GO_TO_LAST_PAGE
                        - ViewButton.ID_GO_TO_PAGE
                        """
                    )
                    raise ViewMenuException(error_msg)
                else:
                    self._msg = await self._handle_send_to(send_to).send(embed=self.__pages[0], view=self._view) # allowed_mentions not needed in embeds

        # add row (dynamic menu)
        elif self._menu_type == ViewMenu.TypeEmbedDynamic:
            for data_clump in self._chunks(self._dynamic_data_builder, self.__rows_requested):
                joined_data = '\n'.join(data_clump)
                if len(joined_data) <= 4096:
                    possible_block = f"```{self.wrap_in_codeblock}\n{joined_data}```"
                    embed = discord.Embed() if self.custom_embed is None else self.custom_embed.copy()
                    embed.description = joined_data if not self.wrap_in_codeblock else possible_block
                    self.__pages.append(embed)
                else:
                    raise DescriptionOversized('With the amount of data that was received, the embed description is over discords size limit. Lower the amount of "rows_requested" to solve this problem')
            else:
                # set the main/last pages if any
                if any((self._main_page_contents, self._last_page_contents)):
                    self.__pages = collections.deque(self.__pages)
                    if self._main_page_contents:
                        self._main_page_contents.reverse()
                        self.__pages.extendleft(self._main_page_contents)
                    
                    if self._last_page_contents:
                        self.__pages.extend(self._last_page_contents)
                
                self._refresh_page_director_info(ViewMenu.TypeEmbedDynamic, self.__pages)

                # make sure data has been added to create at least 1 page
                if not self.__pages: raise NoPages('You cannot start a ViewMenu when no data has been added')
                
                self._msg = await self._handle_send_to(send_to).send(embed=self.__pages[0], view=self._view) # allowed_mentions not needed in embeds
        
        # add page (text menu)
        else:
            if not self.__pages:
                raise NoPages("You cannot start a ViewMenu when you haven't added any pages")
            
            self._refresh_page_director_info(ViewMenu.TypeText, self.__pages)
            self._msg = await self._handle_send_to(send_to).send(content=self.__pages[0], view=self._view, allowed_mentions=self.allowed_mentions)
        
        self._pc = _PageController(self.__pages)
        self._is_running = True
        ViewMenu._active_sessions.append(self)
