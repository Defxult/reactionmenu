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

import asyncio
import collections
import inspect
import random
import re
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    Final,
    List,
    Literal,
    NamedTuple,
    NoReturn,
    Optional,
    Sequence,
    Union,
    overload
)

if TYPE_CHECKING:
    from .abc import MenuType

import discord
from discord.ext.commands import Context

from . import ViewButton
from .abc import (
    _DEFAULT_STYLE,
    DEFAULT_BUTTONS,
    Page,
    _BaseMenu,
    _PageController
)

from .decorators import ensure_not_primed
from .errors import *

_SelectOptionRelayPayload = collections.namedtuple('_SelectOptionRelayPayload', ['func', 'only'])

class ViewSelect(discord.ui.Select):
    """A class to assist in the process of categorizing information on a :class:`ViewMenu`

    Parameters
    ----------
    title: Union[:class:`str`, `None`]
        The category name. If `None`, the category name defaults to "Select a category"
    
    options: Dict[:class:`discord.SelectOption`, List[:class:`Page`]]
        A key/value pair associating the category options with pages to navigate
    
    disabled: :class:`bool`
        If the select should start enabled or disabled

        .. added:: v3.1.0
    """
    def __init__(self, *, title: Union[str, None], options: Dict[discord.SelectOption, List[Page]], disabled: bool=False) -> None:
        self._menu: Optional[ViewMenu] = None
        self._view_select_options = options
        
        super().__init__(custom_id=discord.utils.MISSING, placeholder='Select a category' if title is None else title, min_values=1, max_values=1, options=options.keys(), disabled=disabled, row=None) # type: ignore
    
    def __repr__(self) -> str:
        return f'<ViewSelect title={self.placeholder!r} disabled={self.disabled}>'
    
    @property
    def menu(self) -> Optional[ViewMenu]:
        """
        Returns
        -------
        Optional[:class:`ViewMenu`]: The menu this select is attached to. Can be `None` if not attached to any menu
        """
        return self._menu
    
    async def __dispatch_relay(self, interaction: discord.Interaction) -> None:
        if self._menu:
            relay_info = self._menu._options_relay_info
            if relay_info is not None:
                SelectOptionRelayPayload = collections.namedtuple('SelectOptionRelayPayload', ['member', 'option', 'menu'])
                CLICKED_OPTION: Final[str] = self.values[0]
                
                # Find which :class:`discord.SelectOption` was clicked
                filtered_options = [sel for sel in self._view_select_options if sel.label == CLICKED_OPTION]
                select_option = filtered_options[0]
                payload = SelectOptionRelayPayload(member=interaction.user, option=select_option, menu=self._menu)

                async def call():
                    if asyncio.iscoroutinefunction(relay_info.func):
                        await relay_info.func(payload)
                    else:
                        relay_info.func(payload)
                
                if relay_info.only:
                    for option_label in relay_info.only:
                        if CLICKED_OPTION == option_label:
                            await call()
                            break
                else:
                    if filtered_options:
                        await call()
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """*INTERNAL USE ONLY* - The callback function from the select interaction. This should not be manually called"""
        for option, pages in self._view_select_options.items():
            if option.label == self.values[0]:
                if self._menu:
                    self._menu._pc = _PageController(pages)
                    first_page = self._menu._pc.first_page()
                    await interaction.response.edit_message(**self._menu._determine_kwargs(first_page))
                    break
        await self.__dispatch_relay(interaction)

    class GoTo(discord.ui.Select):
        """Represents a UI based version of a :class:`ViewButton` with the ID `ViewButton.ID_GO_TO_PAGE`

        Parameters
        ----------
        title: Union[:class:`str`, `None`]
            The selects name. If `None`, the name defaults to "Navigate to page..."
        
        page_numbers: This parameter accepts 3 different types and are explained below
        - List[:class:`int`]
            - If set to a list of integers, those specified values are the only options that are available when the select is clicked
        
        - Dict[:class:`int`, Union[:class:`str`, :class:`discord.Emoji`, :class:`discord.PartialEmoji`]]
            - You can use this type if you'd like to utilize emojis in your select options
        
        - `ellipsis`
            - Set an ellipsis to have the library automatically assign all page numbers to the amount of pages that you've added to the menu.
            
        NOTE: Setting the `page_numbers` parameter to an ellipsis (...) only works as intended if you've added the go to select AFTER you've added pages to the menu
        
            .. added:: v3.1.0
        """
        def __init__(self, *, title: Union[str, None], page_numbers: Union[List[int], Dict[int, Union[str, discord.Emoji, discord.PartialEmoji]], ellipsis]) -> None:
            self.callback = self._select_go_to_callback
            self._menu: Optional[ViewMenu] = None
            self._page_numbers = page_numbers
            self._gt_options: List[discord.SelectOption] = []
            
            if isinstance(page_numbers, list):
                self._gt_options.extend([discord.SelectOption(label=str(n)) for n in page_numbers])
            elif isinstance(page_numbers, dict):
                for n, emoji in page_numbers.items():
                    self._gt_options.append(discord.SelectOption(label=str(n), emoji=emoji))
            
            super().__init__(placeholder="Navigate to page..." if title is None else str(title), options=self._gt_options)
        
        @property
        def menu(self) -> Optional[ViewMenu]:
            """
            Returns
            -------
            Optional[:class:`ViewMenu`]: The menu this select is attached to. Can be `None` if not attached to any menu
            """
            return self._menu
        
        async def _select_go_to_callback(self, interaction: discord.Interaction) -> None:
            if self._menu._check(interaction): # type: ignore
                if interaction.data:
                    values = interaction.data.get('values') 
                    if values:
                        CLICKED_OPTION: Final[int] = int(values[0])
                        if self._menu:
                            if 1 <= CLICKED_OPTION <= self._menu._pc.total_pages + 1:
                                self._menu._pc.index = CLICKED_OPTION - 1
                                await interaction.response.edit_message(**self._menu._determine_kwargs(self._menu._pc.current_page))
                                return
                else:
                    assert False, "No interaction data"
            else:
                await interaction.response.defer()

class ViewMenu(_BaseMenu):
    """A class to create a discord pagination menu using :class:`discord.ui.View`
    
    Parameters
    ----------
    method: Union[:class:`discord.ext.commands.Context`, :class:`discord.Interaction`]
        The Context object. You can get this using a command or if you're in a `discord.on_message` event. Also accepts interactions, typically received when using slash commands
    
    menu_type: :class:`MenuType`
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
        Delete the menu when it times out (defaults to `False`) If `True`, :attr:`disable_items_on_timeout` and :attr:`remove_items_on_timeout` will not execute regardless of if they are `True`. This takes priority over those actions
    
    disable_items_on_timeout: :class:`bool`
        Disable the buttons on the menu when the menu times out (defaults to `True`) If :attr:`delete_on_timeout` is `True`, this will be overridden
    
    name: :class:`str`
        A name you can set for the menu (defaults to :class:`None`)
    
    only_roles: List[:class:`discord.Role`]
        If set, only members with any of the given roles are allowed to control the menu. The menu owner can always control the menu (defaults to :class:`None`)
    
    remove_items_on_timeout: :class:`bool`
        Remove the buttons on the menu when the menu times out (defaults to `False`) If :attr:`disable_items_on_timeout` is `True`, this will be overridden
    
    rows_requested: :class:`int`
        The amount of information per :meth:`ViewMenu.add_row()` you would like applied to each embed page (:attr:`ViewMenu.TypeEmbedDynamic` only/defaults to :class:`None`)
    
    show_page_director: :class:`bool`
        Shown at the bottom of each embed page. "Page 1/20" (defaults to `True`)
    
    style: :class:`str`
        A custom page director style you can select. "$" represents the current page, "&" represents the total amount of pages (defaults to "Page $/&") Example: `ViewMenu(ctx, ..., style='On $ out of &')`
    
    timeout: Union[:class:`int`, :class:`float`, :class:`None`]
        The timer for when the menu times out. Can be :class:`None` for no timeout (defaults to `60.0`)
    
    wrap_in_codeblock: :class:`str`
        The discord codeblock language identifier to wrap your data in (:attr:`ViewMenu.TypeEmbedDynamic` only/defaults to :class:`None`). Example: `ViewMenu(ctx, ..., wrap_in_codeblock='py')`
    """
    
    _active_sessions: List[ViewMenu] = []
    
    def __init__(self, method: Union[Context, discord.Interaction], /, *, menu_type: MenuType, **kwargs):
        super().__init__(method, menu_type, **kwargs)

        self.__buttons: List[ViewButton] = []
        self._stop_initiated = False

        # kwargs
        self.disable_items_on_timeout: bool = kwargs.get('disable_items_on_timeout', True)
        self.remove_items_on_timeout: bool = kwargs.get('remove_items_on_timeout', False)
        self.__timeout: Union[int, float, None] = kwargs.get('timeout', 60.0) # property get/set

        # view
        self.__view = discord.ui.View(timeout=self.__timeout)
        self.__view.on_timeout = self._on_dpy_view_timeout
        self.__view.on_error = self._on_dpy_view_error

        # select
        self.__selects: List[ViewSelect] = []
        self._options_relay_info: Optional[_SelectOptionRelayPayload] = None
        self._gotos: List[ViewSelect.GoTo] = []
    
    def __repr__(self):
        return f'<ViewMenu name={self.name!r} owner={str(self._extract_proper_user(self._method))!r} is_running={self._is_running} timeout={self.timeout} menu_type={self._menu_type.name}>'

    async def _on_dpy_view_timeout(self) -> None:
        self._menu_timed_out = True
        await self.stop(delete_menu_message=self.delete_on_timeout, disable_items=self.disable_items_on_timeout, remove_items=self.remove_items_on_timeout) 
    
    async def _on_dpy_view_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> NoReturn:
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
    def selects(self) -> List[ViewSelect]:
        """
        Returns
        -------
        List[:class:`ViewSelect`]: All selects that have been added to the menu
        
            .. added:: v3.1.0
        """
        return self.__selects
    
    @property
    def go_to_selects(self) -> List[ViewSelect.GoTo]:
        """
        Returns
        -------
        List[:class:`ViewSelect.GoTo`]: All go to selects that have been added to the menu
        
            .. added:: v3.1.0
        """
        return self._gotos
    
    @property
    def timeout(self):
        return self.__timeout
    
    @timeout.setter
    def timeout(self, value) -> Union[int, float, None]:
        """A property getter/setter for kwarg `timeout`"""
        if isinstance(value, (int, float, type(None))):
            self.__view.timeout = value
            self.__timeout = value
        else:
            raise IncorrectType(f'"timeout" expected int, float, or None, got {value.__class__.__name__}')
        
    @property
    def buttons(self) -> List[ViewButton]:
        """
        Returns
        -------
        List[:class:`ViewButton`]: All buttons that have been added to the menu
        """
        return self.__buttons
    
    @property
    def buttons_most_clicked(self) -> List[ViewButton]:
        """
        Returns
        -------
        List[:class:`ViewButton`]: The list of buttons on the menu ordered from highest (button with the most clicks) to lowest (button with the least clicks). Can be an empty list if there are no buttons registered to the menu
        """
        return self._sort_buttons(self.__buttons)
    
    @classmethod
    async def quick_start(cls, method: Union[Context, discord.Interaction], /, pages: Sequence[Union[discord.Embed, str]], buttons: Optional[Sequence[ViewButton]]=DEFAULT_BUTTONS) -> ViewMenu:
        """|coro class method|
        
        Start a menu with default settings either with a `menu_type` of `ViewMenu.TypeEmbed` (all values in `pages` are of type `discord.Embed`) or `ViewMenu.TypeText` (all values in `pages` are of type `str`)

        Parameters
        ----------
        method: Union[:class:`discord.ext.commands.Context`, :class:`discord.Interaction`]
            The Context object. You can get this using a command or if you're in a `discord.on_message` event. Also accepts interactions, typically received when using slash commands

        pages: Sequence[Union[:class:`discord.Embed`, :class:`str`]]
            The pages to add

        buttons: Optional[Sequence[:class:`ViewButton`]]
            The buttons to add. If left as `DEFAULT_BUTTONS`, that is equivalent to `ViewButton.all()`
        
        Returns
        -------
        :class:`ViewMenu`: The menu that was started
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `NoPages`: The menu was started when no pages have been added
        - `NoButtons`: Attempted to start the menu when no Buttons have been registered
        - `IncorrectType`: All items in :param:`pages` were not of type :class:`discord.Embed` or :class:`str`
        
            .. added v3.1.0
        """
        menu = cls(method, menu_type=cls._quick_check(pages))
        menu.add_pages(pages) # type: ignore
        menu.add_buttons(ViewButton.all() if buttons is DEFAULT_BUTTONS else buttons) # type: ignore
        await menu.start()
        return menu
    
    def _should_persist(self, button: ViewButton) -> bool:
        """Determine if a link button should stay enabled/remain on the menu when it times out or is stopped

            .. added:: v3.1.0
        """
        return True if all([
            button.custom_id is None,
            button.url,
            button.persist,
            self._stop_initiated
        ]) else False
    
    def _check(self, inter: discord.Interaction) -> bool:
        """Base menu button interaction check. Verifies who (user, everyone, or role) can interact with the button"""
        author_pass = False
        if self._extract_proper_user(inter).id == self.owner.id: author_pass = True
        if self.only_roles: self.all_can_click = False

        if self.only_roles:
            for role in self.only_roles:
                if role in inter.user.roles: # type: ignore / will be :class:`discord.Member`. :attr:`only_roles` will always be `None` because of overridden DM settings so this line will never be reached
                    author_pass = True
                    break
        if self.all_can_click:
            author_pass = True

        return author_pass
    
    async def _handle_event(self, button: ViewButton) -> None:
        """|coro| If an event is set, disable/remove the buttons from the menu when the click requirement has been met"""
        if button.event:
            event_type = button.event.event_type
            event_value = button.event.value
            if button.total_clicks == event_value:
                if event_type == ViewButton.Event._DISABLE:
                    self.disable_button(button)
                
                elif event_type == ViewButton.Event._REMOVE:
                    self.remove_button(button)
                
                await self.refresh_menu_items()
    
    def _remove_director(self, page: Page) -> Page:
        """Removes the page director contents from the page. This is used for :meth:`ViewMenu.update()`"""
        style = self.style
        if style is None:
            style = _DEFAULT_STYLE
        
        escaped_style = re.escape(style)
        STYLE_PATTERN = escaped_style.replace(r'\$', r'\d{1,}').replace(r'\&', r'\d{1,}')
        STYLE_STR_PATTERN = escaped_style.replace(r'\$', r'\d{1,}').replace(r'\&', r'(\d{1,}.*)')
        
        if self.show_page_director:
            # TypeEmbed
            if isinstance(page.embed, discord.Embed) and self._menu_type == ViewMenu.TypeEmbed:
                embed = page.embed
                if embed.footer.text:
                    DIRECTOR_PATTERN = STYLE_PATTERN + r':? '
                    if re.search(DIRECTOR_PATTERN, embed.footer.text):
                        embed.set_footer(text=re.sub(DIRECTOR_PATTERN, '', embed.footer.text), icon_url=embed.footer.icon_url)
                
                return page
            
            # TypeText
            elif isinstance(page.content, str) and self._menu_type == ViewMenu.TypeText:
                if re.search(STYLE_STR_PATTERN, page.content):
                    page.content = re.sub(STYLE_STR_PATTERN, '', page.content).rstrip('\n')
                
                return page

            else:
                raise TypeError(f'_remove_director parameter "page" expected discord.Embed or str, got {page.__class__.__name__}')
        else:
            return page
    
    def set_select_option_relay(self, func: Callable[[NamedTuple], None], *, only: Optional[Sequence[str]]=None) -> None:
        """Set a function to be called with a given set of information when a select option is pressed on the menu. The information passed is `SelectOptionRelayPayload`, a named tuple.
        The named tuple contains the following attributes:

        - `member`: The :class:`discord.Member` object of the person who pressed the option. Could be :class:`discord.User` if the menu was started in a DM
        - `option`: The :class:`discord.SelectOption` that was pressed
        - `menu`: An instance of :class:`ViewMenu` that the select option is operating under

        Parameters
        ----------
        func: Callable[[:class:`NamedTuple`], :class:`None`]
            The function should only contain a single positional argument. Command functions (`@bot.command()`) not supported

        only: Optional[Sequence[:class:`str`]]
            A sequence of :class:`discord.SelectOption` labels associated with the current menu instance. If this is :class:`None`, all select options on the menu will be relayed.
            If set, only presses from the options matching the given labels specified will be relayed

        Raises
        ------
        - `IncorrectType`: The :param:`func` argument provided was not callable
        
            .. added:: v3.1.0
        """
        
        if callable(func):
            self._options_relay_info = _SelectOptionRelayPayload(func, only)
        else:
            raise IncorrectType('When setting the relay for a select option, argument "func" must be callable')
    
    def remove_select_option_relay(self) -> None:
        """Remove the select option relay that's been set
        
            .. added:: v3.1.0
        """
        self._options_relay_info = None
    
    @ensure_not_primed
    def add_select(self, select: ViewSelect) -> None:
        """Add a select category to the menu

        Parameters
        ----------
        select: :class:`ViewSelect`
            The category listing to add
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `ViewMenuException`:  The `menu_type` was not of :attr:`TypeEmbed`. The "embed" parameter in a :class:`Page` was not set. Or both :class:`ViewSelect` and a :class:`ViewSelect.GoTo` were being used

            .. added:: v3.1.0
        """
        if self._gotos:
            raise ViewMenuException('Category selects cannot be used in conjunction with go to selects')
        
        pages = select._view_select_options.values()
        for all_pages in pages:
            for individual_page in all_pages:
                if not individual_page.embed:
                    raise ViewMenuException("The 'embed' parameter in a Page must be set when using selects")
        else:
            if self._menu_type == ViewMenu.TypeEmbed:
                select._menu = self

                # prevent default select options (https://github.com/Defxult/reactionmenu/issues/55)
                for option in select.options:
                    if option.default:
                        option.default = False
                
                self.__view.add_item(select)
                self.__selects.append(select)
            else:
                raise ViewMenuException('Selects can only be added when the menu_type is TypeEmbed')
    
    def remove_select(self, select: ViewSelect) -> None:
        """Remove a select from the menu
        
        Parameters
        ----------
        select: :class:`ViewSelect`
            The select to remove
        
        Raises
        ------
        - `SelectNotFound`: The provided select was not found in the list of selects on the menu
        
            .. added:: v3.1.0
        """
        if select in self.__selects:
            select._menu = None
            self.__view.remove_item(select)
            self.__selects.remove(select)
        else:
            raise SelectNotFound('Cannot remove a select that is not registered')
    
    def remove_all_selects(self) -> None:
        """Remove all selects from the menu
        
            .. added:: v3.1.0
        """
        while self.__selects:
            self.remove_select(self.__selects[0])

    def disable_select(self, select: ViewSelect) -> None:
        """Disable a select on the menu
        
        Parameters
        ----------
        select: :class:`ViewSelect`
            The select to disable
        
        Raises
        ------
        - `SelectNotFound`: The provided select was not found in the list of selects on the menu
        
            .. added:: v3.1.0
        """
        if select in self.__selects:
            select.disabled = True
        else:
            raise SelectNotFound('Cannot disable a select that is not registered')
    
    def disable_all_selects(self) -> None:
        """Disable all selects on the menu
        
            .. added:: v3.1.0
        """
        for select in self.__selects:
            select.disabled = True
    
    def enable_select(self, select: ViewSelect) -> None:
        """Enable the specified select
        
        Parameters
        ----------
        select: :class:`ViewSelect`
            The select to enable
        
        Raises
        ------
        - `SelectNotFound`: The provided select was not found in the list of selects on the menu
        
            .. added:: v3.1.0
        """
        if select in self.__selects:
            select.disabled = False
        else:
            raise SelectNotFound('Cannot enable a select that is not registered')
    
    def enable_all_selects(self) -> None:
        """Enable all selects on the menu
        
            .. added:: v3.1.0
        """
        for select in self.__selects:
            self.enable_select(select)
    
    @overload
    def get_select(self, title: str) -> List[ViewSelect]:
        ...
    
    @overload
    def get_select(self, title: None) -> List[ViewSelect]:
        ...
    
    def get_select(self, title: Union[str, None]) -> List[ViewSelect]:
        """Get a select by it's title (category name) that has been registered to the menu
        
        Parameters
        ----------
        title: Union[:class:`str`, `None`]
            Title of the category
        
        Returns
        -------
        List[:class:`ViewSelect`]: All selects matching the given title
        """
        return [select for select in self.__selects if select.placeholder == title]
    
    @ensure_not_primed
    def add_go_to_select(self, goto: ViewSelect.GoTo) -> None:
        """Add a select where the user can choose which page they'd like to navigate to.

        Parameters
        ----------
        goto: :class:`ViewSelect.GoTo`
            The navigation listing
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `ViewMenuException`:  A :class:`ViewSelect` was already added to the menu. A :class:`ViewSelect` and a :class:`ViewSelect.GoTo` cannot both be used on a single menu 

            .. added:: v3.1.0
        """
        if not self.__selects:
            goto._menu = self
            if goto._page_numbers is ...:
                for n in range(1, len(self._pages) + 1):
                    goto._gt_options.append(discord.SelectOption(label=str(n)))
            self._gotos.append(goto)
            self.__view.add_item(goto)
        else:
            raise ViewMenuException('Category selects cannot be used in conjunction with go to selects')
    
    def enable_go_to_select(self, goto: ViewSelect.GoTo) -> None:
        """Enable the specified go to select

        Parameters
        ----------
        goto: :class:`ViewSelect.GoTo`
            The go to select to enable
        
            .. added:: v3.1.0
        """
        if goto in self._gotos:
            goto.disabled = False
    
    def enable_all_go_to_selects(self) -> None:
        """Enable all go to selects
        
            .. added:: v3.1.0
        """
        for goto in self._gotos:
            goto.disabled = False
    
    def disable_go_to_select(self, goto: ViewSelect.GoTo) -> None:
        """Disable the specified go to select

        Parameters
        ----------
        goto: :class:`ViewSelect.GoTo`
            The go to select to disable
        
            .. added:: v3.1.0
        """
        if goto in self._gotos:
            goto.disabled = True
    
    def disable_all_go_to_selects(self) -> None:
        """Disable all go to selects
        
            .. added:: v3.1.0
        """
        for goto in self._gotos:
            goto.disabled = True
    
    def remove_go_to_select(self, goto: ViewSelect.GoTo) -> None:
        """Remove a go to select from the menu
        
        Parameters
        ----------
        goto: :class:`ViewSelect.GoTo`
            The go to select to remove
        
        Raises
        ------
        - `SelectNotFound`: The provided go to select was not found in the list of selects on the menu
        
            .. added:: v3.1.0
        """
        if goto in self._gotos:
            goto._menu = None
            self.__view.remove_item(goto)
            self._gotos.remove(goto)
        else:
            raise SelectNotFound('Cannot remove a go to select that is not registered')

    def remove_all_go_to_selects(self) -> None:
        """Remove all go to selects from the menu
        
            .. added:: v3.1.0
        """
        while self._gotos:
            self.remove_go_to_select(self._gotos[0])
    
    async def update(self, *, new_pages: Union[List[Union[discord.Embed, str]], None], new_buttons: Union[List[ViewButton], None]) -> None:
        """|coro|
        
        When the menu is running, update the pages or buttons. It should be noted that `ViewSelect`s are not supported here, and they will automatically be removed
        once the menu is updated. This method only supports pages and buttons.
        
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
                # TypeEmbed
                if self._menu_type == ViewMenu.TypeEmbed:
                    for new_embed_page in new_pages:
                        self._remove_director(Page(embed=new_embed_page)) # type: ignore / contains embed if TypeEmbed
                    
                    self._pages = [Page(embed=e) for e in new_pages.copy()] # type: ignore
                    self._pc = _PageController(self._pages)
                    self._refresh_page_director_info(ViewMenu.TypeEmbed, self._pages)
                
                # TypeText
                else:
                    removed_director_info: List[Page] = []
                    for new_str_page in new_pages.copy():
                        removed_director_info.append(self._remove_director(Page(content=new_str_page))) # type: ignore
                    
                    self._pages = removed_director_info.copy()
                    self._pc = _PageController(self._pages)
                    self._refresh_page_director_info(ViewMenu.TypeText, self._pages)
            else:
                # page controller needs to be reset because even though there are no new pages. the page index is still in the location BEFORE the update
                # EXAMPLE: 5 page menu > click Next button  (on page 2) > update menu no new pages > click Next button (on page 3)
                # that makes no sense and resetting the page controller fixes that issue 
                self._pc = _PageController(self._pages)
            
            kwargs_to_pass = {}
            self.remove_all_selects()

            self.__view.stop()
            self.__view = self._get_new_view()

            # re-using current buttons
            if isinstance(new_buttons, type(None)):
                original_buttons = self.__buttons.copy()
                self.remove_all_buttons()
                for orig_button in original_buttons:
                    self._bypass_primed = True
                    self.add_button(orig_button)
            
            # using new buttons
            elif isinstance(new_buttons, list):
                self.remove_all_buttons()
                if len(new_buttons) >= 1: # empty lists mean all buttons will be removed
                    for new_btn in new_buttons:
                        self._bypass_primed = True
                        self.add_button(new_btn)
            
            kwargs_to_pass['view'] = self.__view
            
            if self._menu_type == ViewMenu.TypeEmbed:
                kwargs_to_pass['embed'] = self._pages[0].embed
            else:
                kwargs_to_pass['content'] = self._pages[0].content
            
            await self._msg.edit(**kwargs_to_pass)
    
    def randomize_button_styles(self) -> None:
        """Set all buttons currently registered to the menu to a random :class:`discord.ButtonStyle` excluding link buttons"""
        all_styles = (
            discord.ButtonStyle.blurple,
            discord.ButtonStyle.green,
            discord.ButtonStyle.gray,
            discord.ButtonStyle.red
        )
        for btn in [button for button in self.__buttons if button.style not in (discord.ButtonStyle.link, discord.ButtonStyle.url)]:
            btn.style = random.choice(all_styles)
    
    def set_button_styles(self, style: discord.ButtonStyle) -> None:
        """Set all buttons currently registered to the menu to the specified :class:`discord.ButtonStyle` excluding link buttons
        
        Parameters
        ----------
        style: :class:`discord.ButtonStyle`
            The button style to set
        """
        for btn in [button for button in self.__buttons if button.style not in (discord.ButtonStyle.link, discord.ButtonStyle.url)]:
            btn.style = style
    
    async def refresh_menu_items(self) -> None:
        """|coro|
        
        When the menu is running, update the message to reflect the buttons/selects that were removed, enabled, or disabled
        """
        if self._is_running:
            current_items = self.__view.children.copy()
            self.remove_all_buttons()
            self.remove_all_selects()
            self.remove_all_go_to_selects()
            self.__view.stop()
            self.__view = self._get_new_view()
            for item in current_items:
                self._bypass_primed = True
                if isinstance(item, discord.ui.Select):
                    if item.__class__.__name__ == "ViewSelect":
                        self.add_select(item) # type: ignore / it's subclassed
                    elif item.__class__.__name__ == "GoTo":
                        self.add_go_to_select(item) # type: ignore / it's subclassed
                elif isinstance(item, ViewButton):
                    self.add_button(item)
                elif isinstance(item, ViewSelect.GoTo):
                    self.add_go_to_select(item)
            await self._msg.edit(view=self.__view)
    
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
        if button in self.__buttons:
            button._menu = None
            self.__buttons.remove(button)
            self.__view.remove_item(button)
        else:
            raise ButtonNotFound('Cannot remove a button that is not registered')
    
    def remove_all_buttons(self) -> None:
        """Remove all buttons from the menu"""
        # Set persists
        persistent_link_buttons: List[ViewButton] = []
        for btn in self.__buttons:
            if self._should_persist(btn):
                persistent_link_buttons.append(btn)
                continue
        else:
            while self.__buttons:
                self.remove_button(self.__buttons[0])
            else:
                for plb in persistent_link_buttons:
                    self._bypass_primed = True
                    self.add_button(plb)
    
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
        if button in self.__buttons:
            idx = self.__buttons.index(button)
            self.__buttons[idx].disabled = True
        else:
            raise ButtonNotFound('Cannot disable a button that is not registered')
    
    def disable_all_buttons(self) -> None:
        """Disable all buttons on the menu"""
        for btn in self.__buttons:
            if self._should_persist(btn): continue
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
        if button in self.__buttons:
            idx = self.__buttons.index(button)
            self.__buttons[idx].disabled = False
        else:
            raise ButtonNotFound('Cannot enable a button that is not registered')
    
    def enable_all_buttons(self) -> None:
        """Enable all buttons on the menu"""
        for btn in self.__buttons:
            btn.disabled = False
    
    def _button_add_check(self, button: ViewButton) -> None:
        """A set of checks to ensure the proper button is being added"""
        # ensure they are using only the ViewButton and not ReactionMenus :class:`ReactionButton`
        if isinstance(button, ViewButton):

            # ensure the button custom_id is a valid one, but skip this check if its a link button because they dont have custom_ids
            if button.style == discord.ButtonStyle.link:
                pass
            else:
                # Note: this needs to be an re search because of buttons with an ID of "[ID]_[unique ID]"
                if not re.search(ViewButton._RE_IDs, button.custom_id): # type: ignore
                    raise ViewMenuException(f'ViewButton custom_id {button.custom_id!r} was not recognized')
            
            # ensure there are no duplicate custom_ids for the base navigation buttons
            # Note: there's no need to have a check for buttons that are not navigation buttons because they have a unique ID and duplicates of those are allowed
            active_button_ids: List[str] = [btn.custom_id for btn in self.__buttons] # type: ignore
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
            if len(self.__buttons) >= 25:
                raise TooManyButtons('ViewMenu cannot have more than 25 buttons (discord limitation)')
        else:
            raise IncorrectType(f'When adding a button to the ViewMenu, the button type must be ViewButton, got {button.__class__.__name__}')
    
    def _maybe_unique_id(self, button: ViewButton) -> None:
        """Create a unique ID if the `custom_id` for buttons that are allowed to have duplicates
        
            Note ::
                This excludes link buttons because they don't have a `custom_id`
        """
        if button.custom_id in (ViewButton.ID_CALLER, ViewButton.ID_SEND_MESSAGE, ViewButton.ID_CUSTOM_EMBED, ViewButton.ID_SKIP):
            button.custom_id = f'{button.custom_id}_{id(button)}'
    
    @ensure_not_primed
    def add_button(self, button: ViewButton) -> None:
        """Add a button to the menu
        
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
        self.__view.add_item(button)
        self.__buttons.append(button)
    
    @ensure_not_primed
    def add_buttons(self, buttons: Sequence[ViewButton]) -> None:
        """Add multiple buttons to the menu at once
        
        Parameters
        ----------
        buttons: Sequence[:class:`ViewButton`]
            The buttons to add
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: One of the buttons `custom_id` was set as :attr:`ViewButton.ID_CUSTOM_EMBED` but the `menu_type` is :attr:`ViewMenu.TypeText`
        - `ViewMenuException`: The `custom_id` for a button was not recognized or a button with that `custom_id` has already been added
        - `TooManyButtons`: There are already 25 buttons on the menu
        - `IncorrectType`: One or more values supplied in parameter :param:`buttons` was not of type :class:`ViewButton`
        """
        for btn in buttons:
            self.add_button(btn)
    
    def get_button(self, identity: str, *, search_by: Literal['label', 'id', 'name']='label') -> List[ViewButton]:
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
        search_by = str(search_by).lower() # type: ignore

        if search_by == 'label':
            matched_labels: List[ViewButton] = [btn for btn in self.__buttons if btn.label and btn.label == identity]
            return matched_labels
        
        elif search_by == 'id':
            matched_ids: List[ViewButton] = [btn for btn in self.__buttons if btn.custom_id and btn.custom_id.startswith(identity)]
            return matched_ids
        
        elif search_by == 'name':
            matched_names: List[ViewButton] = [btn for btn in self.__buttons if btn.name and btn.name == identity]
            return matched_names
        
        else:
            raise ViewMenuException(f'Parameter "search_by" expected "label", "id", or "name", got {search_by!r}')

    async def _paginate(self, button: ViewButton, inter: discord.Interaction) -> None:
        """|coro| When the button is pressed, handle the pagination process"""
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
            prompt: discord.Message = await self._msg.channel.send(f'{inter.user.display_name}, what page would you like to go to?') # type: ignore / `.channel` is known at this point
            try:
                selection_message: discord.Message = await inter.client.wait_for('message', check=lambda m: all([m.channel.id == self._msg.channel.id, m.author.id == inter.user.id]), timeout=self.timeout) # type: ignore / `.channel` is known at this point
                page = int(selection_message.content)
            except (asyncio.TimeoutError, ValueError):
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
            #* NOTE: Link buttons, aka buttons with a `custom_id` of `None` do not send interactions, so there's no need for an if check

            if button.custom_id.startswith(ViewButton.ID_CALLER): # type: ignore
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
                    if asyncio.iscoroutinefunction(func): await func(*args, **kwargs) # type: ignore / `func` is already confirmed to be a coroutine
                    else: func(*args, **kwargs)
                except Exception as err:
                    call_failed_error_msg = inspect.cleandoc(
                        f"""
                        The button with custom_id ViewButton.ID_CALLER with the label "{button.label}" raised an error during its execution
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
            
            elif button.custom_id.startswith(ViewButton.ID_SEND_MESSAGE): # type: ignore
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
            
            elif button.custom_id.startswith(ViewButton.ID_CUSTOM_EMBED): # type: ignore
                if self._menu_type not in (ViewMenu.TypeEmbed, ViewMenu.TypeEmbedDynamic):
                    raise ViewMenuException('Buttons with custom_id ViewButton.ID_CUSTOM_EMBED can only be used when the menu_type is ViewMenu.TypeEmbed or ViewMenu.TypeEmbedDynamic')
                else:
                    if button.followup is None or button.followup.embed is None:
                        raise ViewMenuException('ViewButton custom_id was set as ViewButton.ID_CUSTOM_EMBED but the "followup" kwargs for that ViewButton was not set or the "embed" kwarg for the followup was not set')
                   
                    await inter.response.edit_message(embed=button.followup.embed)            
            
            elif button.custom_id.startswith(ViewButton.ID_SKIP): # type: ignore
                await inter.response.edit_message(**self._determine_kwargs(self._pc.skip(button.skip)))
            
            else:
                # this shouldn't execute because of :meth:`_button_add_check`, but just in case i missed something, raise the appropriate error
                raise ViewMenuException(f'ViewButton custom_id {button.custom_id!r} was not recognized')

        await self._contact_relay(inter.user, button)

    async def stop(self, *, delete_menu_message: bool=False, disable_items: bool=False, remove_items: bool=False) -> None:
        """|coro|
        
        Stops the process of the menu with the option of deleting the menu's message, removing the buttons, or disabling the buttons upon stop
        
        Parameters
        ----------
        delete_menu_message: :class:`bool`
            Delete the message the menu is operating from

        disable_items: :class:`bool`
            Disable the buttons & selects on the menu
        
        remove_items: :class:`bool`
            Remove the buttons & selects from the menu

        Parameter Hierarchy
        -------------------
        Only one option is available when stopping the menu. If you have multiple parameters as `True`, only one will execute
        - `disable_items` > `remove_items`

        Raises
        ------
        - `discord.DiscordException`: Any exception that can be raised when deleting or editing a message
        """
        if self._is_running:
            self._stop_initiated = True
            try:
                if delete_menu_message:
                    await self._msg.delete()
                else:
                    already_disabled = False
                    if disable_items:
                        self.disable_all_buttons()
                        self.disable_all_selects()
                        self.disable_all_go_to_selects()
                        already_disabled = True
                        await self._msg.edit(view=self.__view)
                    
                    if remove_items and not already_disabled:
                        self.remove_all_buttons()
                        self.remove_all_selects()
                        self.remove_all_go_to_selects()
                        await self._msg.edit(view=self.__view)
            
            except discord.DiscordException as dpy_error:
                raise dpy_error
            
            finally:
                self.__view.stop()
                self._is_running = False

                if self in ViewMenu._active_sessions:
                    ViewMenu._active_sessions.remove(self)
                
                self._on_close_event.set()
                await self._handle_on_timeout()
    
    def _override_dm_settings(self) -> None:
        """If a menu session is in a direct message the following settings are disabled/changed because of discord limitations and resource/safety reasons
        
            .. added:: v3.1.0
        """
        if self.in_dms:
            # Can't delete someone else's message in DMs
            if self.delete_interactions:
                self.delete_interactions = False
            
            # There are no roles in DMs
            if self.only_roles:
                self.only_roles = None
            
            # No point in having an *indefinite* menu in DMs
            if self.timeout is None:
                self.timeout = 60.0
    
    def __generate_viewmenu_payload(self) -> dict:
        """Creates the parameters needed for :meth:`discord.Messageable.send()`
        
            .. added:: v3.1.0
        """
        return {
            "content" : self._pages[0].content if self._pages else None,
            "embed" : self._pages[0].embed if self._pages else discord.utils.MISSING,
            "files" : self._pages[0].files if self._pages else discord.utils.MISSING,
            "view" : self.__view,
            "allowed_mentions" : self.allowed_mentions
        }
    
    def __refresh_select_pages(self, menu_type: MenuType) -> None:
        if self.__selects:
            for vm_select in self.__selects:
                for pages in vm_select._view_select_options.values():
                    self._refresh_page_director_info(menu_type, pages)

    @overload
    async def start(self, *, send_to: Optional[str]=None, reply: bool=False) -> None:
        ...
    
    @overload
    async def start(self, *, send_to: Optional[int]=None, reply: bool=False) -> None:
        ...
    
    @overload
    async def start(self, *, send_to: Optional[discord.TextChannel]=None, reply: bool=False) -> None:
        ...
    
    @overload
    async def start(self, *, send_to: Optional[discord.VoiceChannel]=None, reply: bool=False) -> None:
        ...
    
    @overload
    async def start(self, *, send_to: Optional[discord.Thread]=None, reply: bool=False) -> None:
        ...
    
    @ensure_not_primed
    async def start(self, *, send_to: Optional[Union[str, int, discord.TextChannel, discord.VoiceChannel, discord.Thread]]=None, reply: bool=False) -> None:
        """|coro|
        
        Start the menu
        
        Parameters
        ----------
        send_to: Optional[Union[:class:`str`, :class:`int`, :class:`discord.TextChannel`, :class:`discord.VoiceChannel`, :class:`discord.Thread`]]
			The channel/thread you'd like the menu to start in. Use the channel/threads name, ID, or it's object. Please note that if you intend to use a channel/thread object, using
			method :meth:`discord.Client.get_channel()` (or any other related methods), that channel should be in the same list as if you were to use `ctx.guild.text_channels`
			or `ctx.guild.threads`. This only works on a context guild channel basis. That means a menu instance cannot be created in one guild and the menu itself (:param:`send_to`)
			be sent to another. Whichever guild context the menu was instantiated in, the channels/threads of that guild are the only options for :param:`send_to`

            Note: This parameter is not available if your `method` is a :class:`discord.Interaction`, aka a slash command
        
        reply: :class:`bool`
            Enables the menu message to reply to the message that triggered it. Parameter :param:`send_to` must be :class:`None` if this is `True`. This only pertains to a non-interaction based menu.
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `NoPages`: The menu was started when no pages have been added
        - `NoButtons`: Attempted to start the menu when no Buttons have been registered
        - `ViewMenuException`: The :class:`ViewMenu`'s `menu_type` was not recognized. There were more than one base navigation buttons. Or a :attr:`ViewButton.ID_CUSTOM_EMBED` button was not correctly formatted
        - `DescriptionOversized`: When using a `menu_type` of :attr:`ViewMenu.TypeEmbedDynamic`, the embed description was over discords size limit
        - `IncorrectType`: Parameter :param:`send_to` was not of the expected type
        - `MenuException`: The channel set in :param:`send_to` was not found
        """
        if ViewMenu._sessions_limit_details.set_by_user:
            can_proceed = await self._handle_session_limits()
            if not can_proceed:
                return
        
        self._override_dm_settings()
        
        # checks
        # Note 1: each at least 1 page check is done in it's own if statement to avoid clashing between pages and custom embeds
        # Note 2: at least 1 page check for add_row is done in "(dynamic menu)"
        
        # ensure at least 1 button exists before starting the menu
        if not self.__buttons: raise NoButtons
        if self._menu_type not in ViewMenu._all_menu_types(): raise ViewMenuException('ViewMenu menu_type not recognized')

        reply_kwargs = self._handle_reply_kwargs(send_to, reply)
        menu_payload = self.__generate_viewmenu_payload()
        
        if isinstance(self._method, Context):
            menu_payload.update(reply_kwargs)

        # add page (normal menu)
        if self._menu_type == ViewMenu.TypeEmbed:
            self._refresh_page_director_info(ViewMenu.TypeEmbed, self._pages)

            navigation_btns = [btn for btn in self.__buttons if btn.custom_id in ViewButton._base_nav_buttons()]

            # an re search is required here because buttons with ID_CUSTOM_EMBED dont have a normal ID, the ID is "8_[unique ID]"
            custom_embed_btns = [btn for btn in self.__buttons if btn.style != discord.ButtonStyle.link and re.search(r'8_\d+', btn.custom_id)] # type: ignore / raw string is compatible

            if all([not self._pages, not custom_embed_btns]):
                raise NoPages

            # normal pages, no custom embeds
            if self._pages and not custom_embed_btns:
                await self._handle_send_to(send_to, menu_payload)
            
            # only custom embeds
            elif not self._pages and custom_embed_btns:
                # since there are only custom embeds, there is no need for base navigation buttons, so remove them if any
                for nav_btn in navigation_btns:
                    if nav_btn in self.__buttons:
                        self.__buttons.remove(nav_btn)
                
                # ensure all custom embed buttons have the proper values set
                for custom_btn in custom_embed_btns:
                    if custom_btn.followup is None or custom_btn.followup.embed is None:
                        raise ViewMenuException('ViewButton custom_id was set as ViewButton.ID_CUSTOM_EMBED but the "followup" kwargs for that ViewButton was not set or the "embed" kwarg for the followup was not set')
                
                # since there are only custom embeds, self._pages is still set to :class:`None`, so set the embed in `.send()` to the first custom embed in the list
                menu_payload['embed'] = custom_embed_btns[0].followup.embed # type: ignore
                await self._handle_send_to(send_to, menu_payload)
            
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
                    await self._handle_send_to(send_to, menu_payload)
            
            self.__refresh_select_pages(ViewMenu.TypeEmbed)

        # add row (dynamic menu)
        elif self._menu_type == ViewMenu.TypeEmbedDynamic:
            await self._build_dynamic_pages(send_to, view=self.__view, payload=menu_payload)
        
        # add page (text menu)
        else:
            if not self._pages:
                raise NoPages
            
            self._refresh_page_director_info(ViewMenu.TypeText, self._pages)
            menu_payload['content'] = self._pages[0].content # reassign the first page to show to director information
            await self._handle_send_to(send_to, menu_payload)
        
        self._pc = _PageController(self._pages)
        self._is_running = True
        ViewMenu._active_sessions.append(self)
