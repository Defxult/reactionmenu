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
from typing import List, Union, Deque

from discord import Embed, TextChannel
from discord.ext.commands import Context, Command

from .decorators import dynamic_only, static_only, ensure_not_primed
from .errors import *


class ButtonType(Enum):
	"""A helper class for :class:`ReactionMenu`. Determines the generic action a button can perform
	
		.. Changes :: v1.0.1
			- Added :attr:ButtonType.GO_TO_PAGE
		.. Changes :: v1.0.3
			- Added :attr:ButtonType.CALLER
			- Added :meth:caller_details
	"""
	NEXT_PAGE = auto()
	PREVIOUS_PAGE = auto()
	GO_TO_FIRST_PAGE = auto()
	GO_TO_LAST_PAGE = auto()
	GO_TO_PAGE = auto()
	END_SESSION = auto()
	CUSTOM_EMBED = auto()
	CALLER = auto()

	@classmethod
	def caller_details(cls, func, *args, **kwargs) -> tuple:
		"""Registers the function to call as well as it's arguments. Please note that the function you set should not return anything.
		Calling functions with :attr:`ButtonType.CALLER` does not store or handle anything returned by :param:`func`

		Parameter
		---------
		func: `object`
			The function object you want to call when the button is pressed. 
		
		Info
		----
		:param:`*args` and :param:`**kwargs` represents the arguments to be passed to the function.
		
		Example
		-------
		```
		def holiday(location, season, month, *, moto):
			# ...
		
		menu = ReactionMenu(...)
		menu.add_button(Button(emoji='🥶', linked_to=ButtonType.CALLER, details=ButtonType.caller_details(holiday, 'North Pole', 'Winter', 12, moto='hohoho')))
		```

			.. Added v1.0.3

			.. Changes :: v1.0.4
				- Support for commands to be used as functions to call
		"""
		func = func.callback if isinstance(func, Command) else func
		return (func, args, kwargs)


class Button:
	"""A helper class for :class:`ReactionMenu`. Represents a reaction
	
	Parameters
	----------
	emoji: :class:`str`
		The discord reaction that will be used

	linked_to: :class:`ButtonType`
		A generic action a button can perform
	
	Options [kwargs]
	----------------
	embed: :class:`discord.Embed`
		Only used when :param:`linked_to` is set as `ButtonType.CUSTOM_EMBED`. This is the embed that can be selected seperately from the reaction menu (static menu's only)

	name: :class:`str`
		An optional name for the button. Can be set to retrieve it later via :meth:`ReactionMenu.get_button_by_name()`

	details: :meth:`ButtonType.caller_details()`
		The class method used to set the function and it's arguments to be called when the button is pressed

		.. Changes :: v1.0.3
			- Added :attr:details
	"""

	__slots__ = ('emoji', 'linked_to', 'custom_embed', 'details', 'name')

	def __init__(self, *, emoji: str, linked_to: ButtonType, **options):
		self.emoji = emoji
		self.linked_to = linked_to
		self.custom_embed = options.get('embed')
		self.details = options.get('details')
		self.name = options.get('name')
		if self.name:
			self.name = str(self.name).lower()
	
	def __str__(self):
		return self.emoji
	
	def __repr__(self):
		return "<Button emoji='%s' linked_to=%s custom_embed=%s details=%s name=%s>" % (self.emoji, self.linked_to, self.custom_embed, self.details, self.name)
		

class ReactionMenu:
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
		When the menu times out, delete the menu message. This overrides :attr:`clear_reactions_after`

		.. Changes :: v1.0.1
			- Added :attr:_active_sessions
			- Added :attr:_sessions_limit
			- Added :attr:_task_sessions_pool
		.. Changes :: v1.0.2
			- Added :attr:_delete_interactions
		.. Changes :: v1.0.5
			- Added :attr:_navigation_speed
			- Added :attr:NORMAL
			- Added :attr:FAST
		.. Changes :: v1.0.6
			- Added :attr:_custom_embed_set
			- Added :attr:_send_to_channel
		.. Changes :: v1.0.8
			- Added :attr:_delete_on_timeout
	"""
	STATIC = 0
	DYNAMIC = 1
	NORMAL = 'NORMAL'
	FAST = 'FAST'
	
	_active_sessions = []
	_sessions_limit = None
	_task_sessions_pool: List[asyncio.Task] = []

	def __init__(self, ctx: Context, *, back_button: str, next_button: str, config: int, **options): 
		self._ctx = ctx
		self._send_to_channel = None
		self._config = config
		self._bot = ctx.bot
		self._loop = ctx.bot.loop
		self._msg = None
		self._is_running = False
		self._all_buttons: List[Button] = [
			Button(emoji=back_button, linked_to=ButtonType.PREVIOUS_PAGE, name='default back button'),
			Button(emoji=next_button, linked_to=ButtonType.NEXT_PAGE, name='default next button'),
		]
		self._current_page = 0
		self._last_page = 0
		
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
		return self._config

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
	def end_session_buttons(self) -> List[Button]:
		temp = self._all_end_sessions()
		return temp if temp else None

	@property
	def custom_embed_buttons(self) -> List[Button]:
		temp = self._custom_linked_embeds()
		return temp if temp else None

	@property
	def all_buttons(self) -> List[Button]:
		return self._all_buttons

	@property
	def go_to_page_buttons(self) -> List[Button]:
		""".. Added v1.0.1"""
		temp = [button for button in self._all_buttons if button.linked_to is ButtonType.GO_TO_PAGE]
		return temp if temp else None
	
	@property
	def caller_buttons(self) -> List[Button]:
		""" .. Added v1.0.3"""
		temp = [button for button in self._all_buttons if button.linked_to is ButtonType.CALLER]
		return temp if temp else None
	
	@property
	def total_pages(self) -> int:
		"""With a dynamic menu, the total pages isn't known until AFTER the menu has started
			
			.. Added v1.0.1
		"""
		if self._config == ReactionMenu.STATIC:
			return len(self._static_completed_pages)
		elif self._config == ReactionMenu.DYNAMIC:
			return len(self._dynamic_completed_pages)

	@property
	def rows_requested(self) -> int:
		return self._rows_requested
	
	@property
	def navigation_speed(self) -> str:
		""".. Added v1.0.5"""
		return self._navigation_speed
	
	@navigation_speed.setter
	def navigation_speed(self, value):
		"""A property getter/setter for kwarg "navigation_speed"
		
		Example
		-------
		```
		menu = ReactionMenu(...)
		menu.navigation_speed = ReactionMenu.NORMAL
		>>> print(menu.navigation_speed)
		NORMAL
		```
			.. Added v1.0.5
		"""
		if not self._is_running:
			if value in (ReactionMenu.NORMAL, ReactionMenu.FAST):
				self._navigation_speed = value
			else:
				raise ReactionMenuException(f'When setting the \'navigation_speed\' of a menu, {value!r} is not a valid value')
		else:
			ReactionMenu.cancel_all_sessions()
			raise MenuAlreadyRunning(f'You cannot set the navigation speed when the menu is already running. Menu name: {self._name}')

	@property
	def clear_reactions_after(self) -> bool:
		return self._clear_reactions_after

	@clear_reactions_after.setter
	def clear_reactions_after(self, value):
		"""A property getter/setter for kwarg "clear_reactions_after"
		
		Example
		-------
		```
		menu = ReactionMenu(...)
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
		menu = ReactionMenu(...)
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
		menu = ReactionMenu(...)
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
		""".. Added v1.0.2"""
		return self._delete_interactions

	@delete_interactions.setter
	def delete_interactions(self, value):
		"""A property getter/setter for kwarg "delete_interactions"
		
		Example
		-------
		```
		menu = ReactionMenu(...)
		menu.delete_interactions = True
		>>> print(menu.delete_interactions)
		True
		```
			.. Added v1.0.2
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
		menu = ReactionMenu(...)
		menu.name = 'my menu'
		>>> print(menu.name)
		my menu
		```
		"""
		self._name = str(value)

	@property
	def style(self) -> str:
		return self._style

	@style.setter
	def style(self, value):
		"""A property getter/setter for kwarg "style"
		
		Example
		-------
		```
		menu = ReactionMenu(...)
		menu.style = 'On $ out of &'
		>>> On 1 out of 5
		```
		"""
		self._style = str(value)
	
	@property
	def all_can_react(self) -> bool:
		return self._all_can_react

	@all_can_react.setter
	def all_can_react(self, value):
		"""A property getter/setter for kwarg "all_can_react"
		
		Example
		-------
		```
		menu = ReactionMenu(...)
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
			.. Changes :: v1.0.6
				- Added _custom_embed_set
		"""
		if isinstance(value, Embed):
			self._custom_embed = value
			self._custom_embed_set = True
		else:
			raise TypeError(f'"custom_embed" expected discord.Embed, got {value.__class__.__name__}')
	
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
		"""
		if isinstance(value, str):
			self._wrap_in_codeblock = value
		else:
			raise TypeError(f'"wrap_in_codeblock" expected str, got {value.__class__.__name__}')
	
	@property
	def delete_on_timeout(self) -> bool:
		""".. Added v1.0.8"""
		return self._delete_on_timeout
	
	@delete_on_timeout.setter
	def delete_on_timeout(self, value):
		"""A property getter/setter for kwarg "delete_on_timeout"
		
		Example
		-------
		```
		menu = ReactionMenu(...)
		menu.delete_on_timeout = True
		>>> print(menu.delete_on_timeout)
		True
		```
			.. Added v1.0.8
		"""
		if isinstance(value, bool):
			self._delete_on_timeout = value
		else:
			raise TypeError(f'"delete_on_timeout" expected bool, got {value.__class__.__name__}')

	def _maybe_custom_embed(self) -> Embed:
		"""If a custom embed is set, return it
		
			.. Changes :: v1.0.6
				- Replaced the if statement. Caused an issue where if there was no title in the embed, other things such as the color, timestamp, thumbnail, etc. would not be displayed. 
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
		- `MissingSetting`: kwarg "rows_requested" was missing from the Button object
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
		embeds: :class:`discord.Embed`
			Embed objects
		
		Raises
		------
		- `MenuSettingsMismatch`: Tried to use method on a static menu
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		- `SingleUseOnly`: Attempted to call method more than once
		"""
		if not self._main_pages_already_set:
			embeds = collections.deque(embeds)
			embeds.reverse()
			self._dynamic_completed_pages.extendleft(embeds)
			self._main_pages_already_set = True
		else:
			raise SingleUseOnly('Once you\'ve set main pages, you cannot set more')

	@dynamic_only
	@ensure_not_primed
	def set_last_pages(self, *embeds: Embed):
		"""On a dynamic menu, set the pages you would like to show last. These embeds will be shown after the embeds that contain your data
		
		Parameter
		---------
		embeds: :class:`discord.Embed`
			Embed objects
		
		Raises
		------
		- `MenuSettingsMismatch`: Tried to use method on a static menu
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		- `SingleUseOnly`: Attempted to call method more than once
		"""
		if not self._last_pages_already_set:
			embeds = collections.deque(embeds)
			self._last_page_contents = embeds
			self._last_pages_already_set = True
		else:
			raise SingleUseOnly('Once you\'ve set last pages, you cannot set more')

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
	
	def get_button_by_name(self, name: str) -> Button:
		"""Retrieve a Button object by its name if the kwarg "name" for that Button object was set
		
		Parameter
		---------
		name: :class:`str`
			The Button name
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
		- `MissingSetting`: Set the Button :param:`linked_to` as `ButtonType.CUSTOM_EMBED` but did not assign the Button kwarg "embed" a value. 
		- `DuplicateButton`: The emoji used is already registered as a button
		- `TooManyButtons`: More than 20 buttons were added. Discord has a reaction limit of 20
		- `ReactionMenuException`: A name used for the Button is already registered

			.. Changes :: v1.0.3
				- Added check for ButtonType.CALLER
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
				raise MissingSetting('When adding a button with the type "ButtonType.CALLER", the kwarg "details" must be set.')

			self._all_buttons.append(button)
			if len(self._all_buttons) > 20:
				raise TooManyButtons
		else:
			raise DuplicateButton(f'The emoji {tuple(button.emoji)} has already been registered as a button')
	
	def _extract_all_emojis(self) -> List[str]:
		"""Returns a list of the emojis that represents the button"""
		return [button.emoji for button in self._all_buttons]

	def _custom_linked_embeds(self) -> List[Button]:
		"""Returns a list of :class:`Button` that have embeds linked to them"""
		return [button for button in self._all_buttons if button.linked_to is ButtonType.CUSTOM_EMBED]
	
	def _regular_buttons(self) -> List[Button]:
		"""Returns a list of :class:`Button` that do not have the type ButtonType.CUSTOM_EMBED"""
		return [button for button in self._all_buttons if button.linked_to is not ButtonType.CUSTOM_EMBED]
	
	def _actual_embeds(self) -> List[Embed]:
		"""Returns a list of the embed objects that are available from a linked button"""
		return [button.custom_embed for button in self._custom_linked_embeds()]
	
	def _all_end_sessions(self) -> List[Button]:
		""""Returns a list of all :class:`Button` that have the type as ButtonType.END_SESSION"""
		return [button for button in self._all_buttons if button.linked_to is ButtonType.END_SESSION]

	def _get_default_buttons(self) -> List[Button]:
		"""Returns the next and previous buttons"""
		return [self._all_buttons[0], self._all_buttons[1]]
	
	def help_appear_order(self): 
		"""Prints all button emojis you've added before this method was called to the console for easy copy and pasting of the desired order. 
		Note: If using Visual Studio Code, if you see a question mark as the emoji, you need to resize the console in order for it to show up. 
		"""
		print(f'Registered button emojis: {self._extract_all_emojis()}')
	
	def _sort_key(self, item: Button):
		"""Sort key for :attr:`_all_buttons`"""
		idx = self._emoji_new_order.index(item.emoji)
		return idx
	
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
	
	@classmethod
	def _get_task(cls, name: str):
		"""Return the static/dynamic task object"""
		for task in cls._task_sessions_pool:
			if task.get_name() == name:
				return task

	async def stop(self, *, delete_menu_message=False, clear_reactions=False):
		"""|coro| Stops the process of the reaction menu with the option of deleting the menu's message or clearing reactions upon cancellation
		
		Parameters
		----------
		delete_menu_message: :class:`bool`
			(optional) Delete the menu message when stopped (defaults to `False`)

		clear_reactions: :class:`bool`
			(optional) Clear the reactions on the menu's message when stopped (defaults to `False`)

			.. Changes :: v1.0.5
				- Added ID handling for static/dynamic task names
		"""
		def _get_proper_task() -> str:
			"""Depending on the menu instance ID, return the task name equivalent with that ID
				
				.. Added v1.0.5
			"""
			if self._config == ReactionMenu.STATIC:
				return 'static_task_%s' % id(self)
			else:
				return 'dynamic_task_%s' % id(self)

		if self._is_running:
			task = ReactionMenu._get_task(_get_proper_task())
			task.cancel()
			self._is_running = False
			ReactionMenu._remove_session(self)
			if delete_menu_message:
				await self._msg.delete()
				return
			
			if clear_reactions:
				await self._msg.clear_reactions()
	
	def _wait_check(self, reaction, user) -> bool:
		"""Predicate for :meth:discord.Client.wait_for"""
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
	
	@classmethod
	def _remove_session(cls, menu):
		"""Upon session completion, remove it from the list of active sessions
		
			.. Added v1.0.1
		"""
		if menu in cls._active_sessions:
			cls._active_sessions.remove(menu)
	
	@classmethod
	def get_sessions_count(cls) -> int:
		"""A class method that returns the number of active sessions
		
			.. Added v1.0.2
		"""
		return len(cls._active_sessions)

	@classmethod
	def set_sessions_limit(cls, limit: int, message: str='Too many active reaction menus. Wait for other menus to be finished.'):
		"""A class method that sets the amount of menu sessions that can be concurrently active. Should be set before any menus are started and cannot be called more than once
			
			.. Added v1.0.1

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
				ReactionMenu.set_sessions_limit(3, 'Sessions are limited')
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
			setattr(cls, 'limit_message', message)
	
	@classmethod
	def cancel_all_sessions(cls):
		"""A class method that immediately cancels all sessions that are currently running from the menu sessions task pool. Using this method does not allow the normal operations of :meth:`ReactionMenu.stop()`. This
		stops all session processing with no regard to changing the status of :attr:`ReactionMenu.is_running` amongst other things. Should only be used if you have an excess amount of menus running and it has an affect on 
		your bots performance

			.. Added v1.0.1
		"""
		for tsk_session in cls._task_sessions_pool:
			tsk_session.cancel()
		cls._active_sessions.clear()

	@classmethod
	def _is_currently_limited(cls) -> bool:
		"""Check if there is a limit on reaction menus
		
			.. Added v1.0.1
		"""
		if cls._sessions_limit:
			if len(cls._active_sessions) < cls._sessions_limit:
				return False
			else:
				return True
		else:
			return False
	
	def _asyncio_exception_callback(self, task: asyncio.Task):
		"""Used for "handling" unhandled exceptions in :meth:`ReactionMenu._execute_session`. Because that method is running in the background (asyncio.create_task), a callback is needed
		when an exception is raised or else all exceptions are suppressed/lost until the program terminates, which it won't because it's a bot. This re-raises those exceptions
		if any so proper debugging can occur both on my end and the users end (using :attr:`ButtonType.CALLER`)
			
			.. Added v1.0.3

			.. Changes :: v1.0.5
				- Added try/except to properly handle/display the appropriate tracebacks for when tasks are cancelled
		"""
		# only catch this error because I want every other error in :meth:`ReactionMenu._execute_session` to be re-raised. i.e, missing add reactions perms, etc
		try:
			task.result()
		except asyncio.CancelledError:
			pass # ignore this exception so discord.py can reproduce the traceback properly
	
	async def _handle_fast_navigation(self):
		"""If either of the below events are dispatched, return the result (reaction, user) of the coroutine object. Used in :meth:`ReactionMenu._execute_session` for :attr:`ReactionMenu.FAST`.
		Can timeout, `.result()` raises :class:`asyncio.TimeoutError` but is caught in :meth:`ReactionMenu._execute_session` for proper cleanup. This is the core function as to how the 
		navigation speed system works
		
			.. Added v1.0.5

				.. Note :: Handling of aws's 
					The additional time (+ 0.1) is needed because the items in :attr:`wait_for_aws` timeout at the exact same time. Meaning that there will never be an object in :attr:`pending` (which is what I want)
					which renders the ~return_when param useless because the first event that was dispatched is stored in :attr:`done`. Since they timeout at the same time,
					both aws are stored in :attr:`done` upon timeout. 
					
					The goal is to return the result of a single :meth:`discord.Client.wait_for`, the result is returned but the :class:`asyncio.TimeoutError`
					exception that was raised in :meth:`asyncio.wait` (because of the timeout by the other aws) goes unhandled and the exception is raised. The additional time allows the 
					cancellation of the task before the exception (Task exception was never retrieved) is raised 
			
			.. Changes :: v1.0.7
				- Added :func:`_proper_timeout` and replaced the `reaction_remove` ~timeout value to a function that handles cases where there is a timeout vs no timeout
		"""
		def _proper_timeout():
			"""In ~wait_for_aws, if the menu does not have a timeout (`ReactionMenu.timeout = None`), :class:`None` + :class:`float`, the float being "`self._timeout + 0.1`" from v1.0.5, will fail for obvious reasons. This checks if there is no timeout, 
			and instead of adding those two together, simply return :class:`None` to avoid :exc:`TypeError`. This would happen if the menu's :attr:`ReactionMenu.navigation_speed` was set to :attr:`ReactionMenu.FAST` and
			the :attr:`ReactionMenu.timeout` was set to :class:`None`
				
				.. Added v1.0.7
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
	
	async def _execute_navigation_type(self, worker, emoji, **kwargs):
		"""This controls whether the user has to wait until the emoji is removed from the message by the :class:`discord.Client` in order to continue 'turning' pages in the menu session. 
		:attr:`ReactionMenu.NORMAL` indicates the user has to wait for the :class:`discord.Client` to remove the reaction. :attr:`ReactionMenu.FAST` indicates no wait is needed and is 
		processed on each `reaction_add` and `reaction_remove`. In v1.0.0 - v1.0.4, the handling of each button press was processed in :meth:`ReactionMenu._execute_session`. This replaces that
		so each button press is also handled through here now as :attr:`ReactionMenu.NORMAL`, as well as the handling of :attr:`ReactionMenu.FAST`

		Kwargs
		------
		- from_custom_button: :class:`bool` Handles the editing process with interactions from :attr:`ButtonType.CUSTOM_EMBED`		
		- from_caller_button: :class:`bool` Handles the editing process with interactions from :attr:`ButtonType.CALLER`
			
			.. Added v1.0.5
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
				pass
			else:
				await self._msg.edit(embed=worker[self._current_page])
		
	async def _execute_session(self, worker):
		"""Begin the pagination process

			.. Changes :: v1.0.1
				- Added go to page functionality
			.. Changes :: v1.0.2
				- Added optional delete prompt and message interactions
			.. Changes :: v1.0.3
				- Added ButtonType.CALLER functionality	
			.. Changes :: v1.0.5
				- Moved the use of :meth:`_msg.edit` and :meth:`_msg.remove_reaction` to :meth:`ReactionMenu._execute_navigation_type`
			.. Changes :: v1.0.8
				- Added _delete_on_timeout functionality
		"""
		while self._is_running:
			try:
				if self._navigation_speed == ReactionMenu.NORMAL:
					reaction, user = await self._bot.wait_for('reaction_add', check=self._wait_check, timeout=self._timeout)
				elif self._navigation_speed == ReactionMenu.FAST:
					reaction, user = await self._handle_fast_navigation()
				else:
					raise ReactionMenuException(f'Navigation speed {self._navigation_speed!r} is not recognized')
			except asyncio.TimeoutError:
				self._is_running = False
				ReactionMenu._remove_session(self)
				if self._delete_on_timeout:
					await self._msg.delete()
					return
				if self._clear_reactions_after:
					await self._msg.clear_reactions()
				return
			else:
				for btn in self._all_buttons:
					# previous
					if str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.PREVIOUS_PAGE:
						self._current_page -= 1
						self._set_proper_page()
						# await self._msg.edit(embed=worker[self._current_page])
						# await self._msg.remove_reaction(btn.emoji, self._ctx.author) 
						await self._execute_navigation_type(worker, btn.emoji)
						break
					
					# next
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.NEXT_PAGE:
						self._current_page += 1
						self._set_proper_page()
						# await self._msg.edit(embed=worker[self._current_page])
						# await self._msg.remove_reaction(btn.emoji, self._ctx.author)
						await self._execute_navigation_type(worker, btn.emoji)
						break
					
					# first page
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.GO_TO_FIRST_PAGE:
						self._current_page = 0
						# await self._msg.edit(embed=worker[self._current_page])
						# await self._msg.remove_reaction(btn.emoji, self._ctx.author)
						await self._execute_navigation_type(worker, btn.emoji)
						break

					# last page
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.GO_TO_LAST_PAGE:
						self._current_page = self._last_page
						# await self._msg.edit(embed=worker[self._current_page])
						# await self._msg.remove_reaction(btn.emoji, self._ctx.author)
						await self._execute_navigation_type(worker, btn.emoji)
						break

					# go to page
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.GO_TO_PAGE:
						def check(m):
							not_bot = False
							author_pass = False
							channel_pass = False

							if not m.author.bot:
								not_bot = True
							if self._ctx.author.id == m.author.id:
								author_pass = True
							if self._ctx.channel.id == m.channel.id:
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
									# await self._msg.edit(embed=worker[self._current_page])
									# await self._msg.remove_reaction(btn.emoji, self._ctx.author)
									await self._execute_navigation_type(worker, btn.emoji)
									if self._delete_interactions:
										await bot_prompt.delete()
										await msg.delete()
									break
					
					# custom buttons
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.CUSTOM_EMBED:
						# await self._msg.edit(embed=btn.custom_embed)
						# await self._msg.remove_reaction(btn.emoji, self._ctx.author) 
						await self._execute_navigation_type(btn.custom_embed, btn.emoji, from_custom_button=True)
						break

					# caller button
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.CALLER:	
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
						# await self._msg.remove_reaction(btn.emoji, self._ctx.author) 
						await self._execute_navigation_type(None, btn.emoji, from_caller_button=True)
						break

					# end session
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.END_SESSION:
						self._is_running = False
						ReactionMenu._remove_session(self)
						await self._msg.delete()
						return
	
	def _duplicate_emoji_check(self):
		"""Since it's possible for the user to change the emoji of a :class:`Button` after an instance has been created and added to a :class:`ReactionMenu` instance. Before the menu starts, make sure there are no duplicates because if there are,
		it essentially renders that :class:`Button` useless because discord only allows unique reactions to be added.
		
			.. Added v1.0.5
		"""
		counter = collections.Counter(self._extract_all_emojis())
		if max(counter.values()) != 1:
			raise ReactionMenuException('There cannot be duplicate emojis when using Buttons. All emojis must be unique')

	def _duplicate_name_check(self):
		"""Since it's possible for the user to change the name of a :class:`Button` after an instance has been created and added to a :class:`ReactionMenu` instance. Before the menu starts, make sure there are no duplicates because if there are,
		methods such as :meth:`ReactionMenu.get_button_by_name` could return the wrong :class:`Button` object.
		
			.. Added v1.0.5
		"""
		counter = collections.Counter([btn.name.lower() for btn in self._all_buttons if btn.name is not None])
		if max(counter.values()) != 1:
			raise ReactionMenuException('There cannot be duplicate names when using Buttons. All names must be unique')
	
	def _determine_location(self, path):
		"""Set the text channel where the menu should start

			.. Added v1.0.6
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
		elif isinstance(path, TextChannel):
			# it's safe to just set it as the channel object because if the user was to use :meth:`discord.Guild.get_channel`, discord.py would return the obj or :class:`None`
			# which if :class:`None` is sent to :meth:`ReactionMenu.start`, it would be handled in the the "default" elif below
			self._send_to_channel = path

		# default 
		elif isinstance(path, type(None)):
			pass

		else:
			raise TypeError(f'When setting the "send_to" in ReactionMenu.start(), the value must be the name of the channel (str), the channel ID (int), or the channel object (discord.TextChannel), got {path.__class__.__name__}') 
	
	@ensure_not_primed
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

			.. Changes :: v1.0.3
				- Added task callbacks
			.. Changes :: v1.0.5
				- Added unique ID's to task names so multiple sessions can be ran/stopped in a single execution. So if :meth:`ReactionMenu.stop` is called during that execution, it knows exactly which menu instance to stop.
				Unlike before where the menu instance task name would be identified simply as static or dynamic, and with multiple instances ran from a single execution having the same task name, calling :meth:`ReactionMenu.stop`
				could stop the wrong menu instance
				- Added duplication check methods
			.. Changes :: v1.0.6
				- Added :param:`send_to`
				- Added :meth:`ReactionMenu._determine_location` and if checks to determine if the menu should start in the same channel as :attr:`_ctx` or another channel (:attr:`self._send_to_channel`)
		"""
		self._duplicate_emoji_check()
		self._duplicate_name_check()
		self._determine_location(send_to)
		
		if ReactionMenu._is_currently_limited():
			maybe_limit_message = getattr(ReactionMenu, 'limit_message')
			if maybe_limit_message:
				await self._ctx.send(maybe_limit_message)
			return
		else:
			ReactionMenu._active_sessions.append(self)
		
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
				for btn in self._regular_buttons():
					await self._msg.add_reaction(btn.emoji)
				self._last_page = len(worker) - 1

			# normal pages w/ custom pages
			elif len(self._static_completed_pages) >= 2 and self._custom_linked_embeds():
				worker = self._static_completed_pages 
				self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=self._static_completed_pages[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=self._static_completed_pages[0])
				for btn in self._extract_all_emojis():
					await self._msg.add_reaction(btn)
				self._last_page = len(worker) - 1

			# no normal pages w/ custom pages (only custom pages)
			elif len(self._static_completed_pages) == 0 and self._custom_linked_embeds():
				worker = self._actual_embeds()
				#self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=worker[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=worker[0])
				for btn in self._custom_linked_embeds():
					await self._msg.add_reaction(btn.emoji)
				self._last_page = len(worker) - 1
			
			# only 1 page w/ custom pages
			elif len(self._static_completed_pages) == 1 and self._custom_linked_embeds():
				worker = self._static_completed_pages
				self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=worker[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=worker[0])
				for btn in self._custom_linked_embeds():
					await self._msg.add_reaction(btn.emoji)
				else:
					# even though theres no need for directional buttons (only 1 page), add the back button anyway
					# so the user can navigate back to that single page
					await self._msg.add_reaction(self._get_default_buttons()[0].emoji)
			
			# only 1 page and no custom pages
			elif len(self._static_completed_pages) == 1 and not self._custom_linked_embeds():
				worker = self._static_completed_pages
				self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=worker[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=worker[0])
			
			# initiaze end session buttons if any
			for end_session_btn in self._all_end_sessions():
				await self._msg.add_reaction(end_session_btn.emoji)

			self._is_running = True
			unique_tsk_name = f'static_task_{id(self)}'
			static_task = self._loop.create_task(self._execute_session(worker), name=unique_tsk_name)
			static_task.add_done_callback(self._asyncio_exception_callback)
			ReactionMenu._task_sessions_pool.append(static_task)
		
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
					for btn in self._regular_buttons():
						await self._msg.add_reaction(btn.emoji)
					self._last_page = len(worker) - 1
				else:
					self._msg = await self._ctx.send(embed=worker[0]) if self._send_to_channel is None else await self._send_to_channel.send(embed=worker[0])
				
				# initiaze end session buttons if any
				for end_session_btn in self._all_end_sessions():
					await self._msg.add_reaction(end_session_btn.emoji)

				self._is_running = True
				unique_tsk_name = f'dynamic_task_{id(self)}'
				dynamic_task = self._loop.create_task(self._execute_session(worker), name=unique_tsk_name)
				dynamic_task.add_done_callback(self._asyncio_exception_callback)
				ReactionMenu._task_sessions_pool.append(dynamic_task)

		else:
			raise MenuSettingsMismatch('The menu\'s setting for dynamic or static was not recognized')
