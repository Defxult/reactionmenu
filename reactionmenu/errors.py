"""
MIT License

Copyright (c) 2021-present @defxult

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

class MenuException(Exception):
	"""Base exception for all menu's"""
	pass

class ViewMenuException(MenuException):
	"""Base :class:`ViewMenu` exception"""
	pass

class ReactionMenuException(MenuException):
	"""Base :class:`ReactionMenu` exception"""
	pass

class IncorrectType(MenuException):
	"""Raised when the expected type was not given"""
	def __init__(self, message: str):
		super().__init__(message)

class NoButtons(MenuException):
	"""Raised when the menu was started but no buttons were registered or the action initiated requires buttons to be registered"""
	def __init__(self, message: str='You cannot start the menu when no buttons are registered'):
		super().__init__(message)

class InvalidPage(MenuException):
	"""Raised when the page selected to remove does not exist"""
	pass
	
class DescriptionOversized(MenuException):
	"""Used for `TypeEmbedDynamic` menus. The embed description of the menu has a character count > 4096"""
	pass

class MenuSettingsMismatch(MenuException):
	"""Used settings for a specific `menu_type` but different/unrecognized values for those settings were given"""
	pass

class DuplicateButton(MenuException):
	"""The emoji selected as a button has already been registered"""
	pass

class ImproperStyleFormat(MenuException):
	"""The custom style selected by the user did not meet formatting requirements"""
	def __init__(self):
		super().__init__('There needs to be at least but no more than 1 "$" character and at least but no more than 1 "&" character. "$" represents the current page, "&" represents the total amount of pages. Example: "On $ out of &"')

class TooManyButtons(MenuException):
	"""The amount of buttons registered is > 20 (over discords reaction limit)"""
	def __init__(self, message: str='Discord currently has a limit of 20 reactions or less per message. Remove 1 or more buttons'):
		super().__init__(message)

class MissingSetting(MenuException):
	"""Raised when an action requires specific input from the user"""
	pass

class NoPages(MenuException):
	"""Tried to start the menu when they haven't added any pages"""
	def __init__(self, message: str="You cannot start a menu when you haven't added any pages"):
		super().__init__(message)

class MenuAlreadyRunning(MenuException):
	"""Called a method that is not allowed to be called after the menu has started"""
	def __init__(self, message: str):
		super().__init__(message)

class ButtonNotFound(MenuException):
	"""Raised when :meth:`.remove_button()` did not find any matching buttons"""
	pass

class SelectNotFound(MenuException):
	"""Raised when :meth:`.remove_select()` did not find any matching selects
	
		.. added:: v3.1.0
	"""
	pass
