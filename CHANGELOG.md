## v1.0.9 » Upcoming release
#### New Features
* Added new type of reaction menu (`TextMenu`). Just like the normal reaction menu but no embeds are involved, only plain text is used. `TextMenu` has limited options compared to `ReactionMenu` ([docs](https://github.com/Defxult/reactionmenu#textmenu))
* Added auto-pagination. The ability for the menu to turn pages on it's own. In addition to this, the `ReactionMenu` constructors `back_button` and `next_button` parameters can now be set to `None` if you intend to set the menu as an auto-pagination menu ([docs](https://github.com/Defxult/reactionmenu#auto-pagination))
  * `ReactionMenu.set_as_auto_paginator(turn_every: Union[int, float])`
  * `ReactionMenu.update_turn_every(turn_every: Union[int, float])`
  * `ReactionMenu.update_all_turn_every(turn_every: Union[int, float])`
  * `ReactionMenu.refresh_auto_pagination_data(*embeds: Embed)`
  * `ReactionMenu.stop_all_auto_sessions()`
  * `ReactionMenu.auto_turn_every`
  * `ReactionMenu.auto_paginator`
* Added basic emojis. Used as in-house helper variables to set your `back_button`/`next_button` parameters in `ReactionMenu`/`TextMenu` as well as the `emoji` parameter in `Button` ([docs](https://github.com/Defxult/reactionmenu#supported-emojis))
  * `ReactionMenu.EMOJI_NEXT_BUTTON`
  * `ReactionMenu.EMOJI_BACK_BUTTON`
  * `ReactionMenu.EMOJI_FIRST_PAGE`
  * `ReactionMenu.EMOJI_LAST_PAGE`
  * `ReactionMenu.EMOJI_GO_TO_PAGE`
  * `ReactionMenu.EMOJI_END_SESSION`
* Added the ability to track how long a menu session has been active ([docs](https://github.com/Defxult/reactionmenu#all-attributes-for-reactionmenu))
  * `ReactionMenu.run_time`
* Added the ability to set if only members with certain roles can control the menu ([docs](https://github.com/Defxult/reactionmenu#options-of-the-reactionmenu-constructor-kwargs))
  * `ReactionMenu.only_roles`
* Added the ability to gracefully stop all running menu's ([docs](https://github.com/Defxult/reactionmenu#setting-limits))
  * `ReactionMenu.stop_all_sessions()`
* Added the ability to stop a specific menu by it's name ([docs](https://github.com/Defxult/reactionmenu#all-methods-for-reactionmenu))
  * `ReactionMenu.stop_session(name: str, include_all=False)`
* Added the ability to get a session by it's name ([docs](https://github.com/Defxult/reactionmenu#all-methods-for-reactionmenu))
  * `ReactionMenu.get_session(name: str)`
* Added the ability to get all active sessions ([docs](https://github.com/Defxult/reactionmenu#all-methods-for-reactionmenu))
  * `ReactionMenu.get_all_sessions()`
* Added `__repr__` for `ReactionMenu`
* Added documentation (doc strings) to a lot more properties/methods to easily see what it does and what the return type is
* Added new error type: `IncorrectType`. Mainly raised when using a property setter and the supplied value type was not what was expected

#### Bug Fixes
* Fixed an issue where it was possible to call `ReactionMenu.set_main_pages()` and `ReactionMenu.set_last_pages()` without actually implementing the necessary parameters

* Fixed an issue where if `ReactionMenu.clear_all_buttons()` was called and an attempt to access properties `ReactionMenu.default_back_button` or `ReactionMenu.default_next_button`, an error would occur. In addition, if other buttons were added to the menu after `ReactionMenu.clear_all_buttons()` was called and the default back/next properties were accessed, it would not return the true default back/next buttons. It would return the most recently added button after `ReactionMenu.clear_all_buttons()` was called. Accessing `ReactionMenu.default_back_button` or `ReactionMenu.default_next_button` now returns the true default back/next buttons (the buttons set in the `ReactionMenu` constructor), even if all buttons were cleared

#### Breaking Change
  * *removed* `ReactionMenu.cancel_all_sessions()`
    * Before this update, `.cancel_all_sessions()` was used as an easy way to essentially "pull the plug" on all menu session processing. Although it being effective, it left certain values of the menu unchanged/not removed which was okay in versions `<= v1.0.8`. With this update, because of the changes made for how the overall menu functions, those values are now way too important to be left unchanged/not removed. Using the new class method `ReactionMenu.stop_all_sessions()` provides a much cleaner way to end all processing for active menus
  * *changed* Some property return types
    * There were some properties that would return an empty list if there were no items in their associated list. With `v1.0.9`, the below properties now return `None` instead of an empty list if their list contains no items
    * `ReactionMenu.all_buttons`
    * `ReactionMenu.next_buttons`
    * `ReactionMenu.back_buttons`

## v1.0.8 » May 4, 2021
#### New Features
* Added `ReactionMenu.delete_on_timeout` ([docs](https://github.com/Defxult/reactionmenu#options-of-the-reactionmenu-constructor-kwargs))

## v1.0.7 » Mar. 30, 2021
#### Bug Fixes
* Fixed an issue where if a menu's timeout was set to `None` and the `navigation_speed` was set to `ReactionMenu.FAST`, an error would occur

## v1.0.6 » Mar. 22, 2021
#### New Features
* Added the ability to start a menu in a specific channel ([docs](https://github.com/Defxult/reactionmenu#startingstopping-the-reactionmenu))

#### Bug Fixes
* Fixed an issue where custom embeds in a dynamic menu would not display all implemented values from that embed 

## v1.0.5 » Mar.19, 2021
#### New Features
* Added `ReactionMenu` kwarg `navigation_speed`. Used with the below class attributes ([docs](https://github.com/Defxult/reactionmenu#options-of-the-reactionmenu-constructor-kwargs))
  * `ReactionMenu.NORMAL`
  * `ReactionMenu.FAST`
#### Bug Fixes
* Fixed an issue where if multiple menu instances were created and stopped in a single execution, calling `ReactionMenu.stop()` could stop the wrong instance

* Fixed an issue where if an exception was to occur during the startup of a menu, exceptions such as discord.py's "missing permissions" exception would be suppressed and not be displayed 

* Fixed an issue with `Button` objects where a duplicate name/emoji could be used

## v1.0.4 » Mar. 13, 2021
#### New Features
* Small additional update for `v1.0.3`. Support for `@client.command()` functions to be used with `ButtonType.CALLER` ([docs](https://github.com/Defxult/reactionmenu#buttons-with-buttontypecaller))

## v1.0.3 » Mar. 13, 2021
#### New Features
* Added the ability for buttons to call functions ([docs](https://github.com/Defxult/reactionmenu#buttons-with-buttontypecaller))
* Added new `ButtonType` (`ButtonType.CALLER`) ([docs](https://github.com/Defxult/reactionmenu#all-buttontypes))
* Added class method `ButtonType.caller_details()` ([docs](https://github.com/Defxult/reactionmenu#buttons-with-buttontypecaller))

#### Bug Fixes
* Fixed an issue where all exceptions were suppressed specifically inside the execution method

## v1.0.2 » Feb. 19, 2021
#### New Features
* Added class method `ReactionMenu.get_sessions_count()` ([docs](https://github.com/Defxult/reactionmenu#all-methods-for-reactionmenu))
* Added the option to delete the messages sent when interacting with the menu via `ButtonType.GO_TO_PAGE` (`ReactionMenu` kwarg `delete_interactions`). Repeatedly using `ButtonType.GO_TO_PAGE` can sometimes make the chat look like spam ([docs](https://github.com/Defxult/reactionmenu#options-of-the-reactionmenu-constructor-kwargs))

## v1.0.1 » Feb. 16, 2021
#### New Features
* Added the ability to limit the amount of active menu sessions ([docs](https://github.com/Defxult/reactionmenu#setting-limits))
   * `ReactionMenu.set_sessions_limit()`
* Added new `ButtonType` (`ButtonType.GO_TO_PAGE`) ([docs](https://github.com/Defxult/reactionmenu#all-buttontypes))
* Added `go_to_page_buttons` property ([docs](https://github.com/Defxult/reactionmenu#all-attributes-for-reactionmenu))
* Added `total_pages` property ([docs](https://github.com/Defxult/reactionmenu#all-attributes-for-reactionmenu))
* Added class method `ReactionMenu.cancel_all_sessions()` (**removed since** `v1.0.9`)
