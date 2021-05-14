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

from enum import Enum, auto
from discord.ext.commands import Command

class ButtonType(Enum):
	"""A helper class for :class:`ReactionMenu`. Determines the generic action a button can perform
	
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
		name = f'{self.name!r}' if self.name else None
		return f'<Button emoji={self.emoji!r} linked_to={self.linked_to} custom_embed={self.custom_embed} details={self.details} name={name}>'
