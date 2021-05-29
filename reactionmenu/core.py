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
from enum import Enum, auto
import itertools
from typing import List, Union, Deque

from discord import Embed, TextChannel, Member, Role
from discord.ext.commands import Context

from . import abc
from .buttons import Button, ButtonType
from .decorators import *
from .errors import *

class ReactionMenu(abc.Menu):
	"""A class to create a discord.py reaction menu. If discord.py version is 1.5.0+, intents are required
	
	Parameters
	----------
	ctx: :class:`discord.ext.commands.Context`
		The Context object. You can get this using a command or if in `discord.on_message`

	back_button: :class:`str`
		Button used to go to the previous page of the menu

	next_button: :class:`str`
		Button used to go to the next page of the menu

	config: :class:`int`
		The menus core function to set. Class variables :attr:`ReactionMenu.STATIC` or :attr:`ReactionMenu.DYNAMIC`

	Options [kwargs]
	----------------
	rows_requested: :class:`int`
		The amount of information per :meth:`ReactionMenu.add_row()` you would like applied to each embed page (dynamic only/defaults to :class:`None`)

	custom_embed: :class:`discord.Embed`
		Embed object to use when adding data with :meth:`ReactionMenu.add_row()`. Used for styling purposes (dynamic only/defaults to :class:`None`)

	wrap_in_codeblock: :class:`str`
		The discord codeblock language identifier (dynamic only/defaults to :class:`None`). Example: `ReactionMenu(ctx, ..., wrap_in_codeblock='py')`

	clear_reactions_after: :class:`bool`
		If the menu times out, remove all reactions (defaults to `True`)

	timeout: Union[:class:`float`, :class:`None`]
		Timer for when the menu should end. Can be :class:`None` for no timeout (defaults to 60.0)

	show_page_director: :class:`bool`
		Shown at the botttom of each embed page. "Page 1/20" (defaults to `True`)

	name: :class:`str`
		A name you can set for the menu (defaults to :class:`None`)

	style: :class:`str`
		A custom page director style you can select. "$" represents the current page, "&" represents the total amount of pages (defaults to "Page $/&") Example: `ReactionMenu(ctx, ..., style='On $ out of &')`

	all_can_react: :class:`bool`
		Sets if everyone is allowed to control when pages are 'turned' when buttons are pressed (defaults to `False`)

	delete_interactions: :class:`bool`
		Delete the prompt message by the bot and response message by the user when asked what page they would like to go to when using `ButtonType.GO_TO_PAGE` (defaults to `True`)

	navigation_speed: :class:`str`
		Sets if the user needs to wait for the reaction to be removed by the bot before "turning" the page. Setting the speed to :attr:`ReactionMenu.FAST` makes it so that there is no need to wait (reactions are not removed on each press) and can
		navigate lengthy menu's more quickly (defaults to `ReactionMenu.NORMAL`)
	
	delete_on_timeout: :class:`bool`
		When the menu times out, delete the menu message. This overrides :attr:`clear_reactions_after` (defaults to `False`)
	
	only_roles: List[:class:`discord.Role`]
        Members with any of the provided roles are the only ones allowed to control the menu. The member who started the menu will always be able to control it. This overrides :attr:`all_can_react` (defaults to :class:`None`)

		.. changes::
			v1.0.1
				Added :attr:_active_sessions
				Added :attr:_sessions_limit
				Added :attr:_task_sessions_pool
			v1.0.2
				Added :attr:_delete_interactions
			v1.0.5
				Added :attr:_navigation_speed
				Added :attr:NORMAL
				Added :attr:FAST
			v1.0.6
				Added :attr:_custom_embed_set
				Added :attr:_send_to_channel
			v1.0.8
				Added :attr:_delete_on_timeout
			v1.0.9
				Added :attr:_only_roles
				Added :attr:_menu_owner
				Added :attr:_auto_paginator
				Added :attr:_auto_turn_every
				Added :attr:_auto_worker
				Added :attr:_main_session_task
				Added :attr:_runtime_tracking_task
				Added :attr:_countdown_task
				Added :attr:_limit_message
				Added :attr:_default_back_button
				Added :attr:_default_next_button
				Added :attr:_all_buttons_removed
				Added :attr:_is_dm_session
				Added :attr:_relay_function

				
				This class now inherits from :abc:`Menu`
				
				A sizeable amount of methods and properties were moved from here to abc.py to support :class:`TextMenu`

	"""
	STATIC = 0
	DYNAMIC = 1
	
	_active_sessions: List['ReactionMenu'] = []
	_sessions_limit = None
	_task_sessions_pool: List[asyncio.Task] = []
	_limit_message: str = ''

	def __init__(self, ctx: Context, *, back_button: str, next_button: str, config: int, **options): 
		self._ctx = ctx
		self._send_to_channel = None
		self._config = config
		self._bot = ctx.bot
		self._loop = ctx.bot.loop
		self._msg = None
		self._is_running = False
		self._default_back_button: Button = Button(emoji=back_button, linked_to=ButtonType.PREVIOUS_PAGE, name='default back button')
		self._default_next_button: Button = Button(emoji=next_button, linked_to=ButtonType.NEXT_PAGE, name='default next button')
		self._all_buttons: List[Button] = [self._default_back_button, self._default_next_button]
		self._current_page = 0
		self._last_page = 0
		self._run_time = 0
		self._all_buttons_removed = False
		self._is_dm_session = False
		self._relay_function = None

		# auto-pagination
		self._menu_owner = None
		self._auto_paginator = False
		self._auto_turn_every = None
		self._auto_worker = None

		# tasks
		self._main_session_task: asyncio.Task = None
		self._runtime_tracking_task: asyncio.Task = None
		self._countdown_task: asyncio.Task = None
		
		# dynamic session
		self._dynamic_data_builder: List[str] = []
		self._dynamic_completed_pages: Deque[Embed] = collections.deque()
		self._rows_requested: int = options.get('rows_requested')
		self._custom_embed: Embed = options.get('custom_embed')
		self._custom_embed_set: bool = False if self._custom_embed is None else True
		self._wrap_in_codeblock = options.get('wrap_in_codeblock')
		self._main_pages_already_set = False
		self._last_pages_already_set = False
		self._last_page_contents = None
		
		# static session
		self._static_completed_pages: List[Embed] = []
	
		# misc options
		self._only_roles: List[Role] = options.get('only_roles')
		self._clear_reactions_after: bool = options.get('clear_reactions_after', True)
		self._timeout: Union[float, None] = options.get('timeout', 60.0)
		self._show_page_director: bool = options.get('show_page_director', True)
		self._name: str = options.get('name')
		self._style: str = options.get('style')
		self._all_can_react: bool = options.get('all_can_react', False)
		self._delete_interactions: bool = options.get('delete_interactions', True)
		self._navigation_speed: str = options.get('navigation_speed', ReactionMenu.NORMAL)
		self._delete_on_timeout: bool = options.get('delete_on_timeout', False)
		
	@property
	def config(self) -> int:
		"""
		Returns
		-------
		:class:`int`:
			The config of the menu is either `ReactionMenu.STATIC` (a value of 0), or `ReactionMenu.DYNAMIC` (a value of 1)
		"""
		return self._config

	@property
	def custom_embed_buttons(self) -> List[Button]:
		"""
		Returns
		-------
		List[:class:`Button`]:
			Can return :class:`None` if no custom embed buttons have been set
		"""
		temp = self._custom_linked_embeds()
		return temp if temp else None

	@property
	def total_pages(self) -> int:
		"""With a dynamic menu, the total pages isn't known until AFTER the menu has started

		Returns
		-------
		:class:`int`:
			The amount of pages on the menu

			.. added:: v1.0.1

			.. changes::
				v1.0.9
					Moved to ABC
		"""
		if self._config == ReactionMenu.STATIC:
			return len(self._static_completed_pages)
		elif self._config == ReactionMenu.DYNAMIC:
			return len(self._dynamic_completed_pages)

	@property
	def rows_requested(self) -> int:
		"""
		Returns
		-------
		:class:`int`:
			The amount of rows that was set for a dynamic menu
		"""
		return self._rows_requested
	
	@property
	def custom_embed(self) -> Embed:
		return self._custom_embed

	@custom_embed.setter
	def custom_embed(self, value):
		"""A property getter/setter for kwarg "custom_embed"
		
		Example
		-------
		```
		menu = ReactionMenu(...)
		menu.custom_embed = discord.Embed(color=discord.Color.red())
		```
		Returns
		-------
		:class:`discord.Embed`:
			If not set, defaults to :class:`None`

			.. changes::
				v1.0.6
					Added :attr:_custom_embed_set
		"""
		if isinstance(value, Embed):
			self._custom_embed = value
			self._custom_embed_set = True
		else:
			raise IncorrectType(f'"custom_embed" expected discord.Embed, got {value.__class__.__name__}')
	
	@property
	def wrap_in_codeblock(self) -> str:
		return self._wrap_in_codeblock

	@wrap_in_codeblock.setter
	def wrap_in_codeblock(self, value):
		"""A property getter/setter for kwarg "wrap_in_codeblock"
		
		Example
		-------
		```
		menu = ReactionMenu(...)
		menu.wrap_in_codeblock = 'py'
		>>> print(menu.wrap_in_codeblock)
		py
		```
		Returns
		-------
		:class:`str`:
			If not set, defaults to :class:`None`
		"""
		if isinstance(value, str):
			self._wrap_in_codeblock = value
		else:
			raise IncorrectType(f'"wrap_in_codeblock" expected str, got {value.__class__.__name__}')

	def _maybe_custom_embed(self) -> Embed:
		"""If a custom embed is set, return it
		
			.. changes::
				v1.0.6
					Replaced the if statement. Caused an issue where if there was no title in the embed, other things such as the color, timestamp, thumbnail, etc. would not be displayed. 
		"""
		if self._custom_embed_set:
			temp = self._custom_embed.copy()
			temp.description = Embed.Empty
			return temp
		else:
			return Embed()
	
	def _maybe_last_pages(self):
		"""When a dynamic menu has started, check if last_pages have been added. If not, add them to :attr:_dynamic_completed_pages"""
		if self._last_page_contents:
			self._dynamic_completed_pages.extend(self._last_page_contents)

	def _chunks(self, list_, n):
		"""Yield successive n-sized chunks from list. Core component of a dynamic menu"""
		for i in range(0, len(list_), n):
			yield list_[i:i + n]

	@dynamic_only
	@ensure_not_primed
	def clear_all_row_data(self):
		"""Delete all the data thats been added using :meth:`ReactionMenu.add_row()`
		
		Raises
		------
		- `MenuSettingsMismatch`: Tried to use method on a static menu
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		"""
		self._dynamic_data_builder.clear()

	@dynamic_only
	@ensure_not_primed
	def add_row(self, data: str):
		"""Used when the menu is set to dynamic. Apply the data recieved to a row in the embed page

		Parameter
		---------
		data: :class:`str`
			The information to add to the menu 
		
		Raises
		------
		- `MissingSetting`: kwarg "rows_requested" was missing from the :class:`ReactionMenu` constructor
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		- `MenuSettingsMismatch`: Tried to use method on a static menu
		"""
		if self._rows_requested:
			self._dynamic_data_builder.append(str(data))
		else:
			raise MissingSetting(f'ReactionMenu kwarg "rows_requested" (int) has not been set')
						
	@static_only
	@ensure_not_primed
	def remove_page(self, page_number: int):
		"""On a static menu, delete a certain page that has been added
		
		Parameter
		---------
		page_number: :class:`int`
			The page to remove
		
		Raises
		------
		- `InvalidPage`: Page not found
		- `MenuSettingsMismatch`: Tried to use method on a dynamic menu
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		"""
		pages_count = len(self._static_completed_pages)
		if page_number <= 0 or page_number > pages_count:
			raise InvalidPage(f'There are currently {pages_count} pages. You need to delete a page between 1-{pages_count}')
		else:
			del self._static_completed_pages[page_number - 1]
	
	@dynamic_only
	@ensure_not_primed
	def set_main_pages(self, *embeds: Embed):
		"""On a dynamic menu, set the pages you would like to show first. These embeds will be shown before the embeds that contain your data
		
		Parameter
		---------
		*embeds: :class:`discord.Embed`
			An argument list of :class:`discord.Embed` objects
		
		Raises
		------
		- `MenuSettingsMismatch`: Tried to use method on a static menu
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		- `SingleUseOnly`: Attempted to call method more than once
		- `ReactionMenuException`: The "embeds" parameter was empty. At least one value is needed

			.. changes::
				v1.0.9
					Added an if check so it's not possible to set main pages with no embeds 
		"""
		if not embeds:
			raise ReactionMenuException('When setting the main pages, the "embeds" parameter was empty')
		
		if not self._main_pages_already_set:
			embeds = collections.deque(embeds)
			embeds.reverse()
			self._dynamic_completed_pages.extendleft(embeds)
			self._main_pages_already_set = True
		else:
			raise SingleUseOnly("Once you've set main pages, you cannot set more")

	@dynamic_only
	@ensure_not_primed
	def set_last_pages(self, *embeds: Embed):
		"""On a dynamic menu, set the pages you would like to show last. These embeds will be shown after the embeds that contain your data
		
		Parameter
		---------
		*embeds: :class:`discord.Embed`
			An argument list of :class:`discord.Embed` objects
		
		Raises
		------
		- `MenuSettingsMismatch`: Tried to use method on a static menu
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		- `SingleUseOnly`: Attempted to call method more than once
		- `ReactionMenuException`: The "embeds" parameter was empty. At least one value is needed

			.. changes::
				v1.0.9
					Added an if check so it's not possible to set last pages with no embeds
		"""
		if not embeds:
			raise ReactionMenuException('When setting the last pages, the "embeds" parameter was empty')

		if not self._last_pages_already_set:
			embeds = collections.deque(embeds)
			self._last_page_contents = embeds
			self._last_pages_already_set = True
		else:
			raise SingleUseOnly("Once you've set last pages, you cannot set more")

	@static_only
	@ensure_not_primed
	def clear_all_pages(self):
		"""On a static menu, delete all pages that have been added
		
		Raises
		------
		- `MenuSettingsMismatch`: Tried to use method on a dynamic menu
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		"""
		self._static_completed_pages.clear()

	@static_only
	@ensure_not_primed
	def clear_all_custom_pages(self):
		"""On a static menu, delete all custom pages that have been added
		
		Raises
		------
		- `MenuSettingsMismatch`: Tried to use method on a dynamic menu
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		"""
		for cb in self._custom_linked_embeds():
			self._all_buttons.remove(cb)
    
	@static_only
	@ensure_not_primed
	def add_page(self, embed: Embed):
		"""On a static menu, add a page
		
		Parameter
		---------
		embed: :class:`discord.Embed`
			An Embed object
		
		Raises
		------
		- `MenuSettingsMismatch`: Tried to use method on a dynamic menu
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		- `DescriptionOversized`: Description length is over discords character limit
		"""
		if len(embed.description) <= 2000:
			self._static_completed_pages.append(embed)
		else:
			raise DescriptionOversized('When adding a page, your embed description was over the size limit allowed by Discord. Reduce the amount of text in your embed description')

	@ensure_not_primed
	def add_button(self, button: Button): 
		"""Adds a button to the menu. Buttons can also be linked to custom embeds. So when you click the emoji you've assigned, it goes to that page and is seperate from the normal menu
		
		Parameter
		---------
		button: :class:`Button`
			The button to instantiate.
		
		Raises
		------
		- `MenuAlreadyRunning`: Attempted to call this method after the menu has started
		- `MissingSetting`: Set the Button :param:`linked_to` as `ButtonType.CUSTOM_EMBED`/`ButtonType.CALLER` but did not assign the Button kwarg "embed"/"details" a value
		- `DuplicateButton`: The emoji used is already registered as a button
		- `TooManyButtons`: More than 20 buttons were added. Discord has a reaction limit of 20
		- `ReactionMenuException`: A name used for the Button is already registered

			.. changes::
				v1.0.3
					Added check for ButtonType.CALLER
				v1.0.9
					Added if check for :attr:`_all_buttons_removed`
					Moved to ABC
		"""
		if button.emoji not in self._extract_all_emojis():
			if button.linked_to is ButtonType.CUSTOM_EMBED and not button.custom_embed:
				raise MissingSetting('When adding a button with the type "ButtonType.CUSTOM_EMBED", the kwarg "embed" is needed')

			if button.linked_to is ButtonType.CUSTOM_EMBED and self._config == ReactionMenu.DYNAMIC:
				raise MenuSettingsMismatch('You cannot add a button with a linked_to of "ButtonType.CUSTOM_EMBED" on a dynamic menu. Consider using ReactionMenu.set_main_pages or ReactionMenu.set_last_pages instead') 
			
			if button.linked_to is not ButtonType.CUSTOM_EMBED and button.custom_embed:
				raise MenuSettingsMismatch('Button is not set as "ButtonType.CUSTOM_EMBED" but the embed kwarg of that button was set')

			# if the Button has a name, make sure its not a dupliate name
			if button.name in [btn.name for btn in self._all_buttons if btn.name]:
				raise ReactionMenuException('There cannot be duplicate names when setting the name for a Button')

			if button.linked_to is ButtonType.CALLER and not button.details:
				raise MissingSetting('When adding a button with the type "ButtonType.CALLER", the kwarg "details" for that Button must be set.')

			self._all_buttons.append(button)
			if len(self._all_buttons) > 20:
				raise TooManyButtons

			if self._all_buttons_removed:
				self._all_buttons_removed = False
		else:
			raise DuplicateButton(f'The emoji {tuple(button.emoji)} has already been registered as a button')
	
	def _custom_linked_embeds(self) -> List[Button]:
		"""Returns a list of :class:`Button` that have embeds linked to them"""
		return [button for button in self._all_buttons if button.linked_to is ButtonType.CUSTOM_EMBED]
	
	def _regular_buttons(self) -> List[Button]:
		"""Returns a list of :class:`Button` that do not have the type `ButtonType.CUSTOM_EMBED`"""
		return [button for button in self._all_buttons if button.linked_to is not ButtonType.CUSTOM_EMBED]
	
	def _actual_embeds(self) -> List[Embed]:
		"""Returns a list of the embed objects that are available from a linked button"""
		return [button.custom_embed for button in self._custom_linked_embeds()]
	
	def _refresh_page_director_info(self, worker):
		"""Sets the page count at the bottom of embeds if activated"""
		if self._show_page_director:
			page = 1
			outof = len(worker)
			for embed in worker:
				embed.set_footer(text=f'{self._maybe_new_style(page, outof)}{":" if embed.footer.text else ""} {embed.footer.text if embed.footer.text else ""}', icon_url=embed.footer.icon_url)
				page += 1

	def _set_proper_page(self):
		"""When the menu is in an active session, this protects the menu pagination index from going out of bounds (IndexError)"""
		if self._current_page < 0:
			self._current_page = self._last_page
		elif self._current_page > self._last_page:
			self._current_page = 0
	
	async def _execute_navigation_type(self, worker, emoji, **kwargs):
		"""|abc coro| This controls whether the user has to wait until the emoji is removed from the message by the :class:`discord.Client` in order to continue 'turning' pages in the menu session. 
		:attr:`ReactionMenu.NORMAL` indicates the user has to wait for the :class:`discord.Client` to remove the reaction. :attr:`ReactionMenu.FAST` indicates no wait is needed and is 
		processed on each `reaction_add` and `reaction_remove`. In v1.0.0 - v1.0.4, the handling of each button press was processed in :meth:`ReactionMenu._execute_session`. This replaces that
		so each button press is also handled through here now as :attr:`ReactionMenu.NORMAL`, as well as the handling of :attr:`ReactionMenu.FAST`

		Kwargs
		------
		- from_custom_button: :class:`bool` Handles the editing process with interactions from :attr:`ButtonType.CUSTOM_EMBED`		
		- from_caller_button: :class:`bool` Handles the editing process with interactions from :attr:`ButtonType.CALLER`
			
			.. added:: v1.0.5

			.. changes::
				v1.0.9
					Moved to ABC
		"""
		from_custom_button = kwargs.get('from_custom_button', False)
		from_caller_button = kwargs.get('from_caller_button', False)

		if self._navigation_speed == ReactionMenu.NORMAL:
			if from_custom_button:
				await self._msg.edit(embed=worker)
				await self._msg.remove_reaction(emoji, self._ctx.author)
			elif from_caller_button:
				await self._msg.remove_reaction(emoji, self._ctx.author)
			else:
				await self._msg.edit(embed=worker[self._current_page])
				await self._msg.remove_reaction(emoji, self._ctx.author)
		
		elif self._navigation_speed == ReactionMenu.FAST:
			if from_custom_button:
				await self._msg.edit(embed=worker)
			elif from_caller_button:
				# dont do anything here because :meth:`ReactionMenu._execute_session` handles the actual calling. this just ensures theres no ~remove_reaction being done
				# NOTE: See the text.py > :class:`TextMenu` > :meth:`_execute_navigation_type` comment for this. Gives a little more info as to why I am doing this
				pass
			else:
				await self._msg.edit(embed=worker[self._current_page])
	
	def refresh_auto_pagination_data(self, *embeds: Embed):
		"""Update the embeds displayed in the auto-pagination menu. When refreshed, the new embeds don't go into effect until the last round of waiting (what you set for `turn_every`) completes

		Parameters
		----------
		*embeds: :class:`discord.Embed`
			An argument list of :class:`discord.Embed` objects
		
		Raises
		------
		- `ReactionMenuException`: The menu was not set as an auto-paginator menu
		- `IncorrectType`: All values in the argument list were not of type :class:`discord.Embed`

			.. added:: v1.0.9
		"""
		if self._auto_paginator:
			if all([isinstance(e, Embed) for e in embeds]):
				self._auto_worker = itertools.cycle(embeds)
			else:
				raise IncorrectType('Parameter "embeds" expected only discord.Embed values. One or more values were not of type discord.Embed')
		else:
			raise ReactionMenuException('Menu is not set as auto-paginator')
	
	async def _execute_auto_session(self, worker):
		"""|abc coro| Begin the auto-pagination process. This also starts the background task for the countdown to timeout
		
			.. added:: v1.0.9
		"""
		# convert it from a :class:`collections.deque` to a :class:`list`
		worker = list(worker)

		if self._config == ReactionMenu.STATIC:
			embed_buttons = self.custom_embed_buttons
			if embed_buttons:
				embeds = [btn.custom_embed for btn in embed_buttons]
				worker.extend(embeds)
			
			worker = itertools.cycle(worker)
		
		elif self._config == ReactionMenu.DYNAMIC:
			worker = itertools.cycle(self._dynamic_completed_pages)

		self._auto_worker = worker

		# when the initial message is sent, the user already sees the first page. doing a single next()
		# before the auto-pagination process begins allows the menu to display the second page after waiting on 
		# :attr:`ReactionMenu._auto_turn_every`
		next(self._auto_worker)

		# since reactions will not be used during the auto-pagination process, there's no reason to have :class:`Button` objects in the list
		self._all_buttons.clear()

		self._countdown_task = self._loop.create_task(self._auto_countdown())
		
		while self._is_running:
			await asyncio.sleep(self._auto_turn_every)
			await self._msg.edit(embed=next(self._auto_worker))
		
	async def _execute_session(self, worker):
		"""|abc coro| Begin the pagination process

			.. changes::
				v1.0.1
					Added go to page functionality
				v1.0.2
					Added optional delete prompt and message interactions
				v1.0.3
					Added ButtonType.CALLER functionality	
				v1.0.5
					Moved the use of :meth:`_msg.edit` and :meth:`_msg.remove_reaction` to :meth:`ReactionMenu._execute_navigation_type`
				v1.0.8
					Added :attr:`ReactionMenu._delete_on_timeout` functionality
				v1.0.9
					- Added the initialization of :attr:`ReactionMenu._menu_owner` for proper handling in :meth:`Menu._wait_check`
					- Added handling for relays
					- Replaced the end session and timeout actions to :meth:`ReactionMenu.stop`. Stop does all the necessary things needed to properly stop a menu
					- Instead of calling str() everytime on every button emoji check, just store it in a variable to access and check later
					- Moved to ABC
					- Fixed issue associated with `ButtonType.GO_TO_PAGE` and kwarg `send_to` in :meth:`ReactionMenu.start`
		"""
		self._menu_owner = self._ctx.author
		while self._is_running:
			try:
				if self._navigation_speed == ReactionMenu.NORMAL:
					reaction, user = await self._bot.wait_for('reaction_add', check=self._wait_check, timeout=self._timeout)
				elif self._navigation_speed == ReactionMenu.FAST:
					reaction, user = await self._handle_fast_navigation()
				else:
					raise ReactionMenuException(f'Navigation speed {self._navigation_speed!r} is not recognized')
			except asyncio.TimeoutError:
				await self.stop(delete_menu_message=self._delete_on_timeout, clear_reactions=self._clear_reactions_after)
			else:
				emoji = str(reaction.emoji)

				for btn in self._all_buttons:
					# previous
					if emoji == btn.emoji and btn.linked_to is ButtonType.PREVIOUS_PAGE:
						self._current_page -= 1
						self._set_proper_page()
						await self._execute_navigation_type(worker, btn.emoji)
						await self._contact_relay(user, btn)
						break
					
					# next
					elif emoji == btn.emoji and btn.linked_to is ButtonType.NEXT_PAGE:
						self._current_page += 1
						self._set_proper_page()
						await self._execute_navigation_type(worker, btn.emoji)
						await self._contact_relay(user, btn)
						break
					
					# first page
					elif emoji == btn.emoji and btn.linked_to is ButtonType.GO_TO_FIRST_PAGE:
						self._current_page = 0
						await self._execute_navigation_type(worker, btn.emoji)
						await self._contact_relay(user, btn)
						break

					# last page
					elif emoji == btn.emoji and btn.linked_to is ButtonType.GO_TO_LAST_PAGE:
						self._current_page = self._last_page
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
							msg = await self._bot.wait_for('message', check=check, timeout=self._timeout)
						except asyncio.TimeoutError:
							break
						else:
							try:
								requested_page = int(msg.content)
							except ValueError:
								break
							else:
								if requested_page >= 1 and requested_page <= self.total_pages:
									self._current_page = requested_page - 1
									await self._execute_navigation_type(worker, btn.emoji)
									await self._contact_relay(user, btn)
									if self._delete_interactions:
										await bot_prompt.delete()
										await msg.delete()
									break
					
					# custom buttons
					elif emoji == btn.emoji and btn.linked_to is ButtonType.CUSTOM_EMBED:
						await self._execute_navigation_type(btn.custom_embed, btn.emoji, from_custom_button=True)
						await self._contact_relay(user, btn)
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
		"""|coro| Starts the reaction menu

		Parameter
		---------
		send_to: Union[:class:`str`, :class:`int`, :class:`discord.TextChannel`]
			(optional) The channel you'd like the menu to start in. Use the channel name, ID, or it's object. Please note that if you intend to use a text channel object, using
			method :meth:`discord.Client.get_channel`, that text channel should be in the same list as if you were to use `ctx.guild.text_channels`. This only works on a context guild text channel basis. That means a menu instance cannot be
			created in one guild and the menu itself (:param:`send_to`) be sent to another. Whichever guild context the menu was instantiated in, the text channels of that guild are the only options for :param:`send_to` (defaults to :class:`None`)
		
		Example for :param:`send_to`
		---------------------------
		```
		menu = ReactionMenu(...)
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
		- `MenuSettingsMismatch`: The wrong number was used in the "config" parameter. only 0 (`ReactionMenu.STATIC`) or 1 (`ReactionMenu.DYNAMIC`) are permitted
		- `NoButtons`: Attempted to start the menu when no Buttons have been registered
		- `ReactionMenuException`: A duplicate Button emoji/name was used

			.. changes::
				v1.0.3
					Added task callbacks
				v1.0.5
					Added duplication check methods

					Added unique ID's to task names so multiple sessions can be ran/stopped in a single execution. So if :meth:`ReactionMenu.stop` is called during that execution, it knows exactly which menu instance to stop.
					Unlike before where the menu instance task name would be identified simply as static or dynamic, and with multiple instances ran from a single execution having the same task name, calling :meth:`ReactionMenu.stop`
					could stop the wrong menu instance
				v1.0.6
					Added :param:`send_to`
					Added :meth:`ReactionMenu._determine_location` and if checks to determine if the menu should start in the same channel as :attr:`ReactionMenu._ctx` or another channel (:attr:`ReactionMenu._send_to_channel`)
				v1.0.9
					- Added handling for :attr:`ReactionMenu._auto_paginator` to determine when to, and when not to apply reactions
					- Added handling for :attr:`ReactionMenu._auto_paginator` to determine when to check for duplicate emojis/names
					- Added handling for menus started in DMs
					- Added decorator `menu_verification`
					- Moved to ABC
					- Removed [else] from ReactionMenu.STATIC/DYNAMIC check
					- Moved #[core menu initialization] from both STATIC and DYNAMIC if checks to only one at the bottom. Having both was redundant because regardless of configuration both have the same #[core menu initialization]
					- Now raises :exc:`NoButtons` (from decorator `menu_verification`)
		"""
		# check if the menu is limited
		if ReactionMenu._is_currently_limited():
			if ReactionMenu._limit_message:
				await self._ctx.send(ReactionMenu._limit_message)
			return
		
		# determine the channel to send the channel to (if any)
		self._determine_location(send_to)
		
		if self._config == ReactionMenu.STATIC:
			worker = []
			# no pages at all
			if len(self._static_completed_pages) == 0 and not self._custom_linked_embeds():
				raise NoPages

			# normal pages, no custom pages
			if len(self._static_completed_pages) >= 2 and not self._custom_linked_embeds():
				worker = self._static_completed_pages
				self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=self._static_completed_pages[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=self._static_completed_pages[0])
				
				if not self._auto_paginator:
					for btn in self._regular_buttons():
						await self._msg.add_reaction(btn.emoji)

				self._last_page = len(worker) - 1

			# normal pages w/ custom pages
			elif len(self._static_completed_pages) >= 2 and self._custom_linked_embeds():
				worker = self._static_completed_pages 
				self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=self._static_completed_pages[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=self._static_completed_pages[0])
				
				if not self._auto_paginator:
					for btn in self._extract_all_emojis():
						await self._msg.add_reaction(btn)
				
				self._last_page = len(worker) - 1

			# no normal pages w/ custom pages (only custom pages)
			elif len(self._static_completed_pages) == 0 and self._custom_linked_embeds():
				worker = self._actual_embeds()
				#self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=worker[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=worker[0])
				
				if not self._auto_paginator:
					for btn in self._custom_linked_embeds():
						await self._msg.add_reaction(btn.emoji)
				
				self._last_page = len(worker) - 1
			
			# only 1 page w/ custom pages
			elif len(self._static_completed_pages) == 1 and self._custom_linked_embeds():
				worker = self._static_completed_pages
				self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=worker[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=worker[0])
				
				if not self._auto_paginator:
					for btn in self._custom_linked_embeds():
						await self._msg.add_reaction(btn.emoji)
					else:
						# even though theres no need for directional buttons (only 1 page), add the back button anyway
						# so the user can navigate back to that single page
						await self._msg.add_reaction(self.default_back_button.emoji)
			
			# only 1 page and no custom pages
			elif len(self._static_completed_pages) == 1 and not self._custom_linked_embeds():
				worker = self._static_completed_pages
				self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=worker[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=worker[0])
			
			if not self._auto_paginator:
				# initiaze end session buttons if any
				end_buttons = self.end_session_buttons
				if end_buttons:
					for end_session_btn in end_buttons:
						await self._msg.add_reaction(end_session_btn.emoji)

		elif self._config == ReactionMenu.DYNAMIC:
			# no data (rows) have been added and no main/last pages have been set
			if len(self._dynamic_data_builder) == 0 and len(self._dynamic_completed_pages) == 0:
				raise NoPages

			# compile all the data that was recieved and add them as embed pages 
			for data_clump in self._chunks(self._dynamic_data_builder, self._rows_requested):
				embed = self._maybe_custom_embed()
				joined_data = '\n'.join(data_clump)
				if len(joined_data) <= 2000:
					possible_block = f"```{self._wrap_in_codeblock}\n{joined_data}```"			
					embed.description = joined_data if not self._wrap_in_codeblock else possible_block
					self._dynamic_completed_pages.append(embed)
				else:
					raise DescriptionOversized('With the amount of data that was recieved, the embed description is over discords size limit. Lower the amount of "rows_requested" to solve this problem')
			else:
				self._maybe_last_pages()
				worker = self._dynamic_completed_pages
				self._refresh_page_director_info(worker)
				if len(worker) >= 2:
					self._msg = await self._ctx.send(embed=worker[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=worker[0])
					
					if not self._auto_paginator:
						# only add regular buttons (non ButtonType.CUSTOM_EMBEDS) because the dynamic equivalent to that is main_pages and last_pages
						for btn in self._regular_buttons():
							await self._msg.add_reaction(btn.emoji)
					
					self._last_page = len(worker) - 1
				else:
					self._msg = await self._ctx.send(embed=worker[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=worker[0])
				
				if not self._auto_paginator:
					# initiaze end session buttons if any
					end_buttons = self.end_session_buttons
					if end_buttons:
						for end_session_btn in end_buttons:
							await self._msg.add_reaction(end_session_btn.emoji)
		
		# core menu initialization
		ReactionMenu._active_sessions.append(self)
		self._is_running = True

		if self._auto_paginator:
			self._main_session_task = self._loop.create_task(self._execute_auto_session(worker))
		else:
			self._main_session_task = self._loop.create_task(self._execute_session(worker))
		
		self._main_session_task.add_done_callback(self._main_session_callback)
		ReactionMenu._task_sessions_pool.append(self._main_session_task)

		self._runtime_tracking_task = self._loop.create_task(self._track_runtime())
