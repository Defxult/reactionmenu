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

from typing import TYPE_CHECKING, List, NamedTuple, Set, Tuple, Union

if TYPE_CHECKING:
	from . import ViewMenu, ReactionButton, ReactionMenu

import re
from collections import namedtuple
from datetime import datetime

import discord
from discord.ext.commands import Command

from .abc import BaseButton, PaginationEmojis
from .errors import IncorrectType, ViewMenuException


class ViewButton(discord.ui.Button, BaseButton):
	"""A helper class for :class:`ViewMenu`. Represents a UI button. This should *NOT* be used with :class:`ReactionMenu`
	
	Parameters
	----------
	style: :class:`discord.ButtonStyle`
		(optional) The style of the button (defaults to `discord.ButtonStyle.secondary`)
	
	label: :class:`str`
		(optional) The label of the button, if any (defaults to :class:`None`)
	
	disabled: :class:`bool`
		(optional) Whether the button is disabled or not (defaults to `False`)
	
	custom_id: :class:`str`
		(optional) The ID of the button that gets received during an interaction. If this button is for a URL, it does not have a custom ID (defaults to :class:`None`)
	
	url: :class:`str`
		(optional) The URL this button sends you to (defaults to :class:`None`)
	
	emoji: Union[:class:`str`, :class:`discord.PartialEmoji`]
		(optional) The emoji of the button, if available (defaults to :class:`None`)
	
	followup: :class:`ViewButton.Follow`
		(optional) Used with buttons with custom_id `ViewButton.ID_CALLER`, `ViewButton.ID_SEND_MESSAGE`, `ViewButton.ID_CUSTOM_EMBED` (defaults to :class:`None`)
	
	event: :class:`ViewButton.Event`
		(optional) Set the button to be disabled or removed when it has been pressed a certain amount of times (defaults to :class:`None`)
	"""
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
		followup: ViewButton.Followup=None,
		event: ViewButton.Event=None,
		):
		super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=None)
		BaseButton.__init__(self)
		self.followup = followup
		
		# abc
		self._menu: ViewMenu = None
	
	def __repr__(self):
		total_clicks = '' if self.style == discord.ButtonStyle.link else f' total_clicks={self.total_clicks}'
		return f'<ViewButton label={self.label!r} custom_id={ViewButton._get_id_name_from_id(str(self.custom_id))} style={self.style} emoji={self.emoji!r} url={self.url} disabled={self.disabled}{total_clicks}>'

	async def callback(self, interaction: discord.Interaction):
		"""The callback function from the button interaction. This should not be manually called"""
		await self._menu._paginate(self, interaction)
	
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
			If the message will be hidden from everyone except the person that pressed the button (defaults to `False`) *NOTE* This is only valid for a :class:`ViewButton` with custom_id `ViewButton.ID_SEND_MESSAGE`
		"""
		
		__slots__ = ('content', 'embed', 'file', 'tts', 'allowed_mentions', 'delete_after', 'ephemeral', 'details')

		def __init__(
			self,
			content: str=None, 
			*,
			embed: discord.Embed=None,
			file: discord.File=None,
			tts: bool=False,
			allowed_mentions: discord.AllowedMentions=None,
			delete_after: Union[int, float]=None,
			ephemeral: bool=False,
			**kwargs
			):
			self.content = content
			self.embed = embed
			self.file = file
			self.tts = tts
			self.allowed_mentions = allowed_mentions
			self.delete_after = delete_after
			self.ephemeral = ephemeral
			
			self.details: NamedTuple = kwargs.get('details')
		
		def _to_dict(self) -> dict:
			"""This is a :class:`ViewButton.Followup` method"""
			new = {}
			for i in self.__slots__:
				new[i] = getattr(self, i)
			return new
		
		@classmethod
		def set_caller_details(cls, func: object, *args, **kwargs) -> NamedTuple:
			"""|class method| Set the parameters for the function you set for a :class:`ViewButton` with the custom_id `ViewButton.ID_CALLER`
			
			Parameters
			----------
			func: :class:`object`
				The function object that will be called when the associated button is pressed
			
			*args: :class:`Any`
				An argument list that represents the parameters of that function
			
			**kwargs: :class:`Any`
				An argument list that represents the kwarg parameters of that function
			
			Raises
			------
			- `IncorrectType`: Parameter "func" was not a callable object
			"""
			if callable(func):
				Details = namedtuple('Details', ['func', 'args', 'kwargs'])
				func = func.callback if isinstance(func, Command) else func
				return Details(func=func, args=args, kwargs=kwargs)
			else:
				raise IncorrectType('Parameter "func" must be callable')

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
	def go_to_last_page(cls) -> ViewButton:
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
	
	@classmethod
	def all(cls) -> List[ViewButton]:
		"""|class method| A factory method that returns a `list` of all base navigation buttons. Base navigation buttons are :class:`ViewButton` with the `custom_id`:
		
		- `ViewButton.ID_GO_TO_FIRST_PAGE`
		- `ViewButton.ID_PREVIOUS_PAGE`
		- `ViewButton.ID_NEXT_PAGE`
		- `ViewButton.ID_GO_TO_LAST_PAGE`
		- `ViewButton.ID_GO_TO_PAGE`
		- `ViewButton.ID_END_SESSION`

		They are returned in that order
		"""
		return [cls.go_to_first_page(), cls.back(), cls.next(), cls.go_to_last_page(), cls.go_to_page(), cls.end_session()]

class ButtonType:
	"""A helper class for :class:`ReactionMenu`. Determines the generic action a button can perform. This should *NOT* be used with :class:`ViewMenu`"""
	NEXT_PAGE = 0
	PREVIOUS_PAGE = 1
	GO_TO_FIRST_PAGE = 2
	GO_TO_LAST_PAGE = 3
	GO_TO_PAGE = 4
	END_SESSION = 5
	CUSTOM_EMBED = 6
	CALLER = 7

	@classmethod
	def _get_buttontype_name_from_type(cls, type_: int):
		"""|class method| Used to determine the `linked_to` type. Returns the :class:`str` representation of that type"""
		dict_ = {
			cls.NEXT_PAGE : 'ButtonType.NEXT_PAGE',
			cls.PREVIOUS_PAGE : 'ButtonType.PREVIOUS_PAGE',
			cls.GO_TO_FIRST_PAGE : 'ButtonType.GO_TO_FIRST_PAGE',
			cls.GO_TO_LAST_PAGE : 'ButtonType.GO_TO_LAST_PAGE',
			cls.GO_TO_PAGE : 'ButtonType.GO_TO_PAGE',
			cls.END_SESSION : 'ButtonType.END_SESSION',
			cls.CUSTOM_EMBED : 'ButtonType.CUSTOM_EMBED',
			cls.CALLER : 'ButtonType.CALLER'
		}
		return dict_[type_]

class ReactionButton(BaseButton):
	"""A helper class for :class:`ReactionMenu`. Represents a reaction. This should *NOT* be used with :class:`ViewMenu`
	
	Parameters
	----------
	emoji: :class:`str`
		The discord reaction that will be used

	linked_to: :class:`ReactionButton.Type`
		A generic action a button can perform
	
	event: :class:`ReactionButton.Event`
		Determine when a button should be removed depending on how many times it has been pressed
	
	Kwargs
	------
	embed: :class:`discord.Embed`
		Only used when :param:`linked_to` is set as `ReactionButton.Type.CUSTOM_EMBED`. This is the embed that can be selected seperately from the menu (`TypeEmbed` menu's only)

	name: :class:`str`
		An optional name for the button. Can be set to retrieve it later via :meth:`ReactionMenu.get_button_by_name()`

	details: :meth:`ReactionButton.set_caller_details()`
		The class method used to set the function and it's arguments to be called when the button is pressed
	"""

	Type = ButtonType

	def __init__(self, *, emoji: str, linked_to: ReactionButton.Type, event: ReactionButton.Event=None, **kwargs):
		super().__init__()
		self.emoji = emoji
		self.linked_to = linked_to
		# Note: self.event is set in super()
		
		self.custom_embed: discord.Embed = kwargs.get('embed')
		self.details: tuple = kwargs.get('details')
		self.name: str = kwargs.get('name')
		
		# abc
		self._menu: ReactionMenu = None
	
	def __str__(self):
		return self.emoji
	
	def __repr__(self):
		return f'<ReactionButton emoji={self.emoji!r} linked_to={ButtonType._get_buttontype_name_from_type(self.linked_to)} total_clicks={self.total_clicks} name={self.name!r}>'
	
	@classmethod
	def set_caller_details(cls, func: object, *args, **kwargs) -> NamedTuple:
		"""|class method| Set the parameters for the function you set for a :class:`ReactionButton` with a `linked_to` of `ReactionButton.Type.CALLER`

		Parameters
		----------
		func: :class:`object`
			The function object that will be called when the associated button is pressed
		
		*args: :class:`Any`
			An argument list that represents the parameters of that function
		
		**kwargs: :class:`Any`
			An argument list that represents the kwarg parameters of that function
		
		Raises
		------
		- `IncorrectType`: Parameter "func" was not a callable object
		"""
		if callable(func):
			Details = namedtuple('Details', ['func', 'args', 'kwargs'])
			func = func.callback if isinstance(func, Command) else func
			return Details(func=func, args=args, kwargs=kwargs)
		else:
			raise IncorrectType('Parameter "func" must be callable')
	
	@property
	def menu(self) -> ReactionMenu:
		"""
		Returns
		-------
		:class:`ReactionMenu`:
			The menu the button is currently operating under. Can be :class:`None` if the button is not registered to a menu
		"""
		return self._menu
	
	@classmethod
	def back(cls) -> ReactionButton:
		"""|class method| A factory method that returns a :class:`ReactionButton` with the following parameters set:
		
		- emoji: ◀️
		- linked_to: `ReactionButton.Type.PREVIOUS_PAGE`
		"""
		return cls(emoji=PaginationEmojis.BACK_BUTTON, linked_to=cls.Type.PREVIOUS_PAGE)
	
	@classmethod
	def next(cls) -> ReactionButton:
		"""|class method| A factory method that returns a :class:`ReactionButton` with the following parameters set:
		
		- emoji: ▶️
		- linked_to: `ReactionButton.Type.NEXT_PAGE`
		"""
		return cls(emoji=PaginationEmojis.NEXT_BUTTON, linked_to=cls.Type.NEXT_PAGE)
	
	@classmethod
	def go_to_first_page(cls) -> ReactionButton:
		"""|class method| A factory method that returns a :class:`ReactionButton` with the following parameters set:
		
		- emoji: ⏪
		- linked_to: `ReactionButton.Type.GO_TO_FIRST_PAGE`
		"""
		return cls(emoji=PaginationEmojis.FIRST_PAGE, linked_to=cls.Type.GO_TO_FIRST_PAGE)
	
	@classmethod
	def go_to_last_page(cls) -> ReactionButton:
		"""|class method| A factory method that returns a :class:`ReactionButton` with the following parameters set:
		
		- emoji: ⏩
		- linked_to: `ReactionButton.Type.GO_TO_LAST_PAGE`
		"""
		return cls(emoji=PaginationEmojis.LAST_PAGE, linked_to=cls.Type.GO_TO_LAST_PAGE)
	
	@classmethod
	def go_to_page(cls) -> ReactionButton:
		"""|class method| A factory method that returns a :class:`ReactionButton` with the following parameters set:
		
		- emoji: 🔢
		- linked_to: `ReactionButton.Type.GO_TO_PAGE`
		"""
		return cls(emoji=PaginationEmojis.GO_TO_PAGE, linked_to=cls.Type.GO_TO_PAGE)
	
	@classmethod
	def end_session(cls) -> ReactionButton:
		"""|class method| A factory method that returns a :class:`ReactionButton` with the following parameters set:
		
		- emoji: ⏹️
		- linked_to: `ReactionButton.Type.END_SESSION`
		"""
		return cls(emoji=PaginationEmojis.END_SESSION, linked_to=cls.Type.END_SESSION)
	
	@classmethod
	def all(cls) -> List[ReactionButton]:
		"""|class method| A factory method that returns a `list` of all base navigation buttons. Base navigation buttons are :class:`ReactionButton` with a `linked_to` of:
		
		- `ReactionButton.Type.GO_TO_FIRST_PAGE`
		- `ReactionButton.Type.PREVIOUS_PAGE`
		- `ReactionButton.Type.NEXT_PAGE`
		- `ReactionButton.Type.GO_TO_LAST_PAGE`
		- `ReactionButton.Type.GO_TO_PAGE`
		- `ReactionButton.Type.END_SESSION`

		They are returned in that order
		"""
		return [cls.go_to_first_page(), cls.back(), cls.next(), cls.go_to_last_page(), cls.go_to_page(), cls.end_session()]
