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
import re
import warnings
from datetime import datetime
from typing import List, Union

import discord
from discord.ext.commands import AutoShardedBot, Bot, Context
from dislash import ActionRow, MessageInteraction, ResponseType, SlashClient

from .abc import _PageController
from .buttons import ComponentsButton
from .decorators import ensure_not_primed
from .errors import ButtonNotFound, ButtonsMenuException, DescriptionOversized, ImproperStyleFormat, IncorrectType, MenuSettingsMismatch, MissingSetting, NoButtons, NoPages, TooManyButtons


class ButtonsMenu:
    """A class to create a discord.py embed or text pagination menu using discords "Buttons" feature

    Parameters
    ----------
    ctx: :class:`discord.ext.commands.Context`
        The Context object. You can get this using a command or if in `discord.on_message`

    menu_type: :class:`int`:
        The configuration of the menu. Class variables :attr:`ButtonsMenu.TypeEmbed`, :attr:`ButtonsMenu.TypeEmbedDynamic`, or :attr:`ButtonsMenu.TypeText`
    
    Options [kwargs]
    ----------------
    wrap_in_codeblock: :class:`str`
        The discord codeblock language identifier to wrap your data in (:attr:`ButtonsMenu.TypeEmbedDynamic` only/defaults to :class:`None`). Example: `ButtonsMenu(ctx, ..., wrap_in_codeblock='py')`
    
    custom_embed: :class:`discord.Embed`
        Embed object to use when adding data with :meth:`ButtonsMenu.add_row()`. Used for styling purposes (:attr:`ButtonsMenu.TypeEmbedDynamic` only/defaults to :class:`None`)
    
    delete_on_timeout: :class:`bool`
        Delete the menu when it times out (defaults to `False`) If `True`, `disable_buttons_on_timeout` and `remove_buttons_on_timeout` will not execute regardless of if they are `True`. This takes priority over those actions
    
    disable_buttons_on_timeout: :class:`bool`
        Disable the buttons on the menu when the menu times out (defaults to `True`) If `delete_on_timeout` is `True`, this will be overridden
    
    remove_buttons_on_timeout: :class:`bool`
        Remove the buttons on the menu when the menu times out (defaults to `False`) If `disable_buttons_on_timeout` is `True`, this will be overridden
    
    only_roles: List[:class:`discord.Role`]
        If set, only members with any of the given roles are allowed to control the menu. The menu owner can always control the menu (defaults to :class:`None`)
    
    timeout: Union[:class:`int`, :class:`float`, :class:`None`]
        The timer for when the menu times out. Can be :class:`None` for no timeout (defaults to `60.0`)
    
    show_page_director: :class:`bool`
        Shown at the botttom of each embed page. "Page 1/20" (defaults to `True`)
    
    name: :class:`str`
        A name you can set for the menu (defaults to :class:`None`)
    
    style: :class:`str`
        A custom page director style you can select. "$" represents the current page, "&" represents the total amount of pages (defaults to "Page $/&") Example: `ButtonsMenu(ctx, ..., style='On $ out of &')`

    all_can_click: :class:`bool`
        Sets if everyone is allowed to control when pages are 'turned' when buttons are clicked (defaults to `False`)
    
    delete_interactions: :class:`bool`
        Delete the prompt message by the bot and response message by the user when asked what page they would like to go to when using `ComponentsButton.ID_GO_TO_PAGE` (defaults to `True`)
    
    allowed_mentions: :class:`discord.AllowedMentions`
        Controls the mentions being processed in the menu message (defaults to :class:`discord.AllowedMentions(everyone=True, users=True, roles=True, replied_user=True)`)
    
    rows_requested: :class:`int`
        The amount of information per :meth:`ButtonsMenu.add_row()` you would like applied to each embed page (:attr:`ButtonsMenu.TypeEmbedDynamic` only/defaults to :class:`None`)
    """
    TypeEmbed = 1
    TypeEmbedDynamic = 2
    TypeText = 3
    
    _active_sessions: List['ButtonsMenu'] = []

    def __repr__(self):
        x = {key : val for key, val in self.__dict__.items() if not key.startswith('_') and val}
        y = ' '.join(f'{key}={val!r}' for key, val in x.items() if key != 'name') # intentionally exclude "name" because i want the first 3 items to be just like ReactionMenu's __repr__
        z = f'<ButtonsMenu name={self.name!r} owner={str(self.owner)!r} is_running={self._is_running} {y}>'
        return z

    def __init__(self, ctx: Context, *, menu_type: int, **options):
        self._ctx = ctx
        self._bot = ctx.bot
        self._row_of_buttons: List[ComponentsButton] = []
        self._is_running = False
        self.__pages: List[Union[discord.Embed, str]] = []
        self._dynamic_data_builder: List[str] = []
        self._msg: discord.Message = None
        self._main_session_task: asyncio.Task = None
        self._menu_type = menu_type
        self._inter: MessageInteraction = None
        self._pc: _PageController = None
        self._caller_details: 'NamedTuple' = None
        self._on_timeout_details: 'function' = None
        self._main_page_contents = collections.deque()
        self._last_page_contents = collections.deque()

        # kwargs
        self.wrap_in_codeblock: Union[str, None] = options.get('wrap_in_codeblock')
        self.custom_embed: Union[discord.Embed, None] = options.get('custom_embed')
        self.delete_on_timeout: bool = options.get('delete_on_timeout', False)
        self.disable_buttons_on_timeout: bool = options.get('disable_buttons_on_timeout', True)
        self.remove_buttons_on_timeout: bool = options.get('remove_buttons_on_timeout', False)
        self.only_roles: Union[List[discord.Role], None] = options.get('only_roles')
        self.timeout: Union[int, float, None] = options.get('timeout', 60.0)
        self.show_page_director: bool = options.get('show_page_director', True)
        self.name: Union[str, None] = options.get('name')
        self.style: Union[str, None] = options.get('style', 'Page $/&')
        self.all_can_click: bool = options.get('all_can_click', False)
        self.delete_interactions: bool = options.get('delete_interactions', True)
        self.allowed_mentions: discord.AllowedMentions = options.get('allowed_mentions', discord.AllowedMentions())
        self.__rows_requested: int = options.get('rows_requested')
    
    @staticmethod
    def initialize(bot: Union[Bot, AutoShardedBot]):
        """|static method| The initial setup needed in order to use Discord Components (Buttons)
        
        Parameters
        ----------
        bot: Union[:class:`discord.ext.commands.Bot`, :class:`discord.ext.commands.AutoShardedBot`]:
            The bot instance to initialize
        
        Raises
        ------
        - `IncorrectType`: Parameter :param:`bot` was not of type :class:`discord.ext.commands.Bot` or :class:`discord.ext.commands.AutoShardedBot`
        """
        if isinstance(bot, (Bot, AutoShardedBot)):
            SlashClient(bot)
        else:
            raise IncorrectType(f'When initializing the ButtonsMenu, discord.ext.commands.Bot or discord.ext.commands.AutoShardedBot is required, got {bot.__class__.__name__}')
    
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
    def get_menu_from_message(cls, message_id: int) -> Union['ButtonsMenu', None]:
        """|class method| Return the :class:`ButtonsMenu` object associated with the message with the given ID
        
        Parameters
        ----------
        message_id: :class:`int`
            The message ID from the menu message
        
        Returns
        -------
        :class:`ButtonsMenu`:
           Can be :class:`None` if the menu is not found in the list of active menu sessions
        """
        for menu in cls._active_sessions:
            if menu._msg.id == message_id:
                return menu
        return None
        
    @classmethod
    def get_all_sessions(cls) -> Union[List['ButtonsMenu'], None]:
        """|class method| Get all active menu sessions
        
        Returns
        -------
        List[:class:`ButtonsMenu`]:
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
    def get_session(cls, name: str) -> Union['ButtonsMenu', List['ButtonsMenu'], None]:
        """|class method| Get a :class:`ButtonsMenu` instance by its name

        Parameters
        ----------
        name: :class:`str`
            :class:`ButtonsMenu` instance name
        
        Returns
        -------
        Union[:class:`ButtonsMenu`, List[:class:`ButtonsMenu`]]:
            The :class:`ButtonsMenu` instance that was found. Can return a list of :class:`ButtonsMenu` if multiple instances are running that matched the provided name. Can also return :class:`None` if the menu with the provided
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
            The message the :class:`ButtonsMenu` is operating from
        """
        return self._msg
    
    @property
    def buttons(self) -> List[ComponentsButton]:
        """
        Returns
        -------
        List[:class:`ComponentsButton`]: The buttons that have been added to the menu. Can be :class:`None` if there are no buttons registered to the menu
        """
        return self._row_of_buttons if self._row_of_buttons else None
    
    @property
    def buttons_most_clicked(self) -> List[ComponentsButton]:
        """
        Returns
        -------
        List[:class:`ComponentsButton`]:
            The buttons on the menu ordered from highest (button with the most clicks) to lowest (button with the least clicks). Can be :class:`None` if there are no buttons registered to the menu
        """
        if self._row_of_buttons:
            return sorted(self._row_of_buttons, key=lambda btn: btn.total_clicks, reverse=True)
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
        if self._ctx.guild is None:
            return True
        else:
            return False
    
    @property
    def pages(self) -> list:
        """
        Returns
        -------
        A list of either :class:`discord.Embed` if the menu_type is :attr:`ButtonsMenu.TypeEmbed` / :attr:`ButtonsEmbed.TypeEmbedDynamc`. Or :class:`str` if :attr:`ButtonsMenu.TypeText`. Can return :class:`None` if there are no pages
        """
        return self.__pages if self.__pages else None
    
    def _handle_send_to(self, send_to):
        """For the `send_to` kwarg in :meth:`ButtonsMenu.start()`, determine what channel the menu should start in"""
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
                        NO_CHANNELS_ERROR = f'When using parameter "send_to" in ButtonsMenu.start(), there were no channels with the name {send_to!r}'
                        MULTIPLE_CHANNELS_ERROR = f'When using parameter "send_to" in ButtonsMenu.start(), there were {len(matched_channels)} channels with the name {send_to!r}. With multiple channels having the same name, the intended channel is unknown'  
                        raise ButtonsMenuException(NO_CHANNELS_ERROR if len(matched_channels) == 0 else MULTIPLE_CHANNELS_ERROR)
                    
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
                        raise ButtonsMenuException(f'When using parameter "send_to" in ButtonsMenu.start(), the channel {send_to} was not found')
    
    def _check(self, inter: MessageInteraction):
        """Base menu button interaction check"""
        author_pass = False
        
        if self._ctx.author.id == inter.author.id: author_pass = True
        if self.only_roles: self.all_can_click = False

        if self.only_roles:
            for role in self.only_roles:
                if role in inter.author.roles:
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
            Either `ButtonsMenu.TypeEmbed`/`ButtonsMenu.TypeEmbedDynamic` or `ButtonsMenu.TypeText`
        
        pages: List[Union[:class:`discord.Embed`, :class:`str`]]
            The pagination contents
        """
        if self.show_page_director:
            if type_ not in (ButtonsMenu.TypeEmbed, ButtonsMenu.TypeEmbedDynamic, ButtonsMenu.TypeText): raise Exception('Needs to be of type ButtonsMenu.TypeEmbed, ButtonsMenu.TypeEmbedDynamic or ButtonsMenu.TypeText')
            
            if type_ == ButtonsMenu.TypeEmbed or type_ == ButtonsMenu.TypeEmbedDynamic:
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
                    
                    # NOTE: with codeblocks, i already tried the f doc string version of this and it doesnt work because there is a spacing issue with page_info. using a normal f string with \n works as intended
                    # f doc string version: https://github.com/Defxult/reactionmenu/blob/eb88af3a2a6dd468f7bcff38214eb77bc91b241e/reactionmenu/text.py#L288
                    
                    if re.search(CODEBLOCK, content):
                        if re.search(CODEBLOCK_DATA_AFTER, content):
                            pages[idx] = f'{content}\n\n{page_info}'
                        else:
                            pages[idx] = f'{content}\n{page_info}'
                    else:
                        pages[idx] = f'{content}\n\n{page_info}'
                    page_count += 1
            
    def _decide_kwargs(self, button_id: str) -> dict:
        """Used in :meth:`ButtonsMenu._execute_interactive_session()`, determines the kwargs that need to be passed to the `MessageInteraction.reply()` method"""
        kwargs = {
            'content' : None,
            'embed' : None,
            'embeds' : None,
            'components' : None,
            'file' : None,
            'files' : None,
            'tts' : None,
            'hide_user_input' : False,
            'ephemeral' : False,
            'delete_after' : None,
            'allowed_mentions' : self.allowed_mentions,
            'type' : ResponseType.UpdateMessage,
            'fetch_response_message' : True
        }

        if self._menu_type == ButtonsMenu.TypeEmbed or self._menu_type == ButtonsMenu.TypeEmbedDynamic:
            if any([button_id == ComponentsButton.ID_NEXT_PAGE, button_id == ComponentsButton.ID_GO_TO_PAGE]):
                kwargs['embed'] = self._pc.next()
            elif button_id == ComponentsButton.ID_PREVIOUS_PAGE:
                kwargs['embed'] = self._pc.prev()
            else:
                kwargs['embed'] = self._pc.current_page
        
        elif self._menu_type == ButtonsMenu.TypeText:
            if any([button_id == ComponentsButton.ID_NEXT_PAGE, button_id == ComponentsButton.ID_GO_TO_PAGE]):
                kwargs['content'] = self._pc.next()
            elif button_id == ComponentsButton.ID_PREVIOUS_PAGE:
                kwargs['content'] = self._pc.prev()
            else:
                kwargs['content'] = self._pc.current_page
        
        return kwargs

    async def _execute_interactive_session(self):
        """|coro| Handles all processing of the pagination session"""
        ButtonsMenu._active_sessions.append(self)
        while self._is_running:
            try:
                inter: MessageInteraction = await self._msg.wait_for_button_click(check=self._check, timeout=self.timeout)
                self._inter = inter
            except asyncio.TimeoutError:
                await self.stop(delete_menu_message=self.delete_on_timeout, remove_buttons=self.remove_buttons_on_timeout, disable_buttons=self.disable_buttons_on_timeout)
            else:
                btn = inter.clicked_button

                # update the ComponentsButton values
                cmp_btn = self.get_button(btn.custom_id, search_by='id')
                if cmp_btn is not None: # if :class:`None`, it was removed from the menu
                    cmp_btn._ComponentsButton__clicked_by.add(inter.author)
                    cmp_btn._ComponentsButton__total_clicks += 1
                    cmp_btn._ComponentsButton__last_clicked = datetime.utcnow()
                
                if btn.custom_id == ComponentsButton.ID_NEXT_PAGE:
                    await inter.reply(**self._decide_kwargs(button_id=btn.custom_id))
                
                elif btn.custom_id == ComponentsButton.ID_PREVIOUS_PAGE:
                    await inter.reply(**self._decide_kwargs(button_id=btn.custom_id))
                    
                elif btn.custom_id == ComponentsButton.ID_GO_TO_FIRST_PAGE:
                    self._pc.index = 0
                    await inter.reply(**self._decide_kwargs(button_id=btn.custom_id))

                elif btn.custom_id == ComponentsButton.ID_GO_TO_LAST_PAGE:
                    self._pc.index = self._pc.total_pages
                    await inter.reply(**self._decide_kwargs(button_id=btn.custom_id))
                    
                elif btn.custom_id == ComponentsButton.ID_GO_TO_PAGE:
                    await inter.reply(f'{self._ctx.author.name}, what page what you like to go to?', type=ResponseType.ChannelMessageWithSource)
                    
                    try:
                        user_response = await self._bot.wait_for('message', check=lambda m: m.channel.id == inter.message.channel.id and m.author.id == self._ctx.author.id, timeout=self.timeout)
                        selected_page = int(user_response.content)
                    except asyncio.TimeoutError:
                        continue
                    except ValueError:
                        continue
                    else:
                        if 1 <= selected_page <= len(self.__pages):
                            self._pc.index = selected_page - 2
                            kwargs = self._decide_kwargs(button_id=btn.custom_id)
                            kwargs['components'] = [ActionRow(*self._row_of_buttons)]

                            # remove unused kwargs that will be sent in the `.edit` parameters
                            # NOTE: this was made because there was an issue with sending a message with 'content' of :class:`None` because :meth:`_decide_kwargs` is mainly made for the above ComponentButton IDs
                            # but this is the one exception where the kwargs aren't really needed because im using a `discord.Message` to edit instead of replying
                            for key in kwargs.copy().keys():
                                if self._menu_type == ButtonsMenu.TypeText:
                                    if key == 'content' or key == 'allowed_mentions':
                                        continue
                                    else:
                                        del kwargs[key]
                            
                                elif self._menu_type == ButtonsMenu.TypeEmbed or self._menu_type == ButtonsMenu.TypeEmbedDynamic:
                                    if key == 'embed' or key == 'allowed_mentions':
                                        continue
                                    else:
                                        del kwargs[key]
                            else:
                                await self._msg.edit(**kwargs)

                                if self.delete_interactions:
                                    await user_response.delete()
                                    await inter.delete()
                    
                elif btn.custom_id == ComponentsButton.ID_END_SESSION:
                    await self.stop(delete_menu_message=True)
                
                elif btn.custom_id == ComponentsButton.ID_CALLER:
                    if self._caller_details:
                        func = self._caller_details.func
                        args = self._caller_details.args
                        kwargs = self._caller_details.kwargs
                        
                        await inter.reply(type=ResponseType.DeferredUpdateMessage)
                        
                        try:
                            if asyncio.iscoroutinefunction(func):
                                await func(*args, **kwargs)
                            else:
                                func(*args, **kwargs)
                        except TypeError as err:
                            raise ButtonsMenuException(f'When setting the caller details, {err}')
                        else:
                            if cmp_btn.followup:
                                # make sure there is atleast content, embed, or file. if all of them are None, a discord.HTTPException will occur
                                if all((cmp_btn.followup.content is None, cmp_btn.followup.embed is None, cmp_btn.followup.file is None)):
                                    raise ButtonsMenuException('In a ComponentsButton.Followup, there must be at least content, embed, or file')
                                
                                followup_kwargs = cmp_btn.followup._to_dict()

                                # inter.followup() has no attribute delete_after/ephemeral so manually delete the key/val pairs to avoid an error
                                del followup_kwargs['delete_after']
                                del followup_kwargs['ephemeral']

                                followup_message: discord.Message = await inter.followup(**followup_kwargs)
                                
                                if cmp_btn.followup.delete_after:
                                    await followup_message.delete(delay=cmp_btn.followup.delete_after)
                    else:
                        raise ButtonsMenuException('ComponentsButton with custom_id ComponentsButton.ID_CALLER was clicked but method ButtonsMenu.set_caller_details(...) was not called')
                
                elif btn.custom_id == ComponentsButton.ID_SEND_MESSAGE:
                    if cmp_btn.followup is None:
                        raise ButtonsMenuException('ComponentsButton custom_id was set as ComponentsButton.ID_SEND_MESSAGE but the "followup" kwarg for that ComponentsButton was not set')
                    
                    followup_kwargs = cmp_btn.followup._to_dict()

                    # if a file exists, remove it because the file will be ignored because of discord limitations (noted in ComponentsButton.Followup doc string)
                    if followup_kwargs['file']:
                        del followup_kwargs['file']
                    
                    followup_kwargs['type'] = ResponseType.ChannelMessageWithSource
                    await inter.reply(**followup_kwargs)
                
                else:
                    # this shouldnt execute because of :meth:`_button_add_check`, but just in case i missed something, throw the appropriate error
                    raise ButtonsMenuException('ComponentsButton custom_id was not recognized')

    def _done_callback(self, task: asyncio.Task):
        """Main session task done callback"""
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        finally:
            if not task.cancelled():
                self._is_running = False
                cls = self.__class__
                if self in cls._active_sessions:
                    cls._active_sessions.remove(self)
    
    def _chunks(self, list_, n):
        """Yield successive n-sized chunks from list. Core component of a dynamic menu"""
        for i in range(0, len(list_), n):
            yield list_[i:i + n]
    
    async def update(self, new_pages: Union[List[Union[discord.Embed, str]], None], new_buttons: Union[List[ComponentsButton], None]):
        """|coro| When the menu is running, update the pages or buttons 

        Parameters
        ----------
        new_pages: List[Union[:class:`discord.Embed`, :class:`str`]]
            Pages to *replace* the current pages with. If the menus current menu_type is `ButtonsMenu.TypeEmbed`, only :class:`discord.Embed` can be used. If `ButtonsMenu.TypeText`, only :class:`str` can be used. If you
            don't want to replace any pages, set this to :class:`None`
        
        new_buttons: List[:class:`ComponentsButtons`]
            Buttons to *replace* the current buttons with. Can be an empty list if you want the updated menu to have no buttons. Can also be set to :class:`None` if you don't want to replace any buttons
        
        Raises
        ------
        - `TooManyButtons`: There are already 5 buttons on the menu
        - `IncorrectType`: The values in :param:`new_pages` did not match the :class:`ButtonsMenu` menu_type. An attempt to use this method when the menu_type is `ButtonsMenu.TypeEmbedDynamic` which is not allowed. Or
        all :param:`new_buttons` values were not of type :class:`ComponentsButton`
        """
        if self._is_running:
            # checks
            if new_pages is None and new_buttons is None:
                return

            if new_buttons:
                # NOTE: duplicate custom_id check is done when determining the action (below)

                if len(new_buttons) > 5:
                    raise TooManyButtons(f'When updating the menu, ButtonsMenu cannot have more that 5 buttons (discord limitation). Buttons currently registered: {len(self._row_of_buttons)}. Tried to add: {len(new_buttons)}')

                for btn in new_buttons:
                    if not isinstance(btn, ComponentsButton):
                        raise IncorrectType('When updating a menu, all new_buttons must be of type ComponentsButton')

            if self._menu_type not in (ButtonsMenu.TypeEmbed, ButtonsMenu.TypeText):
                raise IncorrectType('Updating a menu is only valid for a menu with menu_type ButtonsMenu.TypeEmbed or ButtonsMenu.TypeText')
            
            if self._menu_type == ButtonsMenu.TypeEmbed and new_pages:
                if not all([isinstance(page, discord.Embed) for page in new_pages]):
                    raise IncorrectType('When updating the menu, all values must be of type discord.Embed because the current menu_type is ButtonsMenu.TypeEmbed')
            
            if self._menu_type == ButtonsMenu.TypeText and new_pages:
                if not all([isinstance(page, str) for page in new_pages]):
                    raise IncorrectType('When updating the menu, all values must be of type str because the current menu_type is ButtonsMenu.TypeText')
            
            if isinstance(new_pages, list) and len(new_pages) == 0:
                raise ButtonsMenuException('new_pages cannot be an empty list. Must be None if no new pages should be added')
            # ---- end checks

            if new_pages is not None:
                self.__pages = new_pages
                self._pc = _PageController(new_pages)
                if self._menu_type == ButtonsMenu.TypeEmbed:
                    # before the refresh of the director, clear all footer information first if any. if new_pages also contains pages from the old pages, director
                    # information will stack. Also just to clear out any text that should be reformatted to fit the page director format. This also fixes the bug where
                    # if a menu was updated multiple times in a single session, the first click would be off by 1. it catches up after the 2nd click, but this prevents
                    # it from happening in the first place (probably because of the director? not sure though)
                    for embed_page in new_pages:
                        if embed_page.footer:
                            embed_page.set_footer(text=discord.Embed.Empty, icon_url=discord.Embed.Empty)

                    self._refresh_page_director_info(ButtonsMenu.TypeEmbed, self.__pages)
                else:
                    self._refresh_page_director_info(ButtonsMenu.TypeText, self.__pages)
            
            # determine the action the user wants for new_buttons
            kwargs_to_pass = {}

            if isinstance(new_buttons, list):
                if len(new_buttons) == 0:
                    self._row_of_buttons.clear()
                    kwargs_to_pass['components'] = []
                else:
                    # before we assign the new row of buttons, make sure there arent any duplicate custom_id's
                    counter = collections.Counter([btn.custom_id for btn in new_buttons])
                    if max(counter.values()) != 1:
                        raise ButtonsMenuException('When updating the menu, new_buttons cannot contain any duplicate custom_id')
                    else:
                        self._row_of_buttons = new_buttons
                        kwargs_to_pass['components'] = [ActionRow(*new_buttons)]
            
            # the user does not want to add any new buttons
            elif isinstance(new_buttons, type(None)):
                kwargs_to_pass['components'] = [ActionRow(*self._row_of_buttons)]
            
            if self._menu_type == ButtonsMenu.TypeEmbed:
                kwargs_to_pass['embed'] = self.__pages[0]
            else:
                kwargs_to_pass['content'] = self.__pages[0]
            
            await self._msg.edit(**kwargs_to_pass)
    
    async def refresh_menu_buttons(self):
        """|coro| When the menu is running, update the message to reflect the buttons that were removed, disabled, or added"""
        if self._is_running:
            if self._row_of_buttons:
                await self._msg.edit(components=[ActionRow(*self._row_of_buttons)])
            else:
                await self._msg.edit(components=[])
    
    def remove_button(self, button: ComponentsButton):
        """Remove a button from the menu

        Parameters
        ----------
        button: :class:`ComponentsButton`:
            The button to remove
        
        Raises
        ------
        - `ButtonNotFound`: The provided button was not found in the list of buttons on the menu
        """
        if button in self._row_of_buttons:
            self._row_of_buttons.remove(button)
        else:
            raise ButtonNotFound(f'Cannot remove a button that is not registered')
    
    def remove_all_buttons(self):
        """Remove all buttons from the menu"""
        self._row_of_buttons.clear()
    
    def disable_button(self, button: ComponentsButton):
        """Disable a button on the menu

        Parameters
        ----------
        button: :class:`ComponentsButton`:
            The button to disable
        
        Raises
        ------
        - `ButtonNotFound`: The provided button was not found in the list of buttons on the menu
        """
        if button in self._row_of_buttons:
            idx = self._row_of_buttons.index(button)
            self._row_of_buttons[idx].disabled = True
        else:
            raise ButtonNotFound(f'Cannot disable a button that is not registered')
    
    def disable_all_buttons(self):
        """Disable all buttons on the menu"""
        for btn in self._row_of_buttons:
            btn.disabled = True
    
    def enable_button(self, button: ComponentsButton):
        """Enable the specified button

        Parameters
        ----------
        button: :class:`ComponentsButton`
            The button to enable
        
        Raises
        ------
        - `ButtonNotFound`: The provided button was not found in the list of buttons on the menu
        """
        if button in self._row_of_buttons:
            idx = self._row_of_buttons.index(button)
            self._row_of_buttons[idx].disabled = False
        else:
            raise ButtonNotFound('Cannot enable a button that is not registered')
    
    def enable_all_buttons(self):
        """Enable all buttons on the menu"""
        for btn in self._row_of_buttons:
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
        - `ButtonsMenuException`: Parameter "func" was not a callable object
        """
        if not callable(func): raise ButtonsMenuException('Parameter "func" must be callable')
        self._on_timeout_details = func
    
    def set_caller_details(self, func: object, *args, **kwargs):
        """Set the parameters for the function you set for a :class:`ComponentsButton` with the custom_id `ComponentsButton.ID_CALLER`
        
        func: :class:`object`
            The function object that will be called when the associated button is clicked

        *args: :class:`Any`
            An argument list that represents the parameters of that function
        
        **kwargs: :class:`Any`
            An argument list that represents the kwarg parameters of that function
        
        Raises
        ------
        - `ButtonsMenuException`: Parameter "func" was not a callable object
        """
        if not callable(func): raise ButtonsMenuException('Parameter "func" must be callable')
        Details = collections.namedtuple('Details', ['func', 'args', 'kwargs'])
        self._caller_details = Details(func=func, args=args, kwargs=kwargs)
    
    def _button_add_check(self, button: ComponentsButton):
        """A set of checks to ensure the proper button is being added"""
        # ensure they are using only the ComponentsButton and not ReactionMenus :class:`Button`/:class:`ButtonType`
        if isinstance(button, ComponentsButton):

            # ensure the button custom_id is a valid one
            if button.custom_id not in ComponentsButton._all_ids():
                if button.style == ComponentsButton.style.link:
                    pass
                else:
                    raise ButtonsMenuException(f'ComponentsButton custom_id {button.custom_id!r} was not recognized')

            # ensure there are no duplicate custom_ids
            active_button_ids: List[str] = [btn.custom_id for btn in self._row_of_buttons]
            if button.custom_id in active_button_ids:
                name = ComponentsButton._get_id_name_from_id(button.custom_id)
                raise ButtonsMenuException(f'A ComponentsButton with custom_id {name!r} has already been added')
            
            # ensure there are no more than 5 buttons
            if len(self._row_of_buttons) >= 5:
                raise TooManyButtons('ButtonsMenu cannot have more that 5 buttons (discord limitation)')
        else:
            raise IncorrectType(f'When adding a button to the ButtonsMenu, the button type must be ComponentsButton, not {button.__class__.__name__}')
    
    @ensure_not_primed
    def add_button(self, button: ComponentsButton):
        """Register a button to the menu
        
        Parameters
        ----------
        button: :class:`ComponentsButton`
            The button to register
        
        Raises
        ------
        - `ButtonsMenuException`: The custom_id for the button was not recognized. A button with that custom_id has already been added
        - `TooManyButtons`: There are already 5 buttons on the menu
        - `IncorrectType`: Parameter :param:`button` was not of type :class:`ComponentsButton`
        """
        self._button_add_check(button)
        self._row_of_buttons.append(button)
    
    def get_button(self, identity: str, *, search_by: str='label') -> Union[ComponentsButton, List[ComponentsButton], None]:
        """Get a button that has been registered to the menu by it's label or custom_id
        
        Parameters
        ----------
        identity: :class:`str`
            The button label (case sensitive) or it's custom_id
        
        search_by: :class:`str`
            (optional) How to search for the button. If "label", it's searched by button labels, if "id", it's searched by it's custom_id (defaults to "label")
        
        Raises
        ------
        - `ButtonsMenuException`: Parameter :param:`search_by` was not "label" or "id"
        
        Returns
        -------
        Union[:class:`ComponentsButton`, List[:class:`ComponentsButton`]]:
            The button(s) matching the given identity. Can be :class:`None` if the button was not found
        """
        identity = str(identity)
        search_by = str(search_by).lower()

        if search_by in ('label', 'id'):
            if search_by == 'label':
                matched_labels = [btn for btn in self._row_of_buttons if btn.label == identity]
                if matched_labels:
                    if len(matched_labels) == 1: return matched_labels[0]
                    else: return matched_labels
                else:
                    return None
            else:
                matched_id = [btn for btn in self._row_of_buttons if btn.custom_id == identity]
                if matched_id: return matched_id[0]
                else: return None
        else:
            raise ButtonsMenuException(f'Parameter "search_by" expected "label" or "id", got {search_by!r}')
    
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
        page_number: :class:`int`:
            The page to remove
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `ButtonsMenuException`: The page associated with the given page number was not valid
        """
        if self.__pages:
            if page_number > 0 and page_number <= len(self.__pages):
                page_to_delete = page_number - 1
                del self.__pages[page_to_delete]
            else:
                raise ButtonsMenuException(f'Page number invalid. Must be from 1 - {len(self.__pages)}')
    
    @ensure_not_primed
    def add_page(self, page: Union[discord.Embed, str]):
        """Add a page to the menu

        Parameters
        ----------
        page: Union[:class:`discord.Embed`, :class:`str`]
            The page to add. Can only be used when the menus `menu_type` is `ButtonsMenu.TypeEmbed` (adding an embed) or `ButtonsMenu.TypeText` (adding a str)

        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: The page being added does not match the menus `menu_type` 
        """
        if self._menu_type == ButtonsMenu.TypeEmbed:
            if isinstance(page, discord.Embed):
                self.__pages.append(page)
            else:
                raise MenuSettingsMismatch(f'ButtonsMenu menu_type was set as ButtonsMenu.TypeEmbed but got {page.__class__.__name__} when adding a page')
        
        elif self._menu_type == ButtonsMenu.TypeText:
            self.__pages.append(str(page))
        
        else:
            raise MenuSettingsMismatch('add_page method cannot be used with the current ButtonsMenu menu_type')
    
    @ensure_not_primed
    def clear_all_row_data(self):
        """Delete all the data thats been added using :meth:`ButtonsMenu.add_row()`
        
        Raises
        ------
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MenuSettingsMismatch`: This method was called but the menus `menu_type` was not `ButtonsMenu.TypeEmbedDynamic`
        """
        if self._menu_type == ButtonsMenu.TypeEmbedDynamic:
            self._dynamic_data_builder.clear()
        else:
            raise MenuSettingsMismatch('Cannot use method ButtonsMenu.clear_all_row_data() when the menu_type is not set as ButtonsMenu.TypeEmbedDynamic')
    
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
        - `MenuSettingsMismatch`: This method was called but the menus `menu_type` was not `ButtonsMenu.TypeEmbedDynamic`
        - `MissingSetting`: `ButtonsMenu` kwarg "rows_requested" (int) has not been set
        """
        if self._menu_type == ButtonsMenu.TypeEmbedDynamic:
            if self.__rows_requested:
                self._dynamic_data_builder.append(str(data))
            else:
                raise MissingSetting(f'ButtonsMenu kwarg "rows_requested" (int) has not been set')
        else:
            raise MenuSettingsMismatch('add_row can only be used with a menu_type of ButtonsMenu.TypeEmbedDynamic')
    
    @ensure_not_primed
    def set_main_pages(self, *embeds: discord.Embed):
        """On a menu with a menu_type of `ButtonsMenu.TypeEmbedDynamic`, set the pages you would like to show first. These embeds will be shown before the embeds that contain your data

        Parameter
        ---------
        *embeds: :class:`discord.Embed`
            An argument list of :class:`discord.Embed` objects

        Raises
        ------
        - `MenuSettingsMismatch`: Tried to use method on a menu that was not of menu_type `ButtonsMenu.TypeEmbedDynamic`
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `ButtonsMenuException`: The "embeds" parameter was empty. At least one value is needed
        - `IncorrectType`: All values in the argument list were not of type `discord.Embed`
        """
        if not embeds: raise ButtonsMenuException('The argument list when setting main pages was empty')
        if not all([isinstance(e, discord.Embed) for e in embeds]): raise IncorrectType('All values in the argument list when setting main pages were not of type discord.Embed')
        if self._menu_type != ButtonsMenu.TypeEmbedDynamic: raise MenuSettingsMismatch('Method set_main_pages is only available for menus with menu_type ButtonsMenu.TypeEmbedDynamic')
        
        # if they've set any values, remove it. Each set should be from the call and should not stack
        self._main_page_contents.clear()
        
        for embed in embeds:
            self._main_page_contents.append(embed)

    @ensure_not_primed
    def set_last_pages(self, *embeds: discord.Embed):
        """On a menu with a menu_type of `ButtonsMenu.TypeEmbedDynamic`, set the pages you would like to show last. These embeds will be shown after the embeds that contain your data

        Parameter
        ---------
        *embeds: :class:`discord.Embed`
            An argument list of :class:`discord.Embed` objects

        Raises
        ------
        - `MenuSettingsMismatch`: Tried to use method on a menu that was not of menu_type `ButtonsMenu.TypeEmbedDynamic`
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `ButtonsMenuException`: The "embeds" parameter was empty. At least one value is needed
        - `IncorrectType`: All values in the argument list were not of type `discord.Embed`
        """
        if not embeds: raise ButtonsMenuException('The argument list when setting main pages was empty')
        if not all([isinstance(e, discord.Embed) for e in embeds]): raise IncorrectType('All values in the argument list when setting main pages were not of type discord.Embed')
        if self._menu_type != ButtonsMenu.TypeEmbedDynamic: raise MenuSettingsMismatch('Method set_last_pages is only available for menus with menu_type ButtonsMenu.TypeEmbedDynamic')
        
        # if they've set any values, remove it. Each set should be from the call and should not stack
        self._last_page_contents.clear()
        
        for embed in embeds:
            self._last_page_contents.append(embed)

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
        
        See the :class:`ButtonsMenu` doc string for more information
        """
        if self._is_running:
            try:
                if delete_menu_message:
                    await self._msg.delete()
                
                elif disable_buttons:
                    def disable_and_return():
                        """Disable all the buttons registered to the menu and return them for use"""
                        for i in self._row_of_buttons:
                            i.disabled = True
                        return self._row_of_buttons
                    
                    if not self._row_of_buttons: return # if there are no buttons (they've all been removed) to disable, skip this step
                    await self._msg.edit(components=[ActionRow(*disable_and_return())])

                elif remove_buttons:
                    if not self._row_of_buttons: return # if there are no buttons to remove (they've already been removed), skip this step
                    await self._msg.edit(components=[])
            
            except discord.DiscordException as dpy_error:
                raise dpy_error
            
            finally:
                self._is_running = False
                if self in ButtonsMenu._active_sessions:
                    ButtonsMenu._active_sessions.remove(self)
                
                # handle `on_timeout`
                if self._on_timeout_details:
                    func = self._on_timeout_details
                    
                    # call the timeout function but ignore any and all exceptions that may occur during the function timeout call.
                    # the most important thing here is to ensure the menu is properly shutdown (task is cancelled) upon timeout and if an exception occurs
                    # the process will not complete
                    try:
                        if asyncio.iscoroutinefunction(func): await func(self)
                        else: func(self)
                    except Exception as error:
                        warnings.formatwarning = lambda msg, *args, **kwargs: f'{msg}'
                        warnings.warn(inspect.cleandoc(
                            f"""
                            UserWarning: The function you have set in method ButtonsMenu.set_on_timeout() raised on error

                            -> {error.__class__.__name__}: {error}
                            
                            This error has been ignored so the menu timeout process can complete
                            """
                        ))
                self._main_session_task.cancel()
    
    @ensure_not_primed
    async def start(self, *, send_to: Union[str, int, discord.TextChannel]=None):
        """|coro| Start the menu

        Parameter
        ---------
        send_to: Union[:class:`str`, :class:`int`, :class:`discord.TextChannel`]
            (optional) The channel you'd like the menu to start in. Use the channel name, ID, or it's object. Please note that if you intend to use a text channel object, using
            method :meth:`discord.Client.get_channel`, that text channel should be in the same list as if you were to use `ctx.guild.text_channels`. This only works on a context guild text channel basis. That means a menu instance cannot be
            created in one guild and the menu itself (:param:`send_to`) be sent to another. Whichever guild context the menu was instantiated in, the text channels of that guild are the only options for :param:`send_to` (defaults to :class:`None`)

        Example for :param:`send_to`
        ---------------------------
        ```
        menu = ButtonsMenu(...)
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
        - `MenuAlreadyRunning`: Attempted to call method after the menu has already started
        - `MissingSetting`: The "components" kwarg is missing from the `Messageable.send()` method (the menu was not initialized with `ButtonsMenu.initialize(...)`)
        - `NoPages`: The menu was started when no pages have been added
        - `NoButtons`: Attempted to start the menu when no Buttons have been registered
        - `ButtonsMenuException`: The `ButtonsMenu` menu_type was not recognized or there was an issue with locating the :param:`send_to` channel if set
        - `DescriptionOversized`: When using a menu_type of `ButtonsMenu.TypeEmbedDynamic`, the embed description was over discords size limit
        - `IncorrectType`: Parameter :param:`send_to` was not :class:`str`, :class:`int`, or :class:`discord.TextChannel`
        """
        # ------------------------------- CHECKS -------------------------------

        # before the menu starts, ensure the "components" kwarg is implemented inside the `_ctx.send` method. If it's missing, raise an error (the menu cannot function without it)
        send_info = inspect.getfullargspec(self._ctx.send)
        if 'components' not in send_info.kwonlyargs:
            raise MissingSetting('The "components" kwarg is missing from the .send() method. Did you forget to initialize the menu first using static method ButtonsMenu.initialize(...)?')

        # ensure at least 1 page exists before starting the menu
        if self._menu_type in (ButtonsMenu.TypeEmbed, ButtonsMenu.TypeText) and not self.__pages:
            raise NoPages("You cannot start a ButtonsMenu when you haven't added any pages")
        
        # ensure at least 1 button exists before starting the menu
        if not self._row_of_buttons:
            raise NoButtons('You cannot start a ButtonsMenu when no buttons are registered')
        
        # ensure only valid menu types have been set
        if self._menu_type not in (ButtonsMenu.TypeEmbed, ButtonsMenu.TypeEmbedDynamic, ButtonsMenu.TypeText):
            raise ButtonsMenuException('ButtonsMenu menu_type not recognized')
        
        # ------------------------------- END CHECKS -------------------------------

        # add page (normal menu)
        if self._menu_type == ButtonsMenu.TypeEmbed:
            self._refresh_page_director_info(ButtonsMenu.TypeEmbed, self.__pages)
            self._msg = await self._handle_send_to(send_to).send(embed=self.__pages[0], components=[ActionRow(*self._row_of_buttons)]) # allowed_mentions not needed in embeds
        
        # add row (dynamic menu)
        elif self._menu_type == ButtonsMenu.TypeEmbedDynamic:
            for data_clump in self._chunks(self._dynamic_data_builder, self.__rows_requested):
                joined_data = '\n'.join(data_clump)
                if len(joined_data) <= 2000:
                    possible_block = f"```{self.wrap_in_codeblock}\n{joined_data}```"
                    embed = discord.Embed() if self.custom_embed is None else self.custom_embed.copy()
                    embed.description = joined_data if not self.wrap_in_codeblock else possible_block
                    self.__pages.append(embed)
                else:
                    raise DescriptionOversized('With the amount of data that was recieved, the embed description is over discords size limit. Lower the amount of "rows_requested" to solve this problem')
            else:
                # set the main/last pages if any
                if any((self._main_page_contents, self._last_page_contents)):
                    self.__pages = collections.deque(self.__pages)
                    if self._main_page_contents:
                        self._main_page_contents.reverse()
                        self.__pages.extendleft(self._main_page_contents)
                    
                    if self._last_page_contents:
                        self.__pages.extend(self._last_page_contents)
                
                self._refresh_page_director_info(ButtonsMenu.TypeEmbedDynamic, self.__pages)

                # make sure data has been added to create at least 1 page
                if not self.__pages: raise NoPages('You cannot start a ButtonsMenu when no data has been added')
                
                self._msg = await self._handle_send_to(send_to).send(embed=self.__pages[0], components=[ActionRow(*self._row_of_buttons)]) # allowed_mentions not needed in embeds
        
        # add page (text menu)
        else:
            self._refresh_page_director_info(ButtonsMenu.TypeText, self.__pages)
            self._msg = await self._handle_send_to(send_to).send(content=self.__pages[0], components=[ActionRow(*self._row_of_buttons)], allowed_mentions=self.allowed_mentions)
        
        self._pc = _PageController(self.__pages)
        self._is_running = True
        self._main_session_task = asyncio.get_event_loop().create_task(self._execute_interactive_session())
        self._main_session_task.add_done_callback(self._done_callback)
