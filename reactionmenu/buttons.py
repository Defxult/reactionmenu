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

from typing import TYPE_CHECKING, Set, Tuple, Union

if TYPE_CHECKING:
	from . import ViewMenu, ReactionMenu

import re
from collections import namedtuple
from datetime import datetime
from enum import Enum, auto

import discord
from discord.ext.commands import Command

from .abc import BaseButton
from .errors import ViewMenuException


class ViewButton(discord.ui.Button, BaseButton):
	ID_NEXT_PAGE =          '0'
	ID_PREVIOUS_PAGE =      '1'
	ID_GO_TO_FIRST_PAGE =   '2'
	ID_GO_TO_LAST_PAGE =    '3'
	ID_GO_TO_PAGE =         '4'
	ID_END_SESSION =        '5'
	ID_CALLER =             '6'
	ID_SEND_MESSAGE =       '7'
	ID_CUSTOM_EMBED = 		'8'

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
		event: BaseButton.Event=None,
		):
		super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
		BaseButton.__init__(self)
		self.followup = followup
		
		# abc
		self._menu: ViewMenu = None
	
	def __repr__(self):
		return f'<ViewButton label={self.label!r} custom_id={ViewButton._get_id_name_from_id(self.custom_id)} style={self.style} emoji={self.emoji!r} url={self.url} disabled={self.disabled} total_clicks={self._total_clicks}>'

	class Followup:
		"""A class that represents the message sent using a :class:`ViewButton`. Contains parameters similar to discord.py's `Messageable.send`. Only to be used with :class:`ViewButton` kwarg "followup".
		It is to be noted that this should not be used with :class:`ViewButton` with a "style" of `discord.ButtonStyle.link` because link buttons do not send interaction events.
		
		Parameters
		----------
		content: :class:`str`
			Message to send (defaults to :class:`None`)
		
		embed: :class:`discord.Embed`
			Embed to send. Can also bet set for buttons with a custom_id of `ViewButton.ID_CUSTOM_EMBED` (defaults to :class:`None`)
		
		file: :class:`discord.File`
			File to send (defaults to :class:`None`) *NOTE* If the :class:`ViewButton` custom_id is `ViewButton.ID_SEND_MESSAGE`, the file will be ignored because of discord API limitations
		
		tts: :class:`bool`
			If discord should read the message aloud (defaults to `False`) *NOTE* Not valid for `ephemeral` messages
		
		allowed_mentions: :class:`discord.AllowedMentions`
			Controls the mentions being processed in the menu message (defaults to :class:`None`) *NOTE* Not valid for `ephemeral` messages
		
		delete_after: Union[:class:`int`, :class:`float`]
			Amount of time to wait before the message is deleted (defaults to :class:`None`) *NOTE* Not valid for `ephemeral` messages
		
		ephemeral: :class:`bool`
			If the message will be hidden from everyone except the person that clicked the button (defaults to `False`) *NOTE* This is only valid for a :class:`ViewButton` with custom_id `ViewButton.ID_SEND_MESSAGE`
		"""
		
		__slots__ = ('content', 'embed', 'file', 'tts', 'allowed_mentions', 'delete_after', 'ephemeral', '_caller_info')

		def __init__(
			self,
			content: str=None, 
			*,
			embed: discord.Embed=None,
			file: discord.File=None,
			tts: bool=False,
			allowed_mentions: discord.AllowedMentions=None,
			delete_after: Union[int, float]=None,
			ephemeral: bool=False
			):
			self.content = content
			self.embed = embed
			self.file = file
			self.tts = tts
			self.allowed_mentions = allowed_mentions
			self.delete_after = delete_after
			self.ephemeral = ephemeral
			self._caller_info: 'NamedTuple' = None
		
		def _to_dict(self) -> dict:
			"""This is a :class:`ViewButton.Followup` method"""
			new = {}
			for i in self.__slots__:
				new[i] = getattr(self, i)
			return new
		
		def set_caller_details(self, func: object, *args, **kwargs):
			"""Set the parameters for the function you set for a :class:`ViewButton` with the custom_id `ViewButton.ID_CALLER`
			
			Parameters
			----------
			func: :class:`object`
				The function object that will be called when the associated button is clicked
			
			*args: :class:`Any`
				An argument list that represents the parameters of that function
			
			**kwargs: :class:`Any`
				An argument list that represents the kwarg parameters of that function
			
			Raises
			------
			- `ViewMenuException`: Parameter "func" was not a callable object
			"""
			if not callable(func): raise ViewMenuException('Parameter "func" must be callable')
			Details = namedtuple('Details', ['func', 'args', 'kwargs'])
			func = func.callback if isinstance(func, Command) else func
			self._caller_info = Details(func=func, args=args, kwargs=kwargs)

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
	
	@property
	def menu(self) -> ViewMenu:
		"""
		Returns
		-------
		:class:`ViewMenu`:
			The menu instance this button is attached to. Could be :class:`None` if the button is not attached to a menu
		"""
		return self._menu
	
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
		await self._menu._paginate(self, interaction)

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

class Button(BaseButton):
	"""A helper class for :class:`ReactionMenu`. Represents a reaction. This should *NOT* be used with :class:`ViewMenu`
	
	Parameters
	----------
	emoji: :class:`str`
		The discord reaction that will be used

	linked_to: :class:`ButtonType`
		A generic action a button can perform
	
	event: :class:`Button.Event`
		Determine when a button should be removed or disabled depending on the amount of clicks
	
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
				Added :attr:`_clicked_by`
				Added :attr:`_total_clicks`
				Added :attr:`_last_clicked`
				Removed `__slots__`
			v3.0.0
				Added :param:`event`
	"""

	def __init__(self, *, emoji: str, linked_to: ButtonType, event: Button.Event=None, **options):
		super().__init__()
		self.emoji = emoji
		self.linked_to = linked_to
		self.custom_embed: discord.Embed = options.get('embed')
		self.details: tuple = options.get('details')
		self.name: str = options.get('name')
		
		# abc
		self._menu: ReactionMenu = None
	
	def __str__(self):
		return self.emoji
	
	def __repr__(self):
		"""
			.. changes::
				v1.0.9
					Replaced old string formatting (%s) with fstring
		"""
		return f'<Button emoji={self.emoji!r} linked_to={self.linked_to} total_clicks={self._total_clicks} name={self.name!r}>'
	
	@property
	def menu(self) -> ReactionMenu:
		"""
		Returns
		-------
		:class:`ReactionMenu`
			The menu the button is currently operating under. Can be :class:`None` if the button is not registered to a menu
		
			.. added:: v2.0.3
		"""
		return self._menu
	
	