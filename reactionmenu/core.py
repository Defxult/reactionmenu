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
import itertools
from threading import Timer
from typing import List, Union

import discord
from discord.ext.commands import Context

from .abc import BaseMenu, _PageController
from .buttons import ReactionButton
from .decorators import ensure_not_primed
from .errors import *


class ReactionMenu(BaseMenu):
	"""A class to create a discord.py pagination menu using reactions

	Parameters
	----------
	ctx: :class:`discord.ext.commands.Context`
		The Context object. You can get this using a command or if you're in a `discord.on_message` event

	menu_type: :class:`int`
		The configuration of the menu. Class variables :attr:`ReactionMenu.TypeEmbed`, :attr:`ReactionMenu.TypeEmbedDynamic`, or :attr:`ReactionMenu.TypeText`

	Kwargs
	------
	all_can_click: :class:`bool`
		Sets if everyone is allowed to control when pages are 'turned' when buttons are pressed (defaults to `False`)

	allowed_mentions: :class:`discord.AllowedMentions`
		Controls the mentions being processed in the menu message (defaults to :class:`discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=True)`)

	clear_reactions_after: :class:`bool`
		If the menu times out, remove all reactions (defaults to `True`)
	
	custom_embed: :class:`discord.Embed`
		Embed object to use when adding data with :meth:`ReactionMenu.add_row()`. Used for styling purposes (:attr:`ReactionMenu.TypeEmbedDynamic` only/defaults to :class:`None`)

	delete_interactions: :class:`bool`
		Delete the prompt message by the bot and response message by the user when asked what page they would like to go to when using :attr:`ReactionButton.Type.GO_TO_PAGE` (defaults to `True`)

	delete_on_timeout: :class:`bool`
		When the menu times out, delete the menu message. This overrides :attr:`clear_reactions_after` (defaults to `False`)
	
	name: :class:`str`
		A name you can set for the menu (defaults to :class:`None`)

	navigation_speed: :class:`str`
		Sets if the user needs to wait for the reaction to be removed by the bot before "turning" the page. Setting the speed to :attr:`ReactionMenu.FAST` makes it so that there is no need to wait (reactions are not removed on each press) and can
		navigate lengthy menu's more quickly (defaults to :attr:`ReactionMenu.NORMAL`)

	only_roles: List[:class:`discord.Role`]
		Members with any of the provided roles are the only ones allowed to control the menu. The member who started the menu will always be able to control it. This overrides :attr:`all_can_click` (defaults to :class:`None`)
	
	remove_extra_reactions: :class:`bool`
		If `True`, all emojis (reactions) added to the menu message that were not originally added to the menu will be removed (defaults to `False`)

	rows_requested: :class:`int`
		The amount of information per :meth:`ReactionMenu.add_row()` you would like applied to each embed page (:attr:`ReactionMenu.TypeEmbedDynamic` only/defaults to :class:`None`)

	show_page_director: :class:`bool`
		Shown at the botttom of each embed page. "Page 1/20" (defaults to `True`)

	style: :class:`str`
		A custom page director style you can select. "$" represents the current page, "&" represents the total amount of pages (defaults to "Page $/&") Example: `ReactionMenu(ctx, ..., style='On $ out of &')`

	timeout: Union[:class:`float`, :class:`None`]
		Timer for when the menu should end. Can be :class:`None` for no timeout (defaults to 60.0)

	wrap_in_codeblock: :class:`str`
		The discord codeblock language identifier (:attr:`ReactionMenu.TypeEmbedDynamic` only/defaults to :class:`None`). Example: `ReactionMenu(ctx, ..., wrap_in_codeblock='py')`
	"""

	NORMAL = 'NORMAL'
	FAST = 'FAST'

	def __init__(self, ctx: Context, *, menu_type: int, **kwargs):
		super().__init__(ctx, menu_type, **kwargs)

		self._main_session_task: asyncio.Task = None

		# auto-pagination
		self._auto_paginator = False
		self._auto_paginator_timer: Timer = None
		self._auto_turn_every: Union[int, float] = None
		self._auto_data: Union[str, discord.Embed] = None
		
		# kwargs
		self.timeout: Union[float, int, None] = kwargs.get('timeout', 60.0)
		self.clear_reactions_after: bool = kwargs.get('clear_reactions_after', True)
		self.remove_extra_reactions: bool = kwargs.get('remove_extra_reactions', False)
		self.__navigation_speed: str = kwargs.get('navigation_speed', ReactionMenu.NORMAL)
	
	def __repr__(self):
		cls = self.__class__
		return f'<ReactionMenu name={self.name!r} owner={str(self._ctx.author)!r} is_running={self._is_running} timeout={self.timeout} menu_type={cls._get_menu_type(self._menu_type)} auto_paginator={self._auto_paginator}>'
	
	@property
	def navigation_speed(self) -> str:
		"""
		Returns
		-------
		:class:`str`: The current :attr:`navigation_speed` that is set for the menu
		"""
		return self.__navigation_speed
	
	@property
	def auto_paginator(self) -> bool:
		"""
		Returns
		-------
		:class:`bool`: If the menu has been set as an auto-paginator menu
		"""
		return self._auto_paginator
	
	@property
	def auto_turn_every(self) -> Union[int, float]:
		"""
		Returns
		-------
		Union[:class:`int`, :class:`float`]: The turn every value currently set for the auto-pagination menu. Can be :class:`None` if the menu is not an auto-paginator menu
		"""
		return self._auto_turn_every
	
	@classmethod
	def update_all_turn_every(cls, *, turn_every: Union[int, float]):
		"""|class method| Update the amount of seconds to wait before going to the next page for all active auto-paginated sessions. When updated, the new value doesn't go into effect until the last
		round of waiting (:param:`turn_every`) completes for each menu
		
		Warning
		-------
		Setting :param:`turn_every` to a number that's too low exposes you to API abuse because an edit of a message will be occurring too quickly.
		It is your responsibility to make sure an appropriate/safe value is set, *especially* if the menu has a timeout of :class:`None`
		
		Parameters
		----------
		turn_every: Union[:class:`int`, :class:`float`]
			The amount of seconds to wait before going to the next page
		
		Raises
		------
		- `ReactionMenuException`: Parameter :param:`turn_every` was not greater than or equal to one
		"""
		if turn_every >= 1:
			auto_sessions = [session for session in cls._active_sessions if session.auto_paginator]
			for session in auto_sessions:
				session.update_turn_every(turn_every=turn_every)
		else:
			raise ReactionMenuException('Parameter "turn_every" must be greater than or equal to one')
	
	@classmethod
	async def stop_all_auto_sessions(cls):
		"""|coro class method| Stops all auto-paginated sessions that are currently running"""
		auto_sessions = [session for session in cls._active_sessions if session.auto_paginator]
		for session in auto_sessions:
			await session.stop()
	
	def _extract_all_emojis(self) -> List[str]:
		"""Return a list of all the emojis registered to each button. Can return an empty list if there are no buttons"""
		return [button.emoji for button in self._buttons]
	
	async def _handle_event(self, button: ReactionButton):
		"""|coro| If an event is set, remove the buttons from the menu when the click requirement has been met"""
		if button.event:
			event_type = button.event.event_type
			event_value = button.event.value
			if button.total_clicks == event_value:
				if event_type == ReactionButton.Event._remove:
					self._bypass_primed = True
					self.remove_button(button)
					await self._msg.clear_reaction(button.emoji)
	
	def _button_add_check(self, button: ReactionButton):
		if isinstance(button, ReactionButton):
			if button.emoji not in self._extract_all_emojis():
				if button.linked_to == ReactionButton.Type.CUSTOM_EMBED and not button.custom_embed:
					raise MissingSetting('When adding a button with the type "ReactionButton.Type.CUSTOM_EMBED", the kwarg "embed" is needed')
				
				if button.linked_to != ReactionButton.Type.CUSTOM_EMBED and button.custom_embed:
					raise MenuSettingsMismatch('ReactionButton is not set as "ReactionButton.Type.CUSTOM_EMBED" but the "embed" of that button was set')

				if button.linked_to == ReactionButton.Type.CALLER and not button.details:
					raise MissingSetting('When adding a button with the type "ReactionButton.Type.CALLER", the kwarg "details" for that ReactionButton must be set.')
				
				# if the menu_type is TypeText, disallow custom embed buttons
				if self._menu_type == ReactionMenu.TypeText and button.linked_to == ReactionButton.Type.CUSTOM_EMBED:
					raise MenuSettingsMismatch('ReactionButton with a linked_to of ReactionButton.Type.CUSTOM_EMBED cannot be used when the menu_type is TypeText')
				
				if len(self._buttons) > 20:
					raise TooManyButtons
			else:
				raise DuplicateButton(f'The emoji "{button.emoji}" has already been registered as a button')
		else:
			raise IncorrectType(f'Parameter "button" expected ReactionButton, got {button.__class__.__name__}')
	
	def _session_done_callback(self, task: asyncio.Task):
		try:
			task.result()
		except asyncio.CancelledError:
			pass
		finally:
			self._is_running = False
			if self in ReactionMenu._active_sessions:
				ReactionMenu._active_sessions.remove(self)
	
	def get_button(self, identity: Union[str, int], *, search_by: str='name') -> Union[ReactionButton, List[ReactionButton]]:
		"""Get a button that has been registered to the menu by name, emoji, or type

		Parameters
		----------
		identity: :class:`str`
			The button name, emoji, or type

		search_by: :class:`str`
			(optional) How to search for the button. If "name", it's searched by button names. If "emoji", it's searched by it's emojis. 
			If "type", it's searched by :attr:`ReactionMenu.Type`, aka the `linked_to` of the button (defaults to "name")

		Raises
		------
		- `ReactionMenuException`: Parameter :param:`search_by` was not "name", "emoji", or "type"

		Returns
		-------
		Union[:class:`ReactionButton`, List[:class:`ReactionButton`]]:
			The button(s) matching the given identity. Can be :class:`None` if the button was not found
		"""
		search_by = str(search_by).lower()
		if search_by in ('name', 'emoji'):
			identity = str(identity)

		if search_by == 'name':
			matched_names = [btn for btn in self._buttons if btn.name == identity]
			if matched_names:
				return matched_names[0] if len(matched_names) == 1 else matched_names
			else:
				return None

		elif search_by == 'emoji':
			for btn in self._buttons:
				if btn.emoji == identity:
					return btn
			return None
		
		elif search_by == 'type':
			matched_types = [btn for btn in self._buttons if btn.linked_to == identity]
			if matched_types:
				return matched_types[0] if len(matched_types) == 1 else matched_types
			else:
				return None
		
		else:
			raise ReactionMenuException(f'Parameter "search_by" expected "name", "emoji", or "type", got {search_by!r}')

	@ensure_not_primed
	def add_button(self, button: ReactionButton):
		"""Adds a button to the menu. Buttons can also be linked to custom embeds. So when you press the emoji you've assigned, it goes to that page and is separate from the normal menu

		Parameters
		----------
		button: :class:`ReactionButton`
			The button to instantiate

		Raises
		------
		- `MenuAlreadyRunning`: Attempted to call this method after the menu has started
		- `MissingSetting`: Set the buttons `linked_to` as :attr:`ReactionButton.Type.CUSTOM_EMBED` / :attr:`ReactionButton.Type.CALLER` but did not assign the :class:`ReactionButton` kwarg "embed" / "details" a value
		- `DuplicateButton`: The emoji used is already registered as a button
		- `TooManyButtons`: More than 20 buttons were added. Discord has a reaction limit of 20
		"""
		self._button_add_check(button)
		button._menu = self
		self._buttons.append(button)
	
	@ensure_not_primed
	def remove_button(self, button: ReactionButton):
		"""Remove a button from the menu

		Parameters
		----------
		button: :class:`ReactionButton`
			The button to remove

		Raises
		------
		- `MenuAlreadyRunning`: Attempted to call this method after the menu has started
		- `ButtonNotFound`: The provided button was not found in the list of buttons on the menu
		"""
		if button in self._buttons:
			button._menu = None
			self._buttons.remove(button)
		else:
			raise ButtonNotFound('Cannot remove a button that is not registered')
	
	@ensure_not_primed
	def remove_all_buttons(self):
		"""Remove all buttons from the menu
		
		Raises
		------
		- `MenuAlreadyRunning`: Attempted to call this method after the menu has started
		"""
		for btn in self._buttons:
			btn._menu = None
		self._buttons.clear()
	
	def refresh_auto_pagination_data(self, *data: Union[str, discord.Embed]):
		"""Update the data displayed in the auto-pagination menu. When refreshed, the new data doesn't go into effect until the last round of waiting (what you set for `turn_every`) completes
		
		Parameters
		----------
		*data: Union[:class:`str`, :class:`discord.Embed`]
			An argument list of :class:`discord.Embed` objects (`menu_type` is :attr:`TypeEmbed`) or :class:`str` (`menu_type` is :attr:`TypeText`) 
		
		Raises
		------
		- `ReactionMenuException`: The menu was not set as an auto-paginator menu
		- `IncorrectType`: All values in the argument list were not of type :class:`discord.Embed` or :class:`str`
		"""
		if self._auto_paginator and self._is_running:
			if self._menu_type == ReactionMenu.TypeEmbed:
				if all([isinstance(i, discord.Embed) for i in data]):
					self._auto_data = itertools.cycle(data)
				else:
					raise IncorrectType('Parameter "data" expected only discord.Embed values because the current menu_type is TypeEmbed. One or more values were not of type discord.Embed')
			else:
				if all([isinstance(i, str) for i in data]):
					self._auto_data = itertools.cycle(data)
				else:
					raise IncorrectType('Parameter "data" expected only str values because the current menu_type is TypeText. One or more values were not of type str')
		else:
			raise ReactionMenuException('ReactionMenu is not set as auto-paginator')
	
	@ensure_not_primed
	def set_as_auto_paginator(self, *, turn_every: Union[int, float]):
		"""Set the menu to turn pages on it's own every x seconds. If this is set, reactions will not be applied to the menu
		
		Warning
		-------
		Setting :param:`turn_every` to a number that's too low exposes you to API abuse because an edit of a message will be occurring too quickly.
		It is your responsibility to make sure an appropriate/safe value is set, *especially* if the menu has a timeout of :class:`None`
		
		Parameters
		----------
		turn_every: Union[:class:`int`, :class:`float`]
			The amount of seconds to wait before going to the next page
		
		Raises
		------
		- `MenuAlreadyRunning`: Attempted to call this method after the menu has started
		- `ReactionMenuException`: Parameter :param:`turn_every` was not greater than or equal to one
		"""
		if turn_every >= 1:
			self._auto_paginator = True
			self._auto_turn_every = turn_every
		else:
			raise ReactionMenuException('Parameter "turn_every" must be greater than or equal to one')
			
	def update_turn_every(self, *, turn_every: Union[int, float]):
		"""Change the amount of seconds to wait before going to the next page. When updated, the new value doesn't go into effect until the last round of waiting (:param:`turn_every`) completes
		
		Warning
		-------
		Setting :param:`turn_every` to a number that's too low exposes you to API abuse because an edit of a message will be occurring too quickly.
		It is your responsibility to make sure an appropriate/safe value is set, *especially* if the menu has a timeout of :class:`None`
		
		Parameters
		----------
		turn_every: Union[:class:`int`, :class:`float`]
			The amount of seconds to wait before going to the next page
		
		Raises
		------
		- `ReactionMenuException`: Parameter :param:`turn_every` was not greater than or equal to one
		- `MissingSetting`: This method was called from a menu that was not set as an auto-pagination menu
		"""
		if self._auto_paginator:
			if turn_every >= 1:
				self._auto_turn_every = turn_every
			else:
				raise ReactionMenuException('Parameter "turn_every" must be greater than or equal to one')
		else:
			raise MissingSetting('ReactionMenu is not set as auto-paginator')
	
	def _wait_check(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]) -> bool:
		"""Predicate for :meth:`discord.Client.wait_for()`. This also handles :attr:`all_can_click`"""
		not_bot = False
		correct_msg = False
		correct_user = False

		if not user.bot:
			not_bot = True
		
		if reaction.message.id == self._msg.id:
			correct_msg = True

		if self.only_roles:
			if self.all_can_click:
				self.all_can_click = False
			for role in self.only_roles:
				if role in user.roles:
					self._ctx.author = user
					correct_user = True
					break

		if self.all_can_click:
			self._ctx.author = user
			correct_user = True
		
		if user == self._ctx.author and not correct_user:
			self._ctx.author = user
			correct_user = True

		return all([not_bot, correct_msg, correct_user])
	
	async def _handle_fast_navigation(self):
		"""|coro| If either of the below events are dispatched, return the result (reaction, user) of the coroutine object. Used in :meth:`Menu._execute_session()` for :attr:`Menu.FAST`.
		Can timeout, `.result()` raises :class:`asyncio.TimeoutError` but is caught in :meth:`Menu._execute_session()` for proper cleanup. This is the core function as to how the 
		navigation speed system works
		
				.. Note :: Handling of aws's 
					The additional time (+ 0.1) is needed because the items in :var:`wait_for_aws` timeout at the exact same time. Meaning that there will never be an object in :var:`pending` (which is what I want)
					which renders the ~return_when param useless because the first event that was dispatched is stored in :var:`done`. Since they timeout at the same time,
					both aws are stored in :var:`done` upon timeout. 
					
					The goal is to return the result of a single :meth:`discord.Client.wait_for()`, the result is returned but the :exc:`asyncio.TimeoutError`
					exception that was raised in :meth:`asyncio.wait()` (because of the timeout by the other aws) goes unhandled and the exception is raised. The additional time allows the 
					cancellation of the task before the exception (Task exception was never retrieved) is raised 
		"""
		
		def proper_timeout():
			"""In :var:`wait_for_aws`, if the menu does not have a timeout (`Menu.timeout = None`), :class:`None` + :class:`float`, the float being "`self._timeout + 0.1`" from v1.0.5, will fail for obvious reasons. This checks if there is no timeout, 
			and instead of adding those two together, simply return :class:`None` to avoid :exc:`TypeError`. This would happen if the menu's :attr:`Menu.navigation_speed` was set to :attr:`Menu.FAST` and
			the :attr:`Menu.timeout` was set to :class:`None`
			"""
			if self.timeout is not None:
				return self.timeout + 0.1
			else:
				return None

		wait_for_aws = (
			self._ctx.bot.wait_for('reaction_add', check=self._wait_check, timeout=self.timeout),
			self._ctx.bot.wait_for('reaction_remove', check=self._wait_check, timeout=proper_timeout()) 
		)
		done, pending = await asyncio.wait(wait_for_aws, return_when=asyncio.FIRST_COMPLETED)

		temp_pending = list(pending)
		temp_pending[0].cancel()

		temp_done = list(done)
		return temp_done[0].result()
	
	def _get_custom_embed_buttons(self) -> List[ReactionButton]:
		return [btn for btn in self._buttons if btn.linked_to == ReactionButton.Type.CUSTOM_EMBED]
	
	def _get_navigation_buttons(self) -> List[ReactionButton]:
		return [btn for btn in self._buttons if btn.linked_to in (
			ReactionButton.Type.PREVIOUS_PAGE,
			ReactionButton.Type.NEXT_PAGE,
			ReactionButton.Type.GO_TO_FIRST_PAGE,
			ReactionButton.Type.GO_TO_LAST_PAGE,
			ReactionButton.Type.GO_TO_PAGE
		)]
	
	async def _auto_paginate(self, send_to):
		"""|coro| Handles the pagination process for auto-paginator menu's"""
		if self._menu_type in (ReactionMenu.TypeEmbed, ReactionMenu.TypeText):
			
			def stop_auto_pagination():
				"""Called when the :class:`threading.Timer` counter is finished for the auto-session"""
				self._main_session_task.cancel()

			self.remove_all_buttons()
			cycled_pages = itertools.cycle(self._pages)
			send_kwargs = {'embed' if self._menu_type == ReactionMenu.TypeEmbed else 'content' : self._pages[0]}
			
			# when the initial message is sent, the user already sees the first page. doing a single next()
			# before the auto-pagination process begins allows the menu to display the second page after waiting on 
			# :attr:`ReactionMenu._auto_turn_every`
			next(cycled_pages)

			self._msg = await self._handle_send_to(send_to).send(**send_kwargs)
			self._is_running = True
			ReactionMenu._active_sessions.append(self)
			
			if self.timeout:
				timeout = self.timeout
				self._auto_paginator_timer = Timer(timeout, stop_auto_pagination)
				self._auto_paginator_timer.start()
			
			while self._is_running:
				await asyncio.sleep(self._auto_turn_every)
				edit_kwargs = {'embed' if self._menu_type == ReactionMenu.TypeEmbed else 'content' :  next(cycled_pages)}
				try:
					await self._msg.edit(**edit_kwargs)
				except discord.DiscordException as dpy_error:
					if self._auto_paginator_timer is not None and self._auto_paginator_timer.is_alive():
						self._auto_paginator_timer.cancel()
					raise dpy_error # done_callback called
		else:
			raise MenuSettingsMismatch('The menu_type for auto-pagination menus must be TypeEmbed or TypeText')

	async def _paginate(self, ready_event: asyncio.Event):
		"""|coro| Handles the pagination process for all menu types"""
		
		async def determine_removal(emoji: str, user: Union[discord.Member, discord.User]):
			"""|coro| Determines if the reaction should be removed or not depending on the menus :attr:`navigation_speed`"""
			if self.__navigation_speed != ReactionMenu.FAST and self._ctx.guild is not None:
				await self._msg.remove_reaction(emoji, user)
		
		async def update_and_dispatch(emoji: str, user: Union[discord.Member, discord.User], button: ReactionButton):
			"""|coro| Handle reaction removal for :attr:`navigation_speed`. Update the buttons statistics. Contact the relay if one was set and handle any events if set"""
			btn._update_statistics(user)
			await determine_removal(emoji, user)
			await self._handle_event(btn)
			await self._contact_relay(user, btn)

		# apply the reactions (buttons) to the menu message
		for btn in self._buttons:
			await self._msg.add_reaction(btn.emoji)
		
		ready_event.set()
		self._is_running = True
		ReactionMenu._active_sessions.append(self)
		registered_emojis = self._extract_all_emojis()
		
		while self._is_running:
			try:
				if self.__navigation_speed == ReactionMenu.NORMAL:
					reaction, user = await self._ctx.bot.wait_for('reaction_add', check=self._wait_check, timeout=self.timeout)
				elif self.__navigation_speed == ReactionMenu.FAST:
					reaction, user = await self._handle_fast_navigation()
				else:
					raise ReactionMenuException(f'Navigation speed {self.__navigation_speed!r} is not recognized')
			except asyncio.TimeoutError:
				self._menu_timed_out = True
				await self.stop(delete_menu_message=self.delete_on_timeout, clear_reactions=self.clear_reactions_after)
			else:
				emoji = str(reaction.emoji)

				if self.remove_extra_reactions and emoji not in registered_emojis:
					if not self.in_dms:
						await self._msg.clear_reaction(emoji)
						continue

				for btn in self._buttons:
					# previous
					if emoji == btn.emoji and btn.linked_to == ReactionButton.Type.PREVIOUS_PAGE:
						await self._msg.edit(**self._determine_kwargs(self._pc.prev()))
						await update_and_dispatch(emoji, user, btn)
					
					# next
					elif emoji == btn.emoji and btn.linked_to == ReactionButton.Type.NEXT_PAGE:
						await self._msg.edit(**self._determine_kwargs(self._pc.next()))
						await update_and_dispatch(emoji, user, btn)
					
					# first page
					elif emoji == btn.emoji and btn.linked_to == ReactionButton.Type.GO_TO_FIRST_PAGE:
						await self._msg.edit(**self._determine_kwargs(self._pc.first_page()))
						await update_and_dispatch(emoji, user, btn)
					
					# last page
					elif emoji == btn.emoji and btn.linked_to == ReactionButton.Type.GO_TO_LAST_PAGE:
						await self._msg.edit(**self._determine_kwargs(self._pc.last_page()))
						await update_and_dispatch(emoji, user, btn)
					
					# go to page
					elif emoji == btn.emoji and btn.linked_to == ReactionButton.Type.GO_TO_PAGE:
						prompt: discord.Message = await self._msg.channel.send(f'{self._ctx.author.display_name}, what page would you like to go to?')
						try:
							selection_message: discord.Message = await self._ctx.bot.wait_for('message', check=lambda m: all([m.channel.id == self._msg.channel.id, m.author.id == self._ctx.author.id]), timeout=self.timeout)
							page = int(selection_message.content)
						except (asyncio.TimeoutError, ValueError):
							# dont call :meth:`.stop()` here because I want the timeout factor to only be applicable after the
							# original reactions were added
							continue
						else:
							if 1 <= page <= len(self._pages):
								self._pc.index = page - 1
								await self._msg.edit(**self._determine_kwargs(self._pc.current_page))
								if self.delete_interactions:
									await prompt.delete()
									await selection_message.delete()
								
								await update_and_dispatch(emoji, user, btn)
					
					# end session
					elif emoji == btn.emoji and btn.linked_to == ReactionButton.Type.END_SESSION:
						await update_and_dispatch(emoji, user, btn)
						await self.stop(delete_menu_message=True)
					
					# caller buttons
					elif emoji == btn.emoji and btn.linked_to == ReactionButton.Type.CALLER:
						func = btn.details.func
						args = btn.details.args
						kwargs = btn.details.kwargs
						
						try:
							if inspect.iscoroutinefunction(func):
								await func(*args, **kwargs)
							else:
								func(*args, **kwargs)
						except Exception as err:
							raise ReactionMenuException(inspect.cleandoc(
								f"""
								A ReactionButton with a linked_to of ReactionButton.Type.CALLER raised an error during it's execution
								-> {err.__class__.__name__}: {err}
								"""
							))
						else:
							await update_and_dispatch(emoji, user, btn)
						
					# custom buttons
					elif emoji == btn.emoji and btn.linked_to == ReactionButton.Type.CUSTOM_EMBED:
						await update_and_dispatch(emoji, user, btn)
						await self._msg.edit(embed=btn.custom_embed)

	async def stop(self, *, delete_menu_message=False, clear_reactions=False):
		"""|coro| Stops the process of the menu with the option of deleting the menu's message or clearing reactions upon stop"""
		if self._is_running:
			try:
				if delete_menu_message:
					await self._msg.delete()
				elif clear_reactions:
					await self._msg.clear_reactions()
				await self._handle_on_timeout()
			except discord.DiscordException as dpy_error:
				raise dpy_error
			finally:
				if self._auto_paginator:
					if self._auto_paginator_timer is not None and self._auto_paginator_timer.is_alive():
						self._auto_paginator_timer.cancel()
				
				self._main_session_task.cancel()
	
	def _override_dm_settings(self):
		"""If a menu session is in a direct message and the menu is set as an auto-paginator, the following settings are disabled/changed because of discord limitations and resource/safety reasons"""
		if self.in_dms:
			if self.clear_reactions_after:
				self.clear_reactions_after = False
			
			if self.__navigation_speed == ReactionMenu.NORMAL:
				self.__navigation_speed = ReactionMenu.FAST
			
			if self.delete_interactions:
				self.delete_interactions = False
			
			if self.only_roles:
				# this is only type hinted because the type hint gets overridden from `abc` because of the initialization
				self.only_roles: Union[List[discord.Role], None] = None
			
			if self.timeout is None:
				self.timeout = 60.0
			
			if self._auto_paginator:
				self._auto_paginator = False
		
	@ensure_not_primed
	async def start(self, *, send_to: Union[str, int, discord.TextChannel]=None, reply: bool=False):
		"""|coro| Start the menu

		Parameters
		----------
		send_to: Union[:class:`str`, :class:`int`, :class:`discord.TextChannel`]
			(optional) The channel you'd like the menu to start in. Use the channel name, ID, or it's object. Please note that if you intend to use a text channel object, using
			method :meth:`discord.Client.get_channel()` (or any other related methods), that text channel should be in the same list as if you were to use `ctx.guild.text_channels`. This only works on a context guild text channel basis. That means a menu instance cannot be
			created in one guild and the menu itself (:param:`send_to`) be sent to another. Whichever guild context the menu was instantiated in, the text channels of that guild are the only options for :param:`send_to` (defaults to :class:`None`)

		reply: :class:`bool`
			(optional) Enables the menu message to reply to the message that triggered it. Parameter :param:`send_to` must be :class:`None` if this is `True` (defaults to `False`)

		Example for :param:`send_to`
		---------------------------
		Using the `send_to` parameter is optional. Simply calling `menu.start()` will suffice if you want the menu sent to the channel where the command was used/message was sent

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
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		- `NoPages`: The menu was started when no pages have been added
		- `NoButtons`: Attempted to start the menu when no Buttons have been registered
		- `ReactionMenuException`: The :class:`ReactionMenu`'s `menu_type` was not recognized
		- `DescriptionOversized`: When using a `menu_type` of :attr:`ReactionMenu.TypeEmbedDynamic`, the embed description was over discords size limit
		- `IncorrectType`: Parameter :param:`send_to` was not :class:`str`, :class:`int`, or :class:`discord.TextChannel`
		- `MenuException`: The channel set in :param:`send_to` was not found
		"""
		if ReactionMenu._sessions_limited:
			can_proceed = await self._handle_session_limits()
			if not can_proceed:
				return
		
		self._override_dm_settings()
		
		if self._auto_paginator:
			self._main_session_task = self._ctx.bot.loop.create_task(self._auto_paginate(send_to))
			self._main_session_task.add_done_callback(self._session_done_callback)
		else:
			if self._menu_type not in ReactionMenu._all_menu_types():
				raise ReactionMenuException('ReactionMenu menu_type not recognized')
			if not self._buttons:
				raise NoButtons

			reply_kwargs = self._handle_reply_kwargs(send_to, reply)
			
			if self._menu_type == ReactionMenu.TypeEmbed:
				if self._pages:
					self._refresh_page_director_info(self._menu_type, self._pages)
				
				custom_embed_buttons = self._get_custom_embed_buttons()
				# no pages and no custom embeds (no pages at all)
				if not self._pages and not custom_embed_buttons:
					raise NoPages	

				# only custom embeds
				if not self._pages and custom_embed_buttons:
					self._msg = await self._handle_send_to(send_to).send(embed=self._get_custom_embed_buttons()[0].custom_embed, **reply_kwargs)
				else:
					self._msg = await self._handle_send_to(send_to).send(**self._determine_kwargs(self._pages[0]), **reply_kwargs)
			
			elif self._menu_type == ReactionMenu.TypeText:
				if not self._pages:
					raise NoPages
				
				self._refresh_page_director_info(self._menu_type, self._pages)
				self._msg = await self._handle_send_to(send_to).send(content=self._pages[0], allowed_mentions=self.allowed_mentions, **reply_kwargs)
			
			elif self._menu_type == ReactionMenu.TypeEmbedDynamic:
				# page director info is refreshed in method
				await self._build_dynamic_pages(send_to)

			ready_event = asyncio.Event()
			self._pc = _PageController(self._pages)
			self._main_session_task = self._ctx.bot.loop.create_task(self._paginate(ready_event))
			self._main_session_task.add_done_callback(self._session_done_callback)
			await ready_event.wait()
