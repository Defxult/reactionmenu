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

import re
from collections import namedtuple
from datetime import datetime
from enum import Enum, auto
from typing import List, Set, Union

import discord
import dislash
from discord.ext.commands import Command

from .errors import ButtonsMenuException


class ComponentsButton(dislash.Button):
	"""A helper class for :class:`ButtonsMenu`. Determines the generic action a components button can perform. This should *NOT* be used with :class:`ReactionMenu` or :class:`TextMenu`

		.. added:: v1.1.0
	"""
	style = dislash.ButtonStyle

	ID_NEXT_PAGE =          '0'
	ID_PREVIOUS_PAGE =      '1'
	ID_GO_TO_FIRST_PAGE =   '2'
	ID_GO_TO_LAST_PAGE =    '3'
	ID_GO_TO_PAGE =         '4'
	ID_END_SESSION =        '5'
	ID_CALLER =             '6'
	ID_SEND_MESSAGE =       '7'

	# would have imported from .abc, but circular imports
	EMOJI_BACK_BUTTON = 	'◀️'
	EMOJI_NEXT_BUTTON = 	'▶️'
	EMOJI_FIRST_PAGE =  	'⏪'
	EMOJI_LAST_PAGE =   	'⏩'
	EMOJI_GO_TO_PAGE =  	'🔢'
	EMOJI_END_SESSION = 	'❌'

	def __init__(self, *, style: dislash.ButtonStyle, label: str, custom_id: str=None, emoji: Union[discord.PartialEmoji, str]=None, url: str=None, disabled: bool=False, followup: 'ComponentsButton.Followup'=None):
		self.followup = followup
		self.__clicked_by = set()
		self.__total_clicks = 0
		self.__last_clicked: datetime = None
		super().__init__(style=style, label=label, emoji=emoji, custom_id=custom_id, url=url, disabled=disabled)

	def __repr__(self):
	    return f'<ComponentsButton label={self.label!r} custom_id={self._get_id_name_from_id(self.custom_id)} style={self.style} emoji={self.emoji!r} url={self.url} disabled={self.disabled} total_clicks={self.__total_clicks}>'

	class Followup:
		"""A class that represents the message sent using a :class:`ComponentsButton`. Contains parameters similiar to discord.py's `Messageable.send`. Only to be used with :class:`ComponentsButton` kwarg "followup".
		It is to be noted that this should not be used with :class:`ComponentsButton` with a "style" of `ComponentsButton.style.link` because link buttons do not send interaction events.
		
		Parameters
		----------
		content: :class:`str`
			Message to send (defaults to :class:`None`)

		embed: :class:`discord.Embed`
			Embed to send (defaults to :class:`None`)

		file: :class:`discord.File`
			File to send (defaults to :class:`None`) *NOTE* If the :class:`ComponentsButton` custom_id is `ComponentsButton.ID_SEND_MESSAGE`, the file will be ignored because of discord API limitations
		
		tts: :class:`bool`
			If discord should read the message aloud (defaults to `False`) *NOTE* Not valid for `ephemeral` messages
		
		allowed_mentions: :class:`discord.AllowedMentions`
			Controls the mentions being processed in the menu message (defaults to :class:`None`) *NOTE* Not valid for `ephemeral` messages
		
		delete_after: Union[:class:`int`, :class:`float`]
			Amount of time to wait before the message is deleted (defaults to :class:`None`) *NOTE* Not valid for `ephemeral` messages
		
		ephemeral: :class:`bool`
			If the message will be hidden from everyone except the person that clicked the button (defaults to `False`) *NOTE* This is only valid for a :class:`ComponentsButton` with custom_id `ComponentsButton.ID_SEND_MESSAGE`
		"""
		
		__slots__ = ('content', 'embed', 'file', 'tts', 'allowed_mentions', 'delete_after', 'ephemeral', '_caller_info')

		def __init__(self, content: str=None, *, embed: discord.Embed=None, file: discord.File=None, tts: bool=False, allowed_mentions: discord.AllowedMentions=None, delete_after: Union[int, float]=None, ephemeral: bool=False):
			self.content = content
			self.embed = embed
			self.file = file
			self.tts = tts
			self.allowed_mentions = allowed_mentions
			self.delete_after = delete_after
			self.ephemeral = ephemeral
			self._caller_info: 'NamedTuple' = None
		
		def _to_dict(self) -> dict:
			new = {}
			for i in self.__slots__:
				new[i] = getattr(self, i)
			return new
		
		def set_caller_details(self, func: object, *args, **kwargs):
			"""Set the parameters for the function you set for a :class:`ComponentsButton` with the custom_id `ComponentsButton.ID_CALLER`

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
			- `ButtonsMenuException`: Parameter "func" was not a callable object
			"""
			if not callable(func): raise ButtonsMenuException('Parameter "func" must be callable')
			Details = namedtuple('Details', ['func', 'args', 'kwargs'])
			self._caller_info = Details(func=func, args=args, kwargs=kwargs)
	
	@property
	def clicked_by(self) -> Set[discord.Member]:
		"""
		Returns
		-------
		Set[:class:`discord.Member`]:
			The members who clicked the button
		"""
		return self.__clicked_by

	@property
	def total_clicks(self) -> int:
		"""
		Returns
		-------
		:class:`int`:
			The amount of clicks on the button
		"""
		return self.__total_clicks

	@property
	def last_clicked(self) -> datetime:
		"""
		Returns
		-------
		:class:`datetime`:
			The time in UTC for when the button was last clicked. Can be :class:`None` if the button has not been clicked
		"""
		return self.__last_clicked

	@classmethod
	def _all_ids(cls) -> List[int]:
		ids = []
		for key, val in cls.__dict__.items():
			key = str(key) # str() because of ButtonStyle
			if key.startswith('ID_'):
				ids.append(val)
		return ids

	@classmethod
	def _get_id_name_from_id(cls, id_: str) -> str:
		# if its a CALLER or SEND_MESSAGE id, convert to it's true representation, because when passed, it's form is "[ButtonID]_[unique ID]"
		# see :meth:`_button_add_check` for details
		CALLER_OR_SEND = re.compile(r'_\d+')
		if re.search(CALLER_OR_SEND, id_):
			id_ = re.sub(CALLER_OR_SEND, '', id_)
		
		for key, val in cls.__dict__.items():
			if id_ == val:
				return f'ComponentsButton.{key}'

	@classmethod
	def _to_dict_ids(cls) -> dict:
		new = {}
		for key, val in cls.__dict__.items():
			key = str(key) # str() because of ButtonStyle
			if key.startswith('ID_'):
				new[key] = val
		return new

class ButtonType(Enum):
	"""A helper class for :class:`ReactionMenu` and :class:`TextMenu`. Determines the generic action a button can perform. This should *NOT* be used with :class:`ButtonsMenu`
	
		.. changes::
			v1.0.1
				Added :attr:ButtonType.GO_TO_PAGE
			v1.0.3
				Added :attr:ButtonType.CALLER
				Added :meth:caller_details
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
				Added :attr:details
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
		"""
			.. changes::
				v1.0.9
					Replaced old string formatting (%s) with fstring
		"""
		return f'<Button emoji={self.emoji!r} linked_to={self.linked_to} custom_embed={self.custom_embed} details={self.details} name={self.name!r}>'
