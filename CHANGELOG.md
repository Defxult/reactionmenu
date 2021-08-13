<!-- ## Key
* `BM` = `ButtonsMenu`
* `RM` = `ReactionMenu`
* `TM` = `TextMenu` -->

## v3.0.0 » After discord.py 2.0 officially releases
#### Breaking Changes
Discords Buttons feature has been implemented using discord.py instead of a 3rd party library. Meaning this library is now only dependent on discord.py. With that said, two classes have been renamed/removed to support discord.py's `Views`
* *removed* `ButtonsMenu` class
  * This has been replaced with `ViewMenu`
* *removed* `ComponentsButton` class
  * This has been replaced with `ViewButton`
* *removed* All `ComponentsButton` factory methods. They've been renamed and are now apart of the `ViewButton` class
  * `ViewButton.back()` replaced `ComponentsButton.basic_back()`
  * `ViewButton.next()` replaced `ComponentsButton.basic_next()`
  * `ViewButton.go_to_first_page()` replaced `ComponentsButton.basic_go_to_first_page()`
  * `ViewButton.go_to_last_page()` replaced `ComponentsButton.basic_go_to_last_page()`
  * `ViewButton.go_to_page()` replaced `ComponentsButton.basic_go_to_page()`
  * `ViewButton.end_session()` replaced `ComponentsButton.basic_end_session()`


<!-- ## v2.0.3 » Future release
#### New Features
* `RM|TM` The `Button` class now has similar attributes to `ComponentsButton`
  * `Button.menu`
  * `Button.clicked_by`
  * `Button.total_clicks`
  * `Button.last_clicked`
* `BM|RM|TM` `ReactionMenu.EMOJI_END_SESSION` is now ⏹️ instead of ❌

## v2.0.2 » Jul. 6, 2021
#### New Features
* `BM` Added the ability to disable or remove a button from the menu when it has been clicked x amount of times

## v2.0.1 » Jul. 2, 2021
#### New Features
* Not a new feature, but Discord has increased the embed description length limit from 2048 to 4096. Exception `DescriptionOversized`, typically raised when using a dynamic menu and the amount of `rows_requested` is too large for the amount of information received, has been updated to reflect that change
* `BM` Added `ComponentsButton.ID_CUSTOM_EMBED` for `ComponentsButton`. Buttons that go to the specified embed when clicked and are not apart of the normal pagination process
* `BM` Added the ability to get the `ButtonsMenu` instance from a `ComponentsButton`
  * `ComponentsButton.menu`
* `BM` Added the ability to call a function when buttons are pressed
  * `ButtonsMenu.set_relay()`
  * `ButtonsMenu.remove_relay()`
* `RM|TM` Added the ability to remove relays that have been set
  * `ReactionMenu.remove_relay()`

#### Bug Fixes
* `BM` Fixed an issue where a button with `ComponentsButton.ID_CALLER` could not call discord.py command functions
* `BM` Fixes for method `ButtonsMenu.update()`
  * Fixed an issue where if a button with `ComponentsButton.ID_CALLER` or `ComponentsButton.ID_SEND_MESSAGE` was already registered to the menu and an attempt to reuse that button during a `ButtonsMenu.update()` call, an error would occur
  * Fixed an issue where if a menu was updated and there were no `new_pages`, the page index value would still be from before the update, and clicking a back/next button would go to the wrong page
  * Fixed an issue where if a menu was updated and there were `new_pages` (embeds) that contained footers, the footer information would be removed

## v2.0.0 » Jun. 27, 2021
#### New Features
* Added new type of menu (`ButtonsMenu`). Discords new [Buttons](https://support.discord.com/hc/en-us/articles/1500012250861-Bots-Buttons) feature
* `RM|TM` Added the ability to call a function upon menu timeout
  * `ReactionMenu.set_on_timeout(func: object)`
* `RM|TM` Added the ability to get the menu object from a message ID
  * `ReactionMenu.get_menu_from_message(message_id: int)`
* `RM|TM` Added the ability to set menu session limits per guild, channel, or member (before you could only set per guild)
* `RM|TM` Added the ability to remove limits that have been set
  * `ReactionMenu.remove_limit()`
* `RM|TM` Added the ability to access the `discord.Member` object of the person that started the menu
  * `ReactionMenu.owner`
* `RM|TM` Added `owner` to `__repr__`
* `RM|TM` Added the ability to get all active DM sessions
  * `ReactionMenu.get_all_dm_sessions()`

## v1.0.9 » Jun. 1, 2021
#### New Features
* Added new type of reaction menu (`TextMenu`). Just like the normal reaction menu but no embeds are involved, only plain text is used. `TextMenu` has limited options compared to `ReactionMenu`
* Added auto-pagination. The ability for the menu to turn pages on it's own. In addition to this, the `ReactionMenu` constructors `back_button` and `next_button` parameters can now be set to `None` if you intend to set the menu as an auto-pagination menu
  * `ReactionMenu.set_as_auto_paginator(turn_every: Union[int, float])`
  * `ReactionMenu.update_turn_every(turn_every: Union[int, float])`
  * `ReactionMenu.update_all_turn_every(turn_every: Union[int, float])`
  * `ReactionMenu.refresh_auto_pagination_data(*embeds: Embed)`
  * `ReactionMenu.stop_all_auto_sessions()`
  * `ReactionMenu.auto_turn_every`
  * `ReactionMenu.auto_paginator`
* Added basic emojis. Used as in-house helper variables to set your `back_button`/`next_button` parameters in `ReactionMenu`/`TextMenu` as well as the `emoji` parameter in `Button`
  * `ReactionMenu.EMOJI_NEXT_BUTTON`
  * `ReactionMenu.EMOJI_BACK_BUTTON`
  * `ReactionMenu.EMOJI_FIRST_PAGE`
  * `ReactionMenu.EMOJI_LAST_PAGE`
  * `ReactionMenu.EMOJI_GO_TO_PAGE`
  * `ReactionMenu.EMOJI_END_SESSION`
* Added the ability for a menu to be interacted with in direct messages. If a menu session is in a direct message, the following settings are disabled/changed because of discord limitations and resource/safety reasons:
  * `ReactionMenu.clear_reactions_after` (set to `False`)
  * `ReactionMenu.navigation_speed` (set to `ReactionMenu.FAST`)
  * `ReactionMenu.delete_interactions` (set to `False`)
  * `ReactionMenu.only_roles` (set to `None`)
  * `ReactionMenu.timeout` (set to `60.0` if set to `None`)
  * `ReactionMenu.auto_paginator` (set to `False`)
* Added the ability to track how long a menu session has been active
  * `ReactionMenu.run_time`
* Added the ability to set if only members with certain roles can control the menu
  * `ReactionMenu.only_roles`
* Added the ability to access the `discord.Message` object the menu is operating from
  * `ReactionMenu.message`
* Added the ability to gracefully stop all running menu's
  * `ReactionMenu.stop_all_sessions()`
* Added the ability to stop a specific menu by it's name
  * `ReactionMenu.stop_session(name: str, include_all=False)`
* Added the ability to get a session by it's name
  * `ReactionMenu.get_session(name: str)`
* Added the ability to get all active sessions
  * `ReactionMenu.get_all_sessions()`
* Added the ability for a menu reaction press to call other functions with the information of who pressed the reaction, what reaction was pressed, the time it was pressed, and the menu's object
  * `ReactionMenu.set_relay(func)`
* Added `__repr__` for `ReactionMenu`
* Added documentation (doc strings) to a lot more properties to easily see what it does and what the return type is
* Added new error types: `IncorrectType`, mainly raised when using a property setter and the supplied value type was not what was expected. `NoButtons`, raised when the menu was started but there were no buttons registered

#### Bug Fixes
* Fixed an issue where it was possible to call `ReactionMenu.set_main_pages()` and `ReactionMenu.set_last_pages()` without actually implementing the necessary parameters

* Fixed an issue where if `ReactionMenu.clear_all_buttons()` was called and an attempt to access properties `ReactionMenu.default_back_button` or `ReactionMenu.default_next_button`, an error would occur. In addition, if other buttons were added to the menu after `ReactionMenu.clear_all_buttons()` was called and the default back/next properties were accessed, it would not return the true default back/next buttons. It would return the most recently added button after `ReactionMenu.clear_all_buttons()` was called. Accessing `ReactionMenu.default_back_button` or `ReactionMenu.default_next_button` now returns the true default back/next buttons (the buttons set in the `ReactionMenu` constructor), even if all buttons were cleared

* Fixed an issue where if a menu was sent to a channel other than the one it was triggered in using the `send_to` kwarg in method `ReactionMenu.start()`. Using a `Button` with `ButtonType.GO_TO_PAGE`, the prompt would ask what page you'd like to go to but wouldn't respond when a message was sent in the channel where the prompt was

* Fixed an issue where if the menu was started with no buttons registered, an error would occur that was not informative. If there's an attempt to start the menu when no buttons are registered, an informative error (exception `NoButtons`) is now raised 

* Fixed an issue where if buttons were added after all buttons were removed and those buttons did not have their `name` kwarg set, an error would occur. The menu will now run as expected if buttons were added after all buttons were removed from the menu regardless of if a buttons optional kwarg was not set

#### Breaking Change
  * *removed* `ReactionMenu.cancel_all_sessions()`
    * Before this update, `.cancel_all_sessions()` was used as an easy way to essentially "pull the plug" on all menu session processing. Although it being effective, it left certain values of the menu unchanged/not removed which was okay in versions `<= 1.0.8`. With this update, because of the changes made for how the overall menu functions, those values are now way too important to be left unchanged/not removed. Using the new class method `ReactionMenu.stop_all_sessions()` provides a much cleaner way to end all processing for active menus
  * *changed* Some property return types
    * There were some properties that would return an empty list if there were no items in their associated list. With `v1.0.9`, the below properties now return `None` instead of an empty list if their list contains no items
    * `ReactionMenu.all_buttons`
    * `ReactionMenu.next_buttons`
    * `ReactionMenu.back_buttons`

## v1.0.8 » May 4, 2021
#### New Features
* Added `ReactionMenu.delete_on_timeout`

## v1.0.7 » Mar. 30, 2021
#### Bug Fixes
* Fixed an issue where if a menu's timeout was set to `None` and the `navigation_speed` was set to `ReactionMenu.FAST`, an error would occur

## v1.0.6 » Mar. 22, 2021
#### New Features
* Added the ability to start a menu in a specific channel

#### Bug Fixes
* Fixed an issue where custom embeds in a dynamic menu would not display all implemented values from that embed 

## v1.0.5 » Mar. 19, 2021
#### New Features
* Added `ReactionMenu` kwarg `navigation_speed`. Used with the below class attributes
  * `ReactionMenu.NORMAL`
  * `ReactionMenu.FAST`
#### Bug Fixes
* Fixed an issue where if multiple menu instances were created and stopped in a single execution, calling `ReactionMenu.stop()` could stop the wrong instance

* Fixed an issue where if an exception was to occur during the startup of a menu, exceptions such as discord.py's "missing permissions" exception would be suppressed and not be displayed 

* Fixed an issue with `Button` objects where a duplicate name/emoji could be used

## v1.0.4 » Mar. 13, 2021
#### New Features
* Small additional update for `v1.0.3`. Support for `@client.command()` functions to be used with `ButtonType.CALLER`
## v1.0.3 » Mar. 13, 2021
#### New Features
* Added the ability for buttons to call functions
* Added new `ButtonType` (`ButtonType.CALLER`)
* Added class method `ButtonType.caller_details()`

#### Bug Fixes
* Fixed an issue where all exceptions were suppressed specifically inside the execution method

## v1.0.2 » Feb. 19, 2021
#### New Features
* Added class method `ReactionMenu.get_sessions_count()`
* Added the option to delete the messages sent when interacting with the menu via `ButtonType.GO_TO_PAGE` (`ReactionMenu` kwarg `delete_interactions`). Repeatedly using `ButtonType.GO_TO_PAGE` can sometimes make the chat look like spam

## v1.0.1 » Feb. 16, 2021
#### New Features
* Added the ability to limit the amount of active menu sessions
   * `ReactionMenu.set_sessions_limit()`
* Added new `ButtonType` (`ButtonType.GO_TO_PAGE`)
* Added `go_to_page_buttons` property
* Added `total_pages` property
* Added class method `ReactionMenu.cancel_all_sessions()` (**removed since** `v1.0.9`) -->
