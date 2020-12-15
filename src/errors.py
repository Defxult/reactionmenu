"""
MIT License

Copyright (c) 2020 Defxult#8269

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
import inspect

class ReactionMenuException(Exception):
	"""Base Reaction Menu exception"""
	pass

class InvalidPage(ReactionMenuException):
	"""Raised when the page selected to remove does not exist"""
	pass

class SingleUseOnly(ReactionMenuException):
	"""When a method is called more than once"""
	pass
	
class DescriptionOversized(ReactionMenuException):
	"""The content of the menu has a character size >= 2000"""
	pass

class MenuSettingsMismatch(ReactionMenuException):
	"""Used settings for a static menu but is using dynamic methods and vice-versa"""
	pass

class DuplicateButton(ReactionMenuException):
	"""The emoji selected as a button has already been registered"""
	pass

class ImproperStyleFormat(ReactionMenuException):
	"""The custom style selected by the user did not meet formatting requirements"""
	def __init__(self):
		super().__init__('There needs to be at least but no more than 1 "$" character and at least but no more than 1 "&" character. "$" represents the current page, "&" represents the total amount of pages. Example: "On $ out of &"')

class ImproperButtonOrderChange(ReactionMenuException):
	"""Buttons were leftout/added when changing the order"""
	def __init__(self, missing, extra):
		super().__init__(inspect.cleandoc(f"""Missing or extra button(s) when changing the order. The button order list must match the buttons that were already added. You cannot add or leave out any buttons

			Missing = {missing if missing else "<none missing>"} | Extras = {extra if extra else "<no extras>"}

			NOTE: If the menu only has one page, you still need to include the "next_button" and "back_button" in the order, because those are there by default. Add them with.. 
			1 - Attributes ReactionMenu.default_back_button and ReactionMenu.default_next_button. 
			2 - Method ReactionMenu.help_appear_order can be used to print all emojis from the Buttons you've added to the python console for you to copy and paste in the desired order.
			3 - Method ReactionMenu.get_button_by_name to get the button object
		"""))

class TooManyButtons(ReactionMenuException):
	"""The amount of buttons registered is > 20 (over discords reaction limit)"""
	def __init__(self):
		super().__init__('Discord currently has a limit of 20 reactions or less per message. Remove 1 or more buttons')

class MissingSetting(ReactionMenuException):
	"""Raised when an action requires specific input from the user"""
	pass

class NoPages(ReactionMenuException):
	"""Tried to start the menu when they haven't added any pages"""
	def __init__(self):
		super().__init__('You cannot start a reaction menu when there aren\'t any pages')

class MenuAlreadyRunning(ReactionMenuException):
	"""Called a method that is not allowed to be called after the menu has started"""
	def __init__(self, message: str):
		super().__init__(message)

class ButtonNotFound(ReactionMenuException):
	"""Raised when the :meth:ReactionMenu.remove_button did not find any matching buttons"""
	pass