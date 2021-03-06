### v1.0.8 - May 4, 2021
* Added `ReactionMenu.delete_on_timeout`

### v1.0.7 - Mar. 30, 2021
* Fixed an issue where if a menu's timeout was set to `None` and the `navigation_speed` was set to `ReactionMenu.FAST`, an error would occur

### v1.0.6 - Mar. 22, 2021
* Added the ability to start a menu in a specific channel
* Fixed an issue where custom embeds in a dynamic menu would not display all implemented values from that embed 

### v1.0.5 - Mar.19, 2021
* Added class variable `ReactionMenu.NORMAL`
* Added class variable `ReactionMenu.FAST`
* Added `ReactionMenu` kwarg "`navigation_speed`". Used with either `ReactionMenu.NORMAL` or `ReactionMenu.FAST`
* Fixed an issue where if multiple menu instances were created and stopped in a single execution, calling `ReactionMenu.stop()` could stop the wrong instance
* Fixed an issue where if an exception was to occur during the startup of a menu, exceptions such as discord.py's "missing permissions" exception would be suppressed and not be displayed 
* Fixed an issue with `Button` objects where a duplicate name/emoji could be used

### v1.0.4 - Mar. 13, 2021
* Small additional update for v1.0.3. Support for `@client.command()` functions to be used with `ButtonType.CALLER`

### v1.0.3 - Mar. 13, 2021
* Added the ability for buttons to call functions
* Added new `ButtonType` (`ButtonType.CALLER`)
* Added class method `ButtonType.caller_details()`
* Fixed an issue where all exceptions were suppressed specifically inside the execution method

### v1.0.2 - Feb. 19, 2021
* Added class method `ReactionMenu.get_sessions_count()`
* Added the option to delete the messages sent when interacting with the menu via `ButtonType.GO_TO_PAGE`. Repeatedly using `ButtonType.GO_TO_PAGE` can sometimes make the chat look like spam

### v1.0.1 - Feb. 16, 2021
* Added the ability to limit the amount of active menu sessions
* Added new `ButtonType` (`ButtonType.GO_TO_PAGE`)
* Added "`go_to_page_buttons`" property
* Added "`total_pages`" property
* Added class method `ReactionMenu.set_sessions_limit()`
* Added class method `ReactionMenu.cancel_all_sessions()`
