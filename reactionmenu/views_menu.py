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

import asyncio
import inspect
import random
import re
from typing import List, Optional, Union

import discord
from discord.ext.commands import Context

from . import ViewButton
from .abc import _DEFAULT_STYLE, BaseMenu, _PageController
from .decorators import ensure_not_primed
from .errors import *


class ViewMenu(BaseMenu):
    """A class to create a discord pagination menu using :class:`discord.ui.View`
    
    Parameters
    ----------
    ctx: :class:`discord.ext.commands.Context`
        The Context object. You can get this using a command or if you're in a `discord.on_message` event
    
    menu_type: :class:`int`
        The configuration of the menu. Class variables :attr:`ViewMenu.TypeEmbed`, :attr:`ViewMenu.TypeEmbedDynamic`, or :attr:`ViewMenu.TypeText`
    
    Kwargs
    ------
    all_can_click: :class:`bool`
        Sets if everyone is allowed to control when pages are 'turned' when buttons are pressed (defaults to `False`)
    
    allowed_mentions: :class:`discord.AllowedMentions`
        Controls the mentions being processed in the menu message (defaults to :class:`discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True)`).
        Not valid for `ViewMenu` with a `menu_type` of `TypeText`
    
    custom_embed: :class:`discord.Embed`
        Embed object to use when adding data with :meth:`ViewMenu.add_row()`. Used for styling purposes only (:attr:`ViewMenu.TypeEmbedDynamic` only/defaults to :class:`None`)
    
    delete_interactions: :class:`bool`
        Delete the prompt message by the bot and response message by the user when asked what page they would like to go to when using :attr:`ViewButton.ID_GO_TO_PAGE` (defaults to `True`)
    
    delete_on_timeout: :class:`bool`
        Delete the menu when it times out (defaults to `False`) If `True`, :attr:`disable_buttons_on_timeout` and :attr:`remove_buttons_on_timeout` will not execute regardless of if they are `True`. This takes priority over those actions
    
    disable_buttons_on_timeout: :class:`bool`
        Disable the buttons on the menu when the menu times out (defaults to `True`) If :attr:`delete_on_timeout` is `True`, this will be overridden
    
    name: :class:`str`
        A name you can set for the menu (defaults to :class:`None`)
    
    only_roles: List[:class:`discord.Role`]
        If set, only members with any of the given roles are allowed to control the menu. The menu owner can always control the menu (defaults to :class:`None`)
    
    remove_buttons_on_timeout: :class:`bool`
        Remove the buttons on the menu when the menu times out (defaults to `False`) If :attr:`disable_buttons_on_timeout` is `True`, this will be overridden
    
    rows_requested: :class:`int`
        The amount of information per :meth:`ViewMenu.add_row()` you would like applied to each embed page (:attr:`ViewMenu.TypeEmbedDynamic` only/defaults to :class:`None`)
    
    show_page_director: :class:`bool`
        Shown at the botttom of each embed page. "Page 1/20" (defaults to `True`)
    
    style: :class:`str`
        A custom page director style you can select. "$" represents the current page, "&" represents the total amount of pages (defaults to "Page $/&") Example: `ViewMenu(ctx, ..., style='On $ out of &')`
    
    timeout: Union[:class:`int`, :class:`float`, :class:`None`]
        The timer for when the menu times out. Can be :class:`None` for no timeout (defaults to `60.0`)
    
    wrap_in_codeblock: :class:`str`
        The discord codeblock language identifier to wrap your data in (:attr:`ViewMenu.TypeEmbedDynamic` only/defaults to :class:`None`). Example: `ViewMenu(ctx, ..., wrap_in_codeblock='py')`
    """
    def __init__(self, ctx: Context, *, menu_type: int, **kwargs):
        super().__init__(ctx, menu_type, **kwargs)

        # kwargs
        self.disable_buttons_on_timeout: bool = kwargs.get('disable_buttons_on_timeout', True)
        self.remove_buttons_on_timeout: bool = kwargs.get('remove_buttons_on_timeout', False)
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
    
    def _get_new_view(self) -> discord.ui.View:
        """Returns a new :class:`discord.ui.View` object with the `timeout` parameter already set along with `on_timeout` and `on_error`"""
        new_view = discord.ui.View(timeout=self.timeout)
        new_view.on_timeout = self._on_dpy_view_timeout
        new_view.on_error = self._on_dpy_view_error
        return new_view
    
    @property
    def timeout(self):
        return self.__timeout
    
    @timeout.setter
    def timeout(self, value) -> Union[int, float, None]:
        """A property getter/setter for kwarg `timeout`"""
        if isinstance(value, (int, float, type(None))):
            self._view.timeout = value
            self.__timeout = value
        else:
            raise IncorrectType(f'"timeout" expected int, float, or None, got {value.__class__.__name__}')
    
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
    
    async def _handle_event(self, button: ViewButton):
        """|coro| If an event is set, disable/remove the buttons from the menu when the click requirement has been met"""
        if button.event:
            event_type = button.event.event_type
            event_value = button.event.value
            if button.total_clicks == event_value:
                if event_type == ViewButton.Event._disable:
                    self.disable_button(button)
                
                elif event_type == ViewButton.Event._remove:
                    self.remove_button(button)
                
                await self.refresh_menu_buttons()
    
    def _remove_director(self, page: Union[discord.Embed, str]):
        """Removes the page director contents from the page. This is used for :meth:`ViewMenu.update()`"""
        style = self.style
        if style is None:
            style = _DEFAULT_STYLE
        
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
    
    async def update(self, *, new_pages: Union[List[Union[discord.Embed, str]], None], new_buttons: Union[List[ViewButton], None]) -> None:
        """|coro|
        
        When the menu is running, update the pages or buttons 
        
        Parameters
        ----------
        new_pages: List[Union[:class:`discord.Embed`, :class:`str`]]
            Pages to *replace* the current pages with. If the menus current `menu_type` is :attr:`ViewMenu.TypeEmbed`, only :class:`discord.Embed` can be used. If :attr:`ViewMenu.TypeText`, only :class:`str` can be used. If you
            don't want to replace any pages, set this to :class:`None`
        
        new_buttons: List[:class:`ViewButton`]
            Buttons to *replace* the current buttons with. Can be an empty list if you want the updated menu to have no buttons. Can also be set to :class:`None` if you don't want to replace any buttons
        
        Raises
        ------
        - `ViewMenuException`: The :class:`ViewButton` custom_id was not recognized or a :class:`ViewButton` with that ID has already been added
        - `TooManyButtons`: There are already 25 buttons on the menu
        - `IncorrectType`: The values in :param:`new_pages` did not match the :class:`ViewMenu`'s `menu_type`. An attempt to use this method when the `menu_type` is :attr:`ViewMenu.TypeEmbedDynamic` which is not allowed. Or
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

            self._view.stop()
            self._view = self._get_new_view()

            # re-using current buttons
            if isinstance(new_buttons, type(None)):
                original_buttons = self._buttons.copy()
                self.remove_all_buttons()
                for current_btns in original_buttons:
                    self._bypass_primed = True
                    self.add_button(current_btns)
            
            # using new buttons
            elif isinstance(new_buttons, list):
                self.remove_all_buttons()
                if len(new_buttons) >= 1: # empty lists mean all buttons will be removed
                    for new_btn in new_buttons:
                        self._bypass_primed = True
                        self.add_button(new_btn)
            
            kwargs_to_pass['view'] = self._view
            
            if self._menu_type == ViewMenu.TypeEmbed:
                kwargs_to_pass['embed'] = self._pages[0]
            else:
                kwargs_to_pass['content'] = self._pages[0]
            
            await self._msg.edit(**kwargs_to_pass)
    
    def randomize_button_styles(self) -> None:
        """Set all buttons currently registered to the menu to a random :class:`discord.ButtonStyle` excluding link buttons"""
        all_styles = (
            discord.ButtonStyle.blurple,
            discord.ButtonStyle.green,
            discord.ButtonStyle.gray,
            discord.ButtonStyle.red
        )
        for btn in [button for button in self._buttons if button.style not in (discord.ButtonStyle.link, discord.ButtonStyle.url)]:
            btn.style = random.choice(all_styles)
    
    def set_button_styles(self, style: discord.ButtonStyle) -> None:
        """Set all buttons currently registered to the menu to the specified :class:`discord.ButtonStyle` excluding link buttons
        
        Parameters
        ----------
        style: :class:`discord.ButtonStyle`
            The button style to set
        """
        for btn in [button for button in self._buttons if button.style not in (discord.ButtonStyle.link, discord.ButtonStyle.url)]:
            btn.style = style

    async def refresh_menu_buttons(self) -> None:
        """|coro|
        
        When the menu is running, update the message to reflect the buttons that were removed, enabled, or disabled"""
        if self._is_running:
            current_buttons = self._buttons.copy()
            self.remove_all_buttons()
            self._view.stop()
            self._view = self._get_new_view()
            for btn in current_buttons:
                self._bypass_primed = True
                self.add_button(btn)
            await self._msg.edit(view=self._view)
    
    def remove_button(self, button: ViewButton) -> None:
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
            raise ButtonNotFound('Cannot remove a button that is not registered')
    
    def remove_all_buttons(self) -> None:
        """Remove all buttons from the menu"""
        for btn in self._buttons:
            btn._menu = None
        self._buttons.clear()
        self._view.clear_items()
    
    def disable_button(self, button: ViewButton) -> None:
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
            raise ButtonNotFound('Cannot disable a button that is not registered')
    
    def disable_all_buttons(self) -> None:
        """Disable all buttons on the menu"""
        for btn in self._buttons:
            btn.disabled = True
    
    def enable_button(self, button: ViewButton) -> None:
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
    
    def enable_all_buttons(self) -> None:
        """Enable all buttons on the menu"""
        for btn in self._buttons:
            btn.disabled = False
    
    def _button_add_check(self, button: ViewButton):
        """A set of checks to ensure the proper button is being added"""
        # ensure they are using only the ViewButton and not ReactionMenus :class:`ReactionButton`
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
                if not all([button.custom_id is None, button.style == discord.ButtonStyle.link]):
                    name = ViewButton._get_id_name_from_id(button.custom_id)
                    raise ViewMenuException(f'A ViewButton with custom_id {name!r} has already been added')
            
            # if the menu_type is TypeText, disallow custom embed buttons
            if button.style != discord.ButtonStyle.link and self._menu_type == ViewMenu.TypeText:
                if button.custom_id == ViewButton.ID_CUSTOM_EMBED:
                    if button.followup and button.followup.embed is not None:
                        raise MenuSettingsMismatch('ViewButton with custom_id ViewButton.ID_CUSTOM_EMBED cannot be used when the menu_type is ViewMenu.TypeText')
            
            # if using a skip button, ensure the skip attribute was set
            if button.custom_id == ViewButton.ID_SKIP and button.skip is None:
                raise ViewMenuException('When attempting to add a button custom_id ViewButton.ID_SKIP, the "skip" kwarg was not set')
            
            # ensure there are no more than 25 buttons
            if len(self._buttons) >= 25:
                raise TooManyButtons('ViewMenu cannot have more than 25 buttons (discord limitation)')
        else:
            raise IncorrectType(f'When adding a button to the ViewMenu, the button type must be ViewButton, got {button.__class__.__name__}')
    
    def _maybe_unique_id(self, button: ViewButton):
        """Create a unique ID if the `custom_id` for buttons that are allowed to have duplicates
        
            Note ::
                This excludes link buttons because they don't have a `custom_id`
        """
        if button.custom_id in (ViewButton.ID_CALLER, ViewButton.ID_SEND_MESSAGE, ViewButton.ID_CUSTOM_EMBED, ViewButton.ID_SKIP):
            button.custom_id = f'{button.custom_id}_{id(button)}'
    
    @ensure_not_primed
    def add_button(self, button: ViewButton) -> None:
        """Register a button to the menu
        
        Parameters
        ----------
        button: :class:`ViewButton`
            The button to add
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: The buttons custom_id was set as :attr:`ViewButton.ID_CUSTOM_EMBED` but the `menu_type` is :attr:`ViewMenu.TypeText`
        - `ViewMenuException`: The custom_id for the button was not recognized or a button with that custom_id has already been added
        - `TooManyButtons`: There are already 25 buttons on the menu
        - `IncorrectType`: Parameter :param:`button` was not of type :class:`ViewButton`
        """
        self._button_add_check(button)
        self._maybe_unique_id(button)

        button._menu = self
        self._view.add_item(button)
        self._buttons.append(button)
    
    def get_button(self, identity: str, *, search_by: str='label') -> List[ViewButton]:
        """Get a button that has been registered to the menu by it's label, custom_id, or name
        
        Parameters
        ----------
        identity: :class:`str`
            The button label, custom_id, or name
        
        search_by: :class:`str`
            How to search for the button. If "label", it's searched by button labels. If "id", it's searched by it's custom_id. 
            If "name", it's searched by button names
        
        Returns
        -------
        List[:class:`ViewButton`]: The button(s) matching the given identity
        
        Raises
        ------
        - `ViewMenuException`: Parameter :param:`search_by` was not "label", "id", or "name"
        """
        identity = str(identity)
        search_by = str(search_by).lower()

        if search_by == 'label':
            matched_labels: List[ViewButton] = [btn for btn in self._buttons if btn.label and btn.label == identity]
            return matched_labels
        
        elif search_by == 'id':
            matched_ids: List[ViewButton] = [btn for btn in self._buttons if btn.custom_id and btn.custom_id.startswith(identity)]
            return matched_ids
        
        elif search_by == 'name':
            matched_names: List[ViewButton] = [btn for btn in self._buttons if btn.name and btn.name == identity]
            return matched_names
        
        else:
            raise ViewMenuException(f'Parameter "search_by" expected "label", "id", or "name", got {search_by!r}')

    async def _paginate(self, button: ViewButton, inter: discord.Interaction):
        """When the button is pressed, handle the pagination process"""
        if not self._check(inter):
            await inter.response.defer()
            return
        
        button._update_statistics(inter.user)
        await self._handle_event(button)
        
        if button.custom_id == ViewButton.ID_PREVIOUS_PAGE:
            await inter.response.edit_message(**self._determine_kwargs(self._pc.prev()))
        
        elif button.custom_id == ViewButton.ID_NEXT_PAGE:
            await inter.response.edit_message(**self._determine_kwargs(self._pc.next()))
        
        elif button.custom_id == ViewButton.ID_GO_TO_FIRST_PAGE:
            await inter.response.edit_message(**self._determine_kwargs(self._pc.first_page()))
        
        elif button.custom_id == ViewButton.ID_GO_TO_LAST_PAGE:
            await inter.response.edit_message(**self._determine_kwargs(self._pc.last_page()))
        
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
                    await self._msg.edit(**self._determine_kwargs(self._pc.current_page))
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
                # inter.followup.send() is used instead
                await inter.response.defer()

                sent_message: discord.WebhookMessage = await inter.followup.send(**followup_kwargs)
                if button.followup.delete_after:
                    await sent_message.delete(delay=button.followup.delete_after)
            
            elif button.custom_id.startswith(ViewButton.ID_CUSTOM_EMBED):
                if self._menu_type not in (ViewMenu.TypeEmbed, ViewMenu.TypeEmbedDynamic):
                    raise ViewMenuException('Buttons with custom_id ViewButton.ID_CUSTOM_EMBED can only be used when the menu_type is ViewMenu.TypeEmbed or ViewMenu.TypeEmbedDynamic')
                else:
                    if button.followup is None or button.followup.embed is None:
                        raise ViewMenuException('ViewButton custom_id was set as ViewButton.ID_CUSTOM_EMBED but the "followup" kwargs for that ViewButton was not set or the "embed" kwarg for the followup was not set')
                   
                    await inter.response.edit_message(embed=button.followup.embed)            
            
            elif button.custom_id.startswith(ViewButton.ID_SKIP):
                await inter.response.edit_message(**self._determine_kwargs(self._pc.skip(button.skip)))
            
            else:
                # this shouldn't execute because of :meth:`_button_add_check`, but just in case i missed something, raise the appropriate error
                raise ViewMenuException(f'ViewButton custom_id {button.custom_id!r} was not recognized')

        await self._contact_relay(inter.user, button)

    async def stop(self, *, delete_menu_message: bool=False, remove_buttons: bool=False, disable_buttons: bool=False) -> None:
        """|coro|
        
        Stops the process of the menu with the option of deleting the menu's message, removing the buttons, or disabling the buttons upon stop
        
        Parameters
        ----------
        delete_menu_message: :class:`bool`
            Delete the message the menu is operating from

        remove_buttons: :class:`bool`
            Remove the buttons from the menu

        disable_buttons: :class:`bool`
            Disable the buttons on the menu

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
                
                await self._handle_on_timeout()
    
    @ensure_not_primed
    async def start(self, *, send_to: Optional[Union[str, int, discord.TextChannel]]=None, reply: bool=False) -> None:
        """|coro|
        
        Start the menu
        
        Parameters
        ----------
        send_to: Optional[Union[:class:`str`, :class:`int`, :class:`discord.TextChannel`]]
            The channel you'd like the menu to start in. Use the channel name, ID, or it's object. Please note that if you intend to use a text channel object, using
            method :meth:`discord.Client.get_channel()` (or any other related methods), that text channel should be in the same list as if you were to use `ctx.guild.text_channels`. This only works on a context guild text channel basis. That means a menu instance cannot be
            created in one guild and the menu itself (:param:`send_to`) be sent to another. Whichever guild context the menu was instantiated in, the text channels of that guild are the only options for :param:`send_to`
        
        reply: :class:`bool`
			Enables the menu message to reply to the message that triggered it. Parameter :param:`send_to` must be :class:`None` if this is `True`
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `NoPages`: The menu was started when no pages have been added
        - `NoButtons`: Attempted to start the menu when no Buttons have been registered
        - `ViewMenuException`: The :class:`ViewMenu`'s `menu_type` was not recognized. There were more than one base navigation buttons. Or a :attr:`ViewButton.ID_CUSTOM_EMBED` button was not correctly formatted
        - `DescriptionOversized`: When using a `menu_type` of :attr:`ViewMenu.TypeEmbedDynamic`, the embed description was over discords size limit
        - `IncorrectType`: Parameter :param:`send_to` was not :class:`str`, :class:`int`, or :class:`discord.TextChannel`
        - `MenuException`: The channel set in :param:`send_to` was not found
        """
        if ViewMenu._sessions_limited:
            can_proceed = await self._handle_session_limits()
            if not can_proceed:
                return
        # checks
        # Note 1: each at least 1 page check is done in it's own if statement to avoid clashing between pages and custom embeds
        # Note 2: at least 1 page check for add_row is done in "(dynamic menu)"
        
        # ensure at least 1 button exists before starting the menu
        if not self._buttons: raise NoButtons
        if self._menu_type not in ViewMenu._all_menu_types(): raise ViewMenuException('ViewMenu menu_type not recognized')

        reply_kwargs = self._handle_reply_kwargs(send_to, reply)

        # add page (normal menu)
        if self._menu_type == ViewMenu.TypeEmbed:
            self._refresh_page_director_info(ViewMenu.TypeEmbed, self._pages)

            navigation_btns = [btn for btn in self._buttons if btn.custom_id in ViewButton._base_nav_buttons()]

            # an re search is required here because buttons with ID_CUSTOM_EMBED dont have a normal ID, the ID is "8_[unique ID]"
            custom_embed_btns = [btn for btn in self._buttons if btn.style != discord.ButtonStyle.link and re.search(r'8_\d+', btn.custom_id)]

            if all([not self._pages, not custom_embed_btns]):
                raise NoPages

            # normal pages, no custom embeds
            if self._pages and not custom_embed_btns:
                self._msg = await self._handle_send_to(send_to).send(embed=self._pages[0], view=self._view, **reply_kwargs) # allowed_mentions not needed in embeds
            
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
                self._msg = await self._handle_send_to(send_to).send(embed=custom_embed_btns[0].followup.embed, view=self._view, **reply_kwargs)
            
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
                    self._msg = await self._handle_send_to(send_to).send(embed=self._pages[0], view=self._view, **reply_kwargs) # allowed_mentions not needed in embeds

        # add row (dynamic menu)
        elif self._menu_type == ViewMenu.TypeEmbedDynamic:
            await self._build_dynamic_pages(send_to)
        
        # add page (text menu)
        else:
            if not self._pages:
                raise NoPages
            
            self._refresh_page_director_info(ViewMenu.TypeText, self._pages)
            self._msg = await self._handle_send_to(send_to).send(content=self._pages[0], view=self._view, allowed_mentions=self.allowed_mentions, **reply_kwargs)
        
        self._pc = _PageController(self._pages)
        self._is_running = True
        ViewMenu._active_sessions.append(self)
