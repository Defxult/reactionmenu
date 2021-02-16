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
import collections
import asyncio
from enum import Enum, auto
from typing import List, Union, Deque

from discord import Embed
from discord.ext.commands import Context

from .decorators import *

class ButtonType(Enum):
	"""A helper class for :class:`ReactionMenu`. Determines the generic action a button can take"""

	NEXT_PAGE = auto()
	PREVIOUS_PAGE = auto()
	GO_TO_FIRST_PAGE = auto()
	GO_TO_LAST_PAGE = auto()
	END_SESSION = auto()
	CUSTOM_EMBED = auto()

	"""Added v1.0.1"""
	GO_TO_PAGE = auto()

class Button:
	"""A helper class for :class:`ReactionMenu`. Represents a reaction
	
	Parameters
	----------
	- emoji: `str` The discord reaction that will be used
	- linked_to: `ButtonType` A generic action a button can perform
	
	Options [kwargs]
	----------------
	- embed: `discord.Embed` Only used when linked_to is set as :class:`ButtonType.CUSTOM_EMBED`. This is the embed that can be selected seperately from the reaction menu (static menu's only)
	- name: `str` An optional name for the button. Can be set to retrieve it via :meth:`ReactionMenu.get_button_by_name`
	"""

	__slots__ = ('emoji', 'linked_to', 'custom_embed', 'name')

	def __init__(self, *, emoji: str, linked_to: ButtonType, **options):
		self.emoji = emoji
		self.linked_to = linked_to
		self.custom_embed = options.get('embed')
		self.name = options.get('name')
		if self.name:
			self.name = str(self.name).lower()
	
	def __str__(self):
		return self.emoji
	
	def __repr__(self):
		return "<Button emoji='%s' linked_to='%s' custom_embed='%s'>" % (self.emoji, self.linked_to, self.custom_embed)
		
class ReactionMenu:
	"""A class to create a discord.py reaction menu. If discord.py version is 1.5.0+, intents are required
	
	Parameters
	----------
	- ctx: `discord.ext.commands.Context` The Context object. You can get this using a command or if in `discord.on_message`
	- back_button: `str` Button used to go to the previous page of the menu
	- next_button: `str` Button used to go to the next page of the menu
	- config: `int` The menus core function to set. Class variables `ReactionMenu.STATIC` or `ReactionMenu.DYNAMIC`

	Options [kwargs]
	----------------
	- rows_requested: `int` The amount of information per :meth:`ReactionMenu.add_row` you would like applied to each embed page
		- dynamic only
		- default None

	- custom_embed: `discord.Embed` Embed object to use when adding data with :meth:`ReactionMenu.add_row`. Used for styling purposes
		- dynamic only
		- default None 

	- wrap_in_codeblock: `str` The discord codeblock language identifier. Example below
		- dynamic only
		- default None 
		>>> ReactionMenu(ctx, ..., wrap_in_codeblock='py') 

	- clear_reactions_after: `bool` When the menu ends, remove all reactions
		- default True 

	- timeout: Union[:class:`float`, `None`] Timer for when the menu should end. Can be None for no timeout 
		- default 60.0 

	- show_page_director: `bool` Shown at the botttom of each embed page. "Page 1/20"
		- default True

	- name: `str` A name you can set for the menu
		- default None

	- style: `str` A custom page director style you can select. "$" represents the current page, "&" represents the total amount of pages. 
		- default "Page $/&"
		>>> ReactionMenu(ctx, ..., style='On $ out of &')
		'On 1 out of 5'

	- all_can_react: `bool` Sets if everyone is allowed to control when pages are 'turned' when buttons are pressed
		- default False
	"""

	STATIC = 0
	DYNAMIC = 1
	
	"""Added v1.0.1"""
	_active_sessions = []
	_sessions_limit = None
	_task_sessions_pool: List[asyncio.Task] = []

	def __init__(self, ctx: Context, *, back_button: str, next_button: str, config: int, **options): 
		self._ctx = ctx
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
	def clear_reactions_after(self) -> bool:
		return self._clear_reactions_after
	@clear_reactions_after.setter
	def clear_reactions_after(self, value):
		if isinstance(value, bool):
			self._clear_reactions_after = value
		else:
			raise TypeError(f'"clear_reactions_after" expected bool, got {value.__class__.__name__}')
	
	@property
	def timeout(self) -> float:
		return self._timeout
	@timeout.setter
	def timeout(self, value):
		if isinstance(value, (int, float, type(None))):
			self._timeout = value
		else:
			raise TypeError(f'"timeout" expected float, int, or None, got {value.__class__.__name__}')
	
	@property
	def show_page_director(self) -> bool:
		return self._show_page_director
	@show_page_director.setter
	def show_page_director(self, value):
		if isinstance(value, bool):
			self._show_page_director = value
		else:
			raise TypeError(f'"show_page_director" expected bool, got {value.__class__.__name__}')
	
	@property
	def name(self) -> str:
		return self._name
	@name.setter
	def name(self, value):
		self._name = str(value)

	@property
	def style(self) -> str:
		return self._style
	@style.setter
	def style(self, value):
		self._style = str(value)
	
	@property
	def all_can_react(self) -> bool:
		return self._all_can_react
	@all_can_react.setter
	def all_can_react(self, value):
		if isinstance(value, bool):
			self._all_can_react = value
		else:
			raise TypeError(f'"all_can_react" expected bool, got {value.__class__.__name__}')
	
	@property
	def custom_embed(self) -> Embed:
		return self._custom_embed
	@custom_embed.setter
	def custom_embed(self, value):
		if isinstance(value, Embed):
			self._custom_embed = value
		else:
			raise TypeError(f'"custom_embed" expected discord.Embed, got {value.__class__.__name__}')
	
	@property
	def wrap_in_codeblock(self) -> str:
		return self._wrap_in_codeblock
	@wrap_in_codeblock.setter
	def wrap_in_codeblock(self, value):
		if isinstance(value, str):
			self._wrap_in_codeblock = value
		else:
			raise TypeError(f'"wrap_in_codeblock" expected str, got {value.__class__.__name__}')
	
	def _maybe_custom_embed(self) -> Embed:
		"""If a custom embed is set, return it"""
		if self._custom_embed:
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
		data: `str` The information to add to the menu 
		
		Raises
		------
		- `MissingSetting`: kwarg "rows_requested" was missing from the Button object
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
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
		page_number: `int` The page to remove
		
		Raises
		------
		- `InvalidPage`: Page not found
		- `MenuSettingsMismatch`: Tried to use method on a dynamic menu
		- `MenuAlreadyRunning`: Attempted to call method after the menu has already started
		"""
		pages_count = len(self._static_completed_pages)
		if page_number <= 0 or page_number > pages_count:
			raise InvalidPage(f'There are currently {pages_count} pages. You need to delete a page betweem 1-{pages_count}')
		else:
			del self._static_completed_pages[page_number - 1]
	
	@dynamic_only
	@ensure_not_primed
	def set_main_pages(self, *embeds: Embed):
		"""On a dynamic menu, set the pages you would like to show first. These embeds will be shown before the embeds that contain your data
		
		Parameter
		---------
		embeds: `discord.Embed` Embed objects
		
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
			raise SingleUseOnly('Once you\'ve set main pages, you cannot set more. ')

	@dynamic_only
	@ensure_not_primed
	def set_last_pages(self, *embeds: Embed):
		"""On a dynamic menu, set the pages you would like to show last. These embeds will be shown after the embeds that contain your data
		
		Parameter
		---------
		embeds: `discord.Embed` Embed objects
		
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
		embed: `discord.Embed` An Embed object
		
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
		name: `str` The Button name
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
		`MenuAlreadyRunning`: Attempted to call method after the menu has already started
		"""
		self._all_buttons.clear()
	
	@ensure_not_primed
	def remove_button(self, identity: Union[str, Button]):
		"""Remove a button by its name or its object
		
		Parameter
		---------
		identity: Union[`str`, `Button`] Name of the button or the button object itself

		Raises
		------
		`ButtonNotFound` - Button with given identity was not found
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
		button: `Button` The button to instantiate. Contains arguments such as "emoji" (the button), and "linked_to" (an embed)
		
		Raises
		------
		- `MenuAlreadyRunning`: Attempted to call this method after the menu has started
		- `MissingSetting`: Set the Button "linked_to" as ButtonType.CUSTOM_EMBED but did not assign the Button kwarg "embed" a value. 
		- `DuplicateButton`: The emoji used is already registered as a button
		- `TooManyButtons`: More than 20 buttons were added. Discord has a reaction limit of 20
		- `NameError`: A name used for the Button is already registered
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
				raise NameError('There cannot be duplicate names when setting the name for a Button')

			self._all_buttons.append(button)
			if len(self._all_buttons) > 20:
				raise TooManyButtons
		else:
			raise DuplicateButton(f'The emoji {tuple(button.emoji)} has already been registered as button')
	
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
		Note: If using Visual Studio Code, if you see a question mark as the emoji, you need to resize the console size in order for it to show up. 
		"""
		print(f'Registered button emojis: {self._extract_all_emojis()}')
	
	def _sort_key(self, item: Button):
		"""Sort :attr:`_all_buttons`"""
		idx = self._emoji_new_order.index(item.emoji)
		return idx
	
	@ensure_not_primed
	def change_appear_order(self, *emoji_or_button: Union[str, Button]):
		"""Change the order of the reactions you want them to appear in on the menu
		
		Parameter
		---------
		emoji_or_button: Union[`str`, `Button`] The emoji itself or Button object
		
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
				"""If the item in emoji_or_button isinstance of Button, convert it to the emoji it represents, then add it to the list"""
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
		- delete_menu_message: `bool` (optional) Delete the menu message when stopped
			default False

		- clear_reactions: `bool` (optional) Clear the reactions on the menu's message when stopped
			default False
		"""
		if self._is_running:
			task = ReactionMenu._get_task('static_task' if self._config == ReactionMenu.STATIC else 'dynamic_task')
			task.cancel()
			self._is_running = False
			ReactionMenu._remove_session(self)
			if delete_menu_message:
				await self._msg.delete()
				return
			
			if clear_reactions:
				await self._msg.clear_reactions()
	
	def _wait_check(self, reaction, user) -> bool:
		"""Predicate for discord.Client.wait_for"""
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
		for curr_menu in cls._active_sessions:
			if curr_menu == menu:
				cls._active_sessions.remove(menu)
				return
	
	@classmethod
	def set_sessions_limit(cls, limit: int, message: str='Too many active reaction menus. Wait for other menus to be finished.'):
		"""Sets the amount of menu sessions that can be concurrently active. Should be set before any menus are started and cannot be called more than once
			
			.. Added v1.0.1

		Parameters
		----------
		- limit: `int` The amount of menu sessions allowed
		- message: `str` Message that will be sent informing users about the menu limit when the limit is reached. Can be `None` for no message

		Example
		-------
		>>> class Example(commands.Cog):
			def __init__(self, bot):
				self.bot = bot
				ReactionMenu.set_sessions_limit(3, 'Sessions are limited')
		 
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
		"""This method immediately cancels all sessions that are currently running from the menu sessions task pool. Using this method does not allow the normal operations of :meth:`ReactionMenu.stop()`. This
		stops all session processing with no regard to changing the status of :prop:`ReactionMenu.is_running` amongst other things.

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
		
	async def _execute_session(self, worker):
		"""Begin the pagination process"""
		while self._is_running:
			try:
				reaction, user = await self._bot.wait_for('reaction_add', check=self._wait_check, timeout=self._timeout)
			except asyncio.TimeoutError:
				self._is_running = False
				ReactionMenu._remove_session(self)
				if self._clear_reactions_after:
					await self._msg.clear_reactions()
				return
			else:
				for btn in self._all_buttons:
					# previous
					if str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.PREVIOUS_PAGE:
						self._current_page -= 1
						self._set_proper_page()
						await self._msg.edit(embed=worker[self._current_page])
						await self._msg.remove_reaction(btn.emoji, self._ctx.author) 
						break
					
					# next
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.NEXT_PAGE:
						self._current_page += 1
						self._set_proper_page()
						await self._msg.edit(embed=worker[self._current_page])
						await self._msg.remove_reaction(btn.emoji, self._ctx.author)
						break
					
					# first page
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.GO_TO_FIRST_PAGE:
						self._current_page = 0
						await self._msg.edit(embed=worker[self._current_page])
						await self._msg.remove_reaction(btn.emoji, self._ctx.author)
						break

					# last page
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.GO_TO_LAST_PAGE:
						self._current_page = self._last_page
						await self._msg.edit(embed=worker[self._current_page])
						await self._msg.remove_reaction(btn.emoji, self._ctx.author)
						break

					# go to page
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.GO_TO_PAGE:
						"""Added v1.0.1"""
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
							
							if all((author_pass, channel_pass, not_bot)):
								return True
							return False

						await self._msg.channel.send(f'{self._ctx.author.name}, what page would you like to go to?')
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
									await self._msg.edit(embed=worker[self._current_page])
									await self._msg.remove_reaction(btn.emoji, self._ctx.author)
									break
					
					# custom buttons
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.CUSTOM_EMBED:
						await self._msg.edit(embed=btn.custom_embed)
						await self._msg.remove_reaction(btn.emoji, self._ctx.author)
						break
					
					# end session
					elif str(reaction.emoji) == btn.emoji and btn.linked_to is ButtonType.END_SESSION:
						self._is_running = False
						ReactionMenu._remove_session(self)
						await self._msg.delete()
						return
					

	@ensure_not_primed
	async def start(self):
		"""|coro| Starts the reaction menu
		
		Raises
		------
		- `MenuAlreadyRunning`: Attempted to call this method after the menu has started
		- `MenuSettingsMismatch`: The wrong number was used in the "config" parameter. only 0 (`ReactionMenu.STATIC`) or 1 (`ReactionMenu.DYNAMIC`) are permitted
		"""
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
				self._msg = await self._ctx.send(embed=self._static_completed_pages[0]) 
				for btn in self._regular_buttons():
					await self._msg.add_reaction(btn.emoji)
				self._last_page = len(worker) - 1

			# normal pages w/ custom pages
			elif len(self._static_completed_pages) >= 2 and self._custom_linked_embeds():
				worker = self._static_completed_pages 
				self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=self._static_completed_pages[0]) 
				for btn in self._extract_all_emojis():
					await self._msg.add_reaction(btn)
				self._last_page = len(worker) - 1

			# no normal pages w/ custom pages (only custom pages)
			elif len(self._static_completed_pages) == 0 and self._custom_linked_embeds():
				worker = self._actual_embeds()
				#self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=worker[0])
				for btn in self._custom_linked_embeds():
					await self._msg.add_reaction(btn.emoji)
				self._last_page = len(worker) - 1
			
			# only 1 page w/ custom pages
			elif len(self._static_completed_pages) == 1 and self._custom_linked_embeds():
				worker = self._static_completed_pages
				self._refresh_page_director_info(worker)
				self._msg = await self._ctx.send(embed=worker[0])
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
				self._msg = await self._ctx.send(embed=worker[0])
			
			# initiaze end session buttons if any
			for end_session_btn in self._all_end_sessions():
				await self._msg.add_reaction(end_session_btn.emoji)

			self._is_running = True
			static_task = self._loop.create_task(self._execute_session(worker), name='static_task')
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
					self._msg = await self._ctx.send(embed=worker[0])
					for btn in self._regular_buttons():
						await self._msg.add_reaction(btn.emoji)
					self._last_page = len(worker) - 1
				else:
					self._msg = await self._ctx.send(embed=worker[0])
				
				# initiaze end session buttons if any
				for end_session_btn in self._all_end_sessions():
					await self._msg.add_reaction(end_session_btn.emoji)

				self._is_running = True
				dynamic_task = self._loop.create_task(self._execute_session(worker), name='dynamic_task')
				ReactionMenu._task_sessions_pool.append(dynamic_task)
			
		else:
			raise MenuSettingsMismatch('The menu\'s setting for dynamic or static was not recognized')
