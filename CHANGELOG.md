## v3.1.0 » Future Release

#### Breaking Changes
* **This library is no longer dependent on Pycord. It has changed back to discord.py**
* Parameter `ctx` has been changed to `method` for `ReactionMenu` & `ViewMenu` constructor and is now positional only
* Parameter `menu_type` for `ReactionMenu` & `ViewMenu` constructor is now keyword only
* The auto-paginate feature for `ReactionMenu` has been removed
* The `Page` class has been added. Represents each "page" added via `.add_page()`/`.add_pages()`
* Using `.last_viewed` now returns a `Page`. `.pages` now returns a `List[Page]`
* Class methods `ViewButton.skip()` & `ReactionButton.skip()` has been renamed to `.generate_skip()`
* The default behavior for the below methods have changed. Previously, using the below methods would return/stop menu's for both `ReactionMenu` & `ViewMenu`. With this update, each method by default now returns or stops menu's according to whichever class the method was invoked from. For example, `ViewMenu.stop_all_sessions()` only stops all `ViewMenu` sessions instead of all `ReactionMenu` sessions as well as `ViewMenu` sessions. 
  * `.get_all_dm_sessions()`
  * `.get_all_sessions()`
  * `.get_session(name: str)`
  * `.stop_all_sessions()`
  * `.stop_session(name: str, include_all=False)`
  * `.get_sessions_count()`

With this change, methods `.split_sessions()` & `.stop_only()` have been removed
#### New Features
##### ReactionMenu & ViewMenu
* Pagination is no longer limited to just embeds or text. The normal embed menu can now paginate with embeds, text, as well as files. With this, method `.add_page()` has two new parameters
  * Old: `.add_page(embed)`
  * New: `.add_page(embed=MISSING, content=None, files=MISSING)`
* Added class method `quick_start()`. Start a menu with it's default settings only adding the pages
* Added property `menu_type`. Displays the menu type that was set in the constructor
* Added method `.randomize_embed_colors()`. Selects a random color for all embeds added to the menu
* Added method `.version_info()`. A simple shortcut to function `reactionmenu.version_info()`
* Added the ability to set the separator between the page director and embed footer text via the `separator` parameter
  * `.set_page_director_style(..., separator=DEFAULT)`
##### ViewMenu Only
* Added the `persist` kwarg to `ViewButton`. This prevents link buttons from being disabled/removed when the menu times out or is stopped so they can remain clickable
* Added class `ViewSelect`. Used to choose categories in the menu.  With the addition of selects, the following methods have been added
  * `.add_select(select: ViewSelect)`
  * `.remove_select(select: ViewSelect)`
  * `.remove_all_selects()`
  * `.disable_select(select: ViewSelect)`
  * `.disable_all_selects()`
  * `.enable_select(select: ViewSelect)`
  * `.enable_all_selects()`
  * `.get_select(title: Union[str, None])`



## v3.0.2 » GitHub Only
<details>
  <summary>Click to display changelog</summary>
 
#### New Features
##### ReactionMenu & ViewMenu
* Added class method `quick_start()`. Start a menu with it's default settings only adding the pages
* Added property `menu_type`. Displays the menu type that was set in the constructor
##### ViewMenu Only
* Added the `persist` kwarg to `ViewButton`. This prevents link buttons from being disabled/removed when the menu times out or is stopped so they can remain clickable

#### Changes
##### ReactionMenu & ViewMenu
* The default behavior for the below methods have changed. Previously, using the below methods would return/stop menu's for both `ReactionMenu` & `ViewMenu`. With this update, each method by default now returns or stops menu's according to whichever class the method was invoked from. For example, `ViewMenu.stop_all_sessions()` only stops all `ViewMenu` sessions instead of all `ReactionMenu` sessions and `ViewMenu` sessions. This is done with the addition of the `fixed` parameter for the following methods. If you like the old behavior, simply set the `fixed` parameter to `False`
  * `.get_all_dm_sessions(fixed=True)`
  * `.get_all_sessions(fixed=True)`
  * `.get_session(name: str, fixed=True)`
  * `.stop_all_sessions(fixed=True)`
  * `.stop_session(name: str, include_all=False, fixed=True)`
  * `.get_sessions_count(fixed=True)`
  
  With this change, method `.stop_only()` is now deprecated
 </details>


## v3.0.1 » Feb. 02, 2022
<details>
  <summary>Click to display changelog</summary>

#### Bug Fixes
* Fixed an issue where exceptions were being suppressed if one was to occur during the pagination process (`ReactionMenu` only)

#### New Features
##### ReactionMenu & ViewMenu
* Added method `wait_until_close()`
</details>




## v3.0.0 » Jan. 29, 2022
<details>
  <summary>Click to display changelog</summary>

#### Library Change
* With the discontinuation of discord.py, this library is now dependent on [pycord](https://github.com/Pycord-Development/pycord)

#### Breaking Changes
* *changed* `ReactionMenu.STATIC` and `ReactionMenu.DYNAMIC` have been renamed
  * Old: `ReactionMenu.STATIC`
  * New: `ReactionMenu.TypeEmbed`
  * Old: `ReactionMenu.DYNAMIC`
  * New: `ReactionMenu.TypeEmbedDynamic`
* *changed/removed* The parameters of `ReactionMenu` have been changed
  * Old: `ReactionMenu(ctx, back_button='⬅️', next_button='➡️', config=ReactionMenu.STATIC)`
  * New: `ReactionMenu(ctx, menu_type=ReactionMenu.TypeEmbed)`
* *changed/removed* `ReactionMenu` and `TextMenu` are no longer separate classes. `TextMenu` has been merged into `ReactionMenu`. You can use a text menu by doing the following
  * `ReactionMenu(..., menu_type=ReactionMenu.TypeText)`
* *changed* The `Button` class has been renamed to `ReactionButton` to avoid compatibility issues with pycord 2.0
* *changed* `ButtonType` has been moved and setting the `linked_to` of a button is now set through the button itself
  * Old: `Button(..., linked_to=ButtonType.NEXT_PAGE)`
  * New: `ReactionButton(..., linked_to=ReactionButton.Type.NEXT_PAGE)`
* *changed* Method `ButtonType.caller_details()` has been renamed and moved to `ReactionButton`
  * Old: `Button(..., details=ButtonType.caller_details())`
  * New: `ReactionButton(..., details=ReactionButton.set_caller_details())`
* *removed* `ReactionMenu` parameters `back_button` and `next_button` have been removed. Use `ReactionMenu.add_button()` instead
* *removed* `ReactionMenu` parameter `config` has been removed/replaced with parameter `menu_type`
* *removed* Attribute `ReactionMenu.run_time`
* *removed* Attribute `ReactionMenu.default_next_button`
* *removed* Attribute `ReactionMenu.default_back_button`
* *removed* Attribute `ReactionMenu.all_buttons`. Use `ReactionMenu.buttons` instead
* *removed* Attribute `ReactionMenu.next_buttons`
* *removed* Attribute `ReactionMenu.back_buttons`
* *removed* Attribute `ReactionMenu.first_page_buttons`
* *removed* Attribute `ReactionMenu.last_page_buttons`
* *removed* Attribute `ReactionMenu.caller_buttons`
* *removed* Attribute `ReactionMenu.end_session_buttons`
* *removed* Attribute `ReactionMenu.go_to_page_buttons`
* *removed* `ReactionMenu.help_appear_order()`
* *removed* `ReactionMenu.change_appear_order()`
* *removed* Exception `SingleUseOnly`
* *changed* `ReactionMenu.clear_all_buttons()` to `ReactionMenu.remove_all_buttons()`
* *changed* `ReactionMenu.all_can_react` is now `ReactionMenu.all_can_click`
* *changed* Parameter `turn_every` in methods `ReactionMenu.set_as_auto_paginator()` and `ReactionMenu.update_turn_every()` are now keyword only arguments
* *changed* A lot of `ReactionMenu` attributes are no longer property getters/setters. They are now normal attributes with type hints
* *changed* The parameter for method `.get_menu_from_message()` is now positional only
* *changed* The following items now return only a `list` instead of `list` or `None` (if no sessions/buttons were found). If no sessions/buttons were found, an empty list is returned
  * `.get_all_dm_sessions()`
  * `.get_all_sessions()`
  * `.get_session()`
  * `.buttons_most_clicked`
  * `.buttons`

Discords Buttons feature has been implemented using pycord. Two classes have been renamed/removed to support `discord.ui.View`
* *removed* `ButtonsMenu` class
  * This has been replaced with `ViewMenu`
* *changed* The `ViewMenu.update()` method arguments are now keyword only
* *removed* `ComponentsButton` class
  * This has been replaced with `ViewButton`
* *changed* All `ComponentsButton` factory methods. They've been renamed and are now apart of the `ViewButton` class
  * Old
    * `ComponentsButton.basic_back()`
    * `ComponentsButton.basic_next()`
  * New
    * `ViewButton.back()`
    * `ViewButton.next()`
* *changed* The emojis attached to each menu have been moved to their own class
  * Old
    * `ReactionMenu.EMOJI_BACK_BUTTON`
    * `ReactionMenu.EMOJI_NEXT_BUTTON`
  * New
    * `ReactionMenu.Emojis.BACK_BUTTON`
    * `ReactionMenu.Emojis.NEXT_BUTTON`
* *changed* `ReactionButton` names are now case sensitive if you were to `get` a button
* *changed* Getting a button with `ReactionMenu` has been replaced by a new method
  * Old: `ReactionMenu.get_button_by_name(name: str)`
  * New: `ReactionMenu.get_button(identity: Union[str, int], *, search_by='name')`. This method now returns only a `list` of buttons instead of either a single button or multiple buttons
* *changed* Setting the `ID_CALLER` information is different now. See the documentation for proper implementation

#### New Features
##### ReactionMenu & ViewMenu
* Added the ability to paginate through multiple pages in a single button press
  * `ReactionButton(..., skip=ReactionButton.Skip(...))`
* Added the ability for relay functions to relay only the buttons of your choice instead of relaying all buttons
  * `ReactionMenu.set_relay(..., only: List[ReactionButton]=None)`
* Added the ability to remove the call to a timeout method if you have one set
  * `ReactionMenu.remove_on_timeout()`
* Added the ability to add multiple pages/buttons to the menu at once
  * `ReactionMenu.add_pages(pages: Sequence[Union[discord.Embed, str]])`
  * `ReactionMenu.add_buttons(buttons: Sequence[ReactionButton])`
* Added parameter `reply` to the `start` method. Enables the menu message to reply to the message that triggered it
  * `ReactionMenu.start(..., reply: bool=False)`
* Added property `ReactionMenu.last_viewed`. Returns the last page that was seen by the user in the pagination process
* Added the ability to use a message ID/message object to add the specified message's content into a menu
  * `ReactionMenu.add_from_ids(messageable: discord.abc.Messageable, message_ids: Sequence[int])`
  * `ReactionMenu.add_from_messages(messages: Sequence[discord.Message])`
* Added the ability to separate embeds and strings
  * `Reactionmenu.separate(values: Sequence[Any])`
* Added the ability to test whether all items in a sequence are of type `discord.Embed` or `str`
  * `ReactionMenu.all_embeds(values: Sequence[Any])`
  * `ReactionMenu.all_strings(values: Sequence[Any])`
* Added the ability to filter all active `ReactionMenu`'s and `ViewMenu`'s into two separate lists
  * `ReactionMenu.split_sessions()`
* Added the ability to stop all `ReactionMenu`'s or `ViewMenu`'s
  * `ReactionMenu.stop_only(session_type: str)`
* Added a method that allows you to set the page director style from a set of pre-defined styles
  * `ReactionMenu.set_page_director_style(style_id: int)`

##### ReactionMenu Only
* Added factory methods for `ReactionButton`
  * `ReactionButton.back()` 
  * `ReactionButton.next()` 
  * `ReactionButton.go_to_first_page()` 
  * `ReactionButton.go_to_last_page()` 
  * `ReactionButton.go_to_page()` 
  * `ReactionButton.end_session()` 
  * `ReactionButton.all()`
  * `ReactionButton.skip(emoji: str, action: str, amount: int)`
* Added attribute `ReactionMenu.remove_extra_emojis`

##### ViewMenu Only
* Added factory methods for `ViewButton`
  * `ViewButton.link(label: str, url: str)`
  * `ViewButton.skip(label: str, action: str, amount: int)`
* Added methods to set all button styles
  * `ViewMenu.randomize_button_styles()`
  * `ViewMenu.set_button_styles(style: discord.ButtonStyle)`
* `ViewButton` now has a `name` attribute
* Added the ability for method `ViewMenu.get_button()` to get buttons by name
  * `ViewMenu.get_button(..., search_by='name')`

##### Miscellaneous
* `ReactionButton` & `ViewButton` attribute `last_clicked` now supports an aware `datetime.datetime`
* The `send_to` parameter in method `.start()` now supports threads
* Method `.set_on_timeout()` now raises `IncorrectType` instead of `MenuException` if the parameter given was not callable
* Method `ReactionMenu.add_button()` now also raises `MenuSettingsMismatch`
* Method `ReactionMenu.refresh_auto_pagination_data()` now raises an error if no data was given in it's parameter
* Added new exceptions. `ViewMenuException` and `MenuException`. All library exceptions can be caught using `MenuException`
* Added function `reactionmenu.version_info()`. Used if submitting a GitHub issue
* Added dunder methods for the library itself and a class
  * `__all__` for `reactionmenu` (`from reactionmenu import *`)
  * `__repr__` for `ViewButton.Followup`

</details>


## Note
For `v1.0.9 - v2.0.4`, the following displays what each acronym represents
* `BM` = `ButtonsMenu`
* `RM` = `ReactionMenu`
* `TM` = `TextMenu`

## v2.0.4 » Jan. 17, 2022
<details>
  <summary>Click to display changelog</summary>

#### Bug Fixes
* `BM` Fixed an issue where multiple link buttons couldn't be used

</details>




## v2.0.3 » Aug. 18, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* `RM|TM` The `Button` class now has similar attributes to `ComponentsButton`
  * `Button.menu`
  * `Button.clicked_by`
  * `Button.total_clicks`
  * `Button.last_clicked`
* `BM|RM|TM` `ReactionMenu.EMOJI_END_SESSION` is now ⏹️ instead of ❌

</details>




## v2.0.2 » Jul. 6, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* `BM` Added the ability to disable or remove a button from the menu when it has been clicked x amount of times

</details>




## v2.0.1 » Jul. 2, 2021
<details>
  <summary>Click to display changelog</summary>

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
  
</details>




## v2.0.0 » Jun. 27, 2021
<details>
  <summary>Click to display changelog</summary>

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

</details>




## v1.0.9 » Jun. 1, 2021
<details>
  <summary>Click to display changelog</summary>

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

</details>




## v1.0.8 » May 4, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* Added `ReactionMenu.delete_on_timeout`

</details>




## v1.0.7 » Mar. 30, 2021
<details>
  <summary>Click to display changelog</summary>

#### Bug Fixes
* Fixed an issue where if a menu's timeout was set to `None` and the `navigation_speed` was set to `ReactionMenu.FAST`, an error would occur

</details>




## v1.0.6 » Mar. 22, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* Added the ability to start a menu in a specific channel

#### Bug Fixes
* Fixed an issue where custom embeds in a dynamic menu would not display all implemented values from that embed

</details>




## v1.0.5 » Mar. 19, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* Added `ReactionMenu` kwarg `navigation_speed`. Used with the below class attributes
  * `ReactionMenu.NORMAL`
  * `ReactionMenu.FAST`
#### Bug Fixes
* Fixed an issue where if multiple menu instances were created and stopped in a single execution, calling `ReactionMenu.stop()` could stop the wrong instance

* Fixed an issue where if an exception was to occur during the startup of a menu, exceptions such as discord.py's "missing permissions" exception would be suppressed and not be displayed 

* Fixed an issue with `Button` objects where a duplicate name/emoji could be used

</details>




## v1.0.4 » Mar. 13, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* Small additional update for `v1.0.3`. Support for `@client.command()` functions to be used with `ButtonType.CALLER`

</details>




## v1.0.3 » Mar. 13, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* Added the ability for buttons to call functions
* Added new `ButtonType` (`ButtonType.CALLER`)
* Added class method `ButtonType.caller_details()`

#### Bug Fixes
* Fixed an issue where all exceptions were suppressed specifically inside the execution method

</details>




## v1.0.2 » Feb. 19, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* Added class method `ReactionMenu.get_sessions_count()`
* Added the option to delete the messages sent when interacting with the menu via `ButtonType.GO_TO_PAGE` (`ReactionMenu` kwarg `delete_interactions`). Repeatedly using `ButtonType.GO_TO_PAGE` can sometimes make the chat look like spam

</details>




## v1.0.1 » Feb. 16, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* Added the ability to limit the amount of active menu sessions
   * `ReactionMenu.set_sessions_limit()`
* Added new `ButtonType` (`ButtonType.GO_TO_PAGE`)
* Added `go_to_page_buttons` property
* Added `total_pages` property
* Added class method `ReactionMenu.cancel_all_sessions()` (**removed since** `v1.0.9`)

</details>
