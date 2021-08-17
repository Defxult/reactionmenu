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
from .abc import _PageController, BaseMenu
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


class ViewMenu(BaseMenu):
    def __init__(self, ctx: Context, *, menu_type: int, **kwargs):
        super().__init__(ctx, menu_type, **kwargs)

        # kwargs
        self.delete_on_timeout: bool = kwargs.get('delete_on_timeout', False)
        self.disable_buttons_on_timeout: bool = kwargs.get('disable_buttons_on_timeout', True)
        self.remove_buttons_on_timeout: bool = kwargs.get('remove_buttons_on_timeout', False)
        self.all_can_click: bool = kwargs.get('all_can_click', False)
        self.__timeout: Union[int, float, None] = kwargs.get('timeout', 60.0) # property get/set

        # view
        self._view = discord.ui.View(timeout=self.__timeout)
        self._view.on_timeout = self._on_dpy_view_timeout
        self._view.on_error = self._on_dpy_view_error
    
    def __repr__(self):
        cls = self.__class__
        return f'<ViewMenu name={self.name!r} owner={str(self._ctx.author)!r} is_running={self._is_running} timeout={self.timeout} menu_type={cls._get_menu_type(self._menu_type)!r}>'

    async def _on_dpy_view_timeout(self):
        self._menu_timed_out = True
        await self.stop(delete_menu_message=self.delete_on_timeout, remove_buttons=self.remove_buttons_on_timeout, disable_buttons=self.disable_buttons_on_timeout)
    
    async def _on_dpy_view_error(self, error: Exception, item: discord.ui.Item, inter: discord.Interaction):
        try:
            raise error
        finally:
            await self.stop()
    
    @property
    def timeout(self):
        return self.__timeout
    
    @timeout.setter
    def timeout(self, value):
        """A property getter/setter for kwarg `timeout`"""
        if isinstance(value, (int, float)):
            self._view.timeout = value
        else:
            raise IncorrectType(f'"timeout" expected int or float, got {value.__class__.__name__}')
    
    @property
    def pages(self) -> List[Union[discord.Embed, str]]:
        """
        Returns
        -------
        List[Union[:class:`discord.Embed`, :class:`str`]]:
            The pages currently applied to the menu. Depending on the `menu_type`, it will return a list of :class:`discord.Embed` if the menu type is :attr:`ViewMenu.TypeEmbed`
            or :attr:`ViewMenu.TypeEmbedDynamic`. If `ViewMenu.TypeText`, it will return a list of :class:`str` Can return :class:`None` if there are no pages
        
        Note: If the `menu_type` is :attr:`ViewMenu.TypeEmbedDynamic`, the amount of pages isn't known until after the menu has started
        """
        return self._pages if self._pages else None
    
    def _get_new_view(self) -> discord.ui.View:
        """Returns a new :class:`discord.ui.View` object with the `timeout` parameter already set"""
        return discord.ui.View(timeout=self.__timeout)
    
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

    def _handle_event(self, button: ViewButton):
        """If an event is set, disable/remove the buttons from the menu when the click requirement has been met"""
        if button.event:
            event_type = button.event.event_type
            event_value = button.event.value
            if button.total_clicks == event_value:
                if event_type == ViewButton.Event._disable:
                    self.disable_button(button)
                
                elif event_type == ViewButton.Event._remove:
                    self.remove_button(button)
    
    def _remove_director(self, page: Union[discord.Embed, str]):
        """Removes the page director contents from the page. This is used for :meth:`ViewMenu.update()`"""
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

            # Note: button count > 25 check is done in :meth:`ViewMenu.add_button`
            
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
                    
                    self._pages = new_pages.copy()
                    self._pc = _PageController(new_pages)
                    self._refresh_page_director_info(ViewMenu.TypeEmbed, self._pages)
                else:
                    removed_director_info = []
                    for new_str_page in new_pages.copy():
                        removed_director_info.append(self._remove_director(new_str_page))
                    
                    self._pages = removed_director_info.copy()
                    self._pc = _PageController(self._pages)
                    self._refresh_page_director_info(ViewMenu.TypeText, self._pages)
            else:
                # page controller needs to be reset because even though there are no new pages. the page index is still in the location BEFORE the update
                # EXAMPLE: 5 page menu > click Next button  (on page 2) > update menu no new pages > click Next button (on page 3)
                # that makes no sense and resetting the page controller fixes that issue 
                self._pc = _PageController(self._pages)
            
            kwargs_to_pass = {}

            if isinstance(new_buttons, list):
                self.remove_all_buttons()
                self._view = self._get_new_view()
                kwargs_to_pass['view'] = self._view
                if len(new_buttons) >= 1:
                    for new_btn in new_buttons:
                        # this needs to be set to `True` every loop because once the decorator has been bypassed, the decorator resets that bypass back to `False`
                        # i could set the bypass values before and after the loop, but the time it takes for new buttons to be replaced *could* be enough time for other
                        # calls to methods that depend on :dec:`ensure_not_primed` to be executed, which is not good . insufficient, yes i know, but its better to prevent
                        # unwanted successful calls to methods that are decorated with :dec:`ensure_not_primed`. the benefits outweigh the costs. not to mention it's
                        # better to have this simply call :meth:`add_button()` instead of copying the contents of :meth:`add_button()` to bypass :dec:`ensure_not_primed`
                        self._bypass_primed = True
                        
                        self.add_button(new_btn)
            
            if self._menu_type == ViewMenu.TypeEmbed:
                kwargs_to_pass['embed'] = self._pages[0]
            else:
                kwargs_to_pass['content'] = self._pages[0]
            
            await self._msg.edit(**kwargs_to_pass)
    
    # FIXME:
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
            
            # if the menu_type is TypeText, disallow custom embed buttons
            if button.style != discord.ButtonStyle.link and self._menu_type == ViewMenu.TypeText:
                if button.custom_id == ViewButton.ID_CUSTOM_EMBED:
                    if button.followup and button.followup.embed is not None:
                        raise MenuSettingsMismatch('ViewButton with custom_id ViewButton.ID_CUSTOM_EMBED cannot be used when the menu_type is ViewMenu.TypeText')
            
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
        - `MenuSettingsMismatch`: The buttons custom_id was set as `ViewButton.ID_CUSTOM_EMBED` but the `menu_type` is `ViewMenu.TypeText`
        - `ViewMenuException`: The custom_id for the button was not recognized or a button with that custom_id has already been added
        - `TooManyButtons`: There are already 25 buttons on the menu
        - `IncorrectType`: Parameter :param:`button` was not of type :class:`ViewButton`
        """
        self._button_add_check(button)
        self._maybe_unique_id(button)

        button._menu = self
        self._view.add_item(button)
        self._buttons.append(button)
    
    def get_button(self, identity: str, *, search_by: str='label') -> Union[ViewButton, List[ViewButton]]:
        """Get a button that has been registered to the menu by it's label, custom_id, or name
        
        Parameters
        ----------
        identity: :class:`str`
            The button label, custom_id, or name
        
        search_by: :class:`str`
            (optional) How to search for the button. If "label", it's searched by button labels. If "id", it's searched by it's custom_id. 
            If "name", it's searched by button names (defaults to "label")
        
        Raises
        ------
        - `ViewMenuException`: Parameter :param:`search_by` was not "label", "id", or "name"
        
        Returns
        -------
        Union[:class:`ViewButton`, List[:class:`ViewButton`]]:
            The button(s) matching the given identity. Can be :class:`None` if the button was not found
        """
        identity = str(identity)
        search_by = str(search_by).lower()

        if search_by == 'label':
            matched_labels: List[ViewButton] = [btn for btn in self._buttons if btn.label and btn.label == identity]
            if matched_labels:
                return matched_labels[0] if len(matched_labels) == 1 else matched_labels
            else:
                return None
        
        elif search_by == 'id':
            matched_ids: List[ViewButton] = [btn for btn in self._buttons if btn.custom_id and btn.custom_id.startswith(identity)]
            if matched_ids:
                return matched_ids[0] if len(matched_ids) == 1 else matched_ids
            else:
                return None
        
        elif search_by == 'name':
            matched_names: List[ViewButton] = [btn for btn in self._buttons if btn.name and btn.name == identity]
            if matched_names:
                return matched_names[0] if len(matched_names) == 1 else matched_names
            else:
                return None
        
        else:
            raise ViewMenuException(f'Parameter "search_by" expected "label", "id", or "name", got {search_by!r}')

    def _determine_edit_kwargs(self, content: Union[discord.Embed, str]) -> dict:
        """Determine the :meth:`inter.response.edit_message` kwargs for the pagination process. Only used in :meth:`ViewMenu._paginate`"""
        kwargs = {
            'embed' if self._menu_type in (ViewMenu.TypeEmbed, ViewMenu.TypeEmbedDynamic) else 'content' : content
            # Note to self: Take a look at the note below as to why the following item in this dict is commented out
            #'view' : self._view
        }
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

    async def _paginate(self, button: ViewButton, inter: discord.Interaction):
        """When the button is pressed, handle the pagination process"""
        if not self._check(inter):
            await inter.response.defer()
            return
        
        button._update_statistics(inter.user)
        self._handle_event(button)
        
        if button.custom_id == ViewButton.ID_PREVIOUS_PAGE:
            await inter.response.edit_message(**self._determine_edit_kwargs(self._pc.prev()))
        
        elif button.custom_id == ViewButton.ID_NEXT_PAGE:
            await inter.response.edit_message(**self._determine_edit_kwargs(self._pc.next()))
        
        elif button.custom_id == ViewButton.ID_GO_TO_FIRST_PAGE:
            await inter.response.edit_message(**self._determine_edit_kwargs(self._pc.first_page()))
        
        elif button.custom_id == ViewButton.ID_GO_TO_LAST_PAGE:
            await inter.response.edit_message(**self._determine_edit_kwargs(self._pc.last_page()))
        
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
                if 1 <= page <= len(self._pages):
                    self._pc.index = page - 1
                    await self._msg.edit(**self._determine_edit_kwargs(self._pc.current_page))
                    if self.delete_interactions:
                        await prompt.delete()
                        await selection_message.delete()
        
        elif button.custom_id == ViewButton.ID_END_SESSION:
            await self.stop(delete_menu_message=True)
        
        else:
            if button.custom_id.startswith(ViewButton.ID_CALLER):
                if button.followup is None or button.followup.details is None:
                    error_msg = 'ViewButton custom_id was set as ViewButton.ID_CALLER but the "followup" kwarg for that ViewButton was not set ' \
                                'or method ViewButton.Followup.set_caller_details(..) was not called to set the caller information'
                    raise ViewMenuException(error_msg)
                
                func = button.followup.details.func
                args = button.followup.details.args
                kwargs = button.followup.details.kwargs

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

                            # inter.followup() has no attribute delete_after/details, so manually delete the key/val pairs to avoid :exc:`TypeError`, got an unexpected kwarg
                            del followup_kwargs['delete_after']
                            del followup_kwargs['details']
                            
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

                # inter.followup.send() has no kwarg "details"
                del followup_kwargs['details']
                
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
                   
                    await inter.response.edit_message(embed=button.followup.embed)            
            else:
                # this shouldn't execute because of :meth:`_button_add_check`, but just in case i missed something, raise the appropriate error
                raise ViewMenuException(f'ViewButton custom_id {button.custom_id!r} was not recognized')

        await self._contact_relay(inter.user, button)

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
                    if not self._buttons:
                        return # if there are no buttons (they've all been removed) to disable, skip this step
                    self.disable_all_buttons()
                    await self._msg.edit(view=self._view)

                elif remove_buttons:
                    if not self._buttons:
                        return # if there are no buttons (they've already been removed), skip this step
                    self.remove_all_buttons()
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
                    # the most important thing here is to ensure the menu is gracefully stopped while displaying a formatted
                    # error message to the user
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
    
    @ensure_not_primed
    async def start(self, *, send_to: Union[str, int, discord.TextChannel]=None):
        if ViewMenu._sessions_limited:
            can_proceed = await self._handle_session_limits()
            if not can_proceed:
                return
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
            self._refresh_page_director_info(ViewMenu.TypeEmbed, self._pages)

            navigation_btns = [btn for btn in self._buttons if btn.custom_id in ViewButton._base_nav_buttons()]

            # an re search is required here because buttons with ID_CUSTOM_EMBED dont have a normal ID, the ID is "8_[unique ID]"
            custom_embed_btns = [btn for btn in self._buttons if btn.style != discord.ButtonStyle.link and re.search(r'8_\d+', btn.custom_id)]

            if all([not self._pages, not custom_embed_btns]):
                raise NoPages("You cannot start a ViewMenu when you haven't added any pages")

            # normal pages, no custom embeds
            if self._pages and not custom_embed_btns:
                self._msg = await self._handle_send_to(send_to).send(embed=self._pages[0], view=self._view) # allowed_mentions not needed in embeds
            
            # only custom embeds
            elif not self._pages and custom_embed_btns:
                # since there are only custom embeds, there is no need for base navigation buttons, so remove them if any
                for nav_btn in navigation_btns:
                    if nav_btn in self._buttons:
                        self._buttons.remove(nav_btn)
                
                # ensure all custom embed buttons have the proper values set
                for custom_btn in custom_embed_btns:
                    if custom_btn.followup is None or custom_btn.followup.embed is None:
                        raise ViewMenuException('ViewButton custom_id was set as ViewButton.ID_CUSTOM_EMBED but the "followup" kwargs for that ViewButton was not set or the "embed" kwarg for the followup was not set')
                
                # since there are only custom embeds, self._pages is still set to :class:`None`, so set the embed in `.send()` to the first custom embed in the list
                self._msg = await self._handle_send_to(send_to).send(embed=custom_embed_btns[0].followup.embed, view=self._view)
            
            # normal pages and custom embeds
            else:
                # since there are custom embeds, ensure there is at least one base navigation button so they can switch between the normal pages and custom embeds
                if not navigation_btns:
                    error_msg = inspect.cleandoc(
                        """
                        Since you've added pages and custom embeds, there needs to be at least one base navigation button. Without one, there's no way to go back to the normal pages in the menu if a custom embed button is pressed.
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
                    self._msg = await self._handle_send_to(send_to).send(embed=self._pages[0], view=self._view) # allowed_mentions not needed in embeds

        # add row (dynamic menu)
        elif self._menu_type == ViewMenu.TypeEmbedDynamic:
            for data_clump in self._chunks(self._dynamic_data_builder, self.__rows_requested):
                joined_data = '\n'.join(data_clump)
                if len(joined_data) <= 4096:
                    possible_block = f"```{self.wrap_in_codeblock}\n{joined_data}```"
                    embed = discord.Embed() if self.custom_embed is None else self.custom_embed.copy()
                    embed.description = joined_data if not self.wrap_in_codeblock else possible_block
                    self._pages.append(embed)
                else:
                    raise DescriptionOversized('With the amount of data that was received, the embed description is over discords size limit. Lower the amount of "rows_requested" to solve this problem')
            else:
                # set the main/last pages if any
                if any((self._main_page_contents, self._last_page_contents)):
                    self._pages = collections.deque(self._pages)
                    if self._main_page_contents:
                        self._main_page_contents.reverse()
                        self._pages.extendleft(self._main_page_contents)
                    
                    if self._last_page_contents:
                        self._pages.extend(self._last_page_contents)
                
                self._refresh_page_director_info(ViewMenu.TypeEmbedDynamic, self._pages)

                # make sure data has been added to create at least 1 page
                if not self._pages: raise NoPages('You cannot start a ViewMenu when no data has been added')
                
                self._msg = await self._handle_send_to(send_to).send(embed=self._pages[0], view=self._view) # allowed_mentions not needed in embeds
        
        # add page (text menu)
        else:
            if not self._pages:
                raise NoPages("You cannot start a ViewMenu when you haven't added any pages")
            
            self._refresh_page_director_info(ViewMenu.TypeText, self._pages)
            self._msg = await self._handle_send_to(send_to).send(content=self._pages[0], view=self._view, allowed_mentions=self.allowed_mentions)
        
        self._pc = _PageController(self._pages)
        self._is_running = True
        ViewMenu._active_sessions.append(self)
