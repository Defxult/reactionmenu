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

import re
from collections import namedtuple
from datetime import datetime
from enum import Enum, auto
from typing import Set, Union, Tuple

import discord
from discord.ext.commands import Command


class ViewButton(discord.ui.Button):
	ID_NEXT_PAGE =          '0'
	ID_PREVIOUS_PAGE =      '1'
	ID_GO_TO_FIRST_PAGE =   '2'
	ID_GO_TO_LAST_PAGE =    '3'
	ID_GO_TO_PAGE =         '4'
	ID_END_SESSION =        '5'
	ID_CALLER =             '6'
	ID_SEND_MESSAGE =       '7'
	ID_CUSTOM_EMBED = 		'8'

	# would have imported from .abc, but circular imports
	EMOJI_BACK_BUTTON = 	'◀️'
	EMOJI_NEXT_BUTTON = 	'▶️'
	EMOJI_FIRST_PAGE =  	'⏪'
	EMOJI_LAST_PAGE =   	'⏩'
	EMOJI_GO_TO_PAGE =  	'🔢'
	EMOJI_END_SESSION = 	'⏹️'

	_RE_IDs = r'[0-8]|[0-8]_\d+'
	_RE_UNIQUE_ID_SET = r'_\d+'

	def __init__(
		self,
		*,
		style: discord.ButtonStyle=discord.ButtonStyle.secondary,
		label: str=None,
		disabled: bool=False,
		custom_id: str=None,
		url: str=None,
		emoji: Union[str, discord.PartialEmoji]=None,
		row: int=None,
		followup: ViewButton.Followup=None,
		event: ViewButton.Event=None
		):
		self._rm_viewmenu: 'ViewMenu' = None
		super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
	
	class Event:
		...

	class Followup:
		...

	@classmethod
	def _base_nav_buttons(cls) -> Tuple[str]:
		return (ViewButton.ID_PREVIOUS_PAGE, ViewButton.ID_NEXT_PAGE, ViewButton.ID_GO_TO_FIRST_PAGE, ViewButton.ID_GO_TO_LAST_PAGE, ViewButton.ID_GO_TO_PAGE)
	
	@classmethod
	def _get_id_name_from_id(cls, id_: str) -> str:
		# if its a CALLER, SEND_MESSAGE, or CUSTOM_EMBED id, convert to it's true representation, because when passed, it's form is "[ButtonID]_[unique ID]"
		# see :meth:`_button_add_check` or :meth:`_maybe_custom_id` for details
		unique_id_set = re.compile(ViewButton._RE_UNIQUE_ID_SET)
		if re.search(unique_id_set, id_):
			id_ = re.sub(unique_id_set, '', id_)
		
		for key, val in cls.__dict__.items():
			if id_ == val:
				return f'ViewButton.{key}'
	
	@classmethod
	def back(cls) -> ViewButton:
		"""|class method| A factory method that returns a :class:`ViewButton` with the following parameters set:
		
		- style: `discord.ButtonStyle.gray`
		- label: "Back"
		- custom_id: `ViewButton.ID_PREVIOUS_PAGE`
		"""
		return cls(style=discord.ButtonStyle.gray, label='Back', custom_id=ViewButton.ID_PREVIOUS_PAGE)
	
	@classmethod
	def next(cls) -> ViewButton:
		"""|class method| A factory method that returns a :class:`ViewButton` with the following parameters set:
		
		- style: `discord.ButtonStyle.gray`
		- label: "Next"
		- custom_id: `ViewButton.ID_NEXT_PAGE`
		"""
		return cls(style=discord.ButtonStyle.gray, label='Next', custom_id=ViewButton.ID_NEXT_PAGE)
	
	@classmethod
	def go_to_first_page(cls) -> ViewButton:
		"""|class method| A factory method that returns a :class:`ViewButton` with the following parameters set:
		
		- style: `discord.ButtonStyle.gray`
		- label: "First Page"
		- custom_id: `ViewButton.ID_GO_TO_FIRST_PAGE`
		"""
		return cls(style=discord.ButtonStyle.gray, label='First Page', custom_id=ViewButton.ID_GO_TO_FIRST_PAGE)
	
	@classmethod
	def go_to_last_page_(cls) -> ViewButton:
		"""|class method| A factory method that returns a :class:`ViewButton` with the following parameters set:
		
		- style: `discord.ButtonStyle.gray`
		- label: "Last Page"
		- custom_id: `ViewButton.ID_GO_TO_LAST_PAGE`
		"""
		return cls(style=discord.ButtonStyle.gray, label='Last Page', custom_id=ViewButton.ID_GO_TO_LAST_PAGE)
	
	@classmethod
	def go_to_page(cls) -> ViewButton:
		"""|class method| A factory method that returns a :class:`ViewButton` with the following parameters set:
		
		- style: `discord.ButtonStyle.gray`
		- label: "Page Selection"
		- custom_id: `ViewButton.ID_GO_TO_PAGE`
		"""
		return cls(style=discord.ButtonStyle.gray, label='Page Selection', custom_id=ViewButton.ID_GO_TO_PAGE)
	
	@classmethod
	def end_session(cls) -> ViewButton:
		"""|class method| A factory method that returns a :class:`ViewButton` with the following parameters set:
		
		- style: `discord.ButtonStyle.gray`
		- label: "Close"
		- custom_id: `ViewButton.ID_END_SESSION`
		"""
		return cls(style=discord.ButtonStyle.gray, label='Close', custom_id=ViewButton.ID_END_SESSION)

	async def callback(self, interaction: discord.Interaction):
		await self._rm_viewmenu._paginate(self, interaction)

class ButtonType(Enum):
	"""A helper class for :class:`ReactionMenu` and :class:`TextMenu`. Determines the generic action a button can perform. This should *NOT* be used with :class:`ButtonsMenu`
	
		.. changes::
			v1.0.1
				Added :attr:`ButtonType.GO_TO_PAGE`
			v1.0.3
				Added :attr:`ButtonType.CALLER`
				Added :meth:`caller_details`
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
		"""|class method| Registers the function to call as well as it's arguments. Please note that the function you set should not return anything.
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

			.. added:: v1.0.3

			.. changes::
				v1.0.4
					Support for commands to be used as functions to call
		"""
		func = func.callback if isinstance(func, Command) else func
		return (func, args, kwargs)

class Button:
	"""A helper class for :class:`ReactionMenu` and :class:`TextMenu`. Represents a reaction. This should *NOT* be used with :class:`ButtonsMenu`
	
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

		.. changes::
			v1.0.3
				Added :attr:`details`
			v2.0.3
				Added :attr:`__clicked_by`
				Added :attr:`__total_clicks`
				Added :attr:`__last_clicked`
				Removed `__slots__`
	"""

	def __init__(self, *, emoji: str, linked_to: ButtonType, **options):
		self.emoji = emoji
		self.linked_to = linked_to
		self.custom_embed: discord.Embed = options.get('embed')
		self.details: tuple = options.get('details')
		self.name: str = options.get('name')
		if self.name:
			self.name = str(self.name).lower()
		
		self.__clicked_by = set()
		self.__total_clicks = 0
		self.__last_clicked: datetime = None
		self.__menu = None
	
	def __str__(self):
		return self.emoji
	
	def __repr__(self):
		"""
			.. changes::
				v1.0.9
					Replaced old string formatting (%s) with fstring
		"""
		return f'<Button emoji={self.emoji!r} linked_to={self.linked_to} custom_embed={self.custom_embed} details={self.details} name={self.name!r}>'
	
	@property
	def menu(self):
		"""
		Returns
		-------
		The instance of the menu that the button is currently operating under. Can be :class:`None` if the button is not registered to a menu
		
			.. added:: v2.0.3
		"""
		return self.__menu
	
	@property
	def clicked_by(self) -> Set[discord.Member]:
		"""
		Returns
		-------
		Set[:class:`discord.Member`]:
			The members who clicked the button
		
			.. added:: v2.0.3
		"""
		return self.__clicked_by
	
	@property
	def total_clicks(self) -> int:
		"""
		Returns
		-------
		:class:`int`:
			The amount of clicks on the button
		
			.. added:: v2.0.3
		"""
		return self.__total_clicks

	@property
	def last_clicked(self) -> datetime:
		"""
		Returns
		-------
		:class:`datetime.datetime`:
			The time in UTC for when the button was last clicked. Can be :class:`None` if the button has not been clicked
		
			.. added:: v2.0.3
		"""
		return self.__last_clicked
	