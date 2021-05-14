![logo](https://cdn.discordapp.com/attachments/655186216060321816/820162226316378162/discord.jpg)
<div align="center">

[![Downloads](https://pepy.tech/badge/reactionmenu)](https://pepy.tech/project/reactionmenu) [![Downloads](https://pepy.tech/badge/reactionmenu/month)](https://pepy.tech/project/reactionmenu) [![Downloads](https://pepy.tech/badge/reactionmenu/week)](https://pepy.tech/project/reactionmenu)
</div>

## Github Updates vs PyPI Updates
The Github version of this package will always have the latest changes, fixes, and additions before the [PyPI](https://pypi.org/project/reactionmenu/) version. You can install the Github version by doing:
```
pip install git+https://github.com/Defxult/reactionmenu.git
```
You must have [Git](https://git-scm.com/) installed in order to do this. With that said, the current README.md documentation represents the Github version of this package. If you are using the PyPI version of this package, it is suggested to read the README.md that matches your PyPI version [here](https://github.com/Defxult/reactionmenu/releases) because documentation may have changed.

* `Github: v1.0.9.dev`
* `PyPI: v1.0.8`

If you are using `v1.0.9.dev` and discover any bugs, please don't hesitate to put them in [issues](https://github.com/Defxult/reactionmenu/issues) so they can be fixed before release 😀

---
## How to install
```
pip install reactionmenu
```
#### Python 3.8 or higher is required
---
## Showcase
![showcase](https://cdn.discordapp.com/attachments/655186216060321816/819885696176226314/showcase.gif)

## How to import
```py
from reactionmenu import ReactionMenu, Button, ButtonType
```

This package comes with several methods and options in order to make a discord reaction menu simple. Once you have imported the proper classes, you will initialize the constructor like so:
```py
menu = ReactionMenu(ctx, back_button='◀️', next_button='▶️', config=ReactionMenu.STATIC) 
```
---
## Parameters of the ReactionMenu constructor
* `ctx` The `discord.ext.commands.Context` object
* `back_button` Emoji used to go to the previous page ([supported emojis](#supported-emojis))
* `next_button` Emoji used to go to the next page ([supported emojis](#supported-emojis))
* `config` The config of the menu is important. You have two options when it comes to configuration. 
    * `ReactionMenu.STATIC` [more info](#reactionmenustatic-vs-reactionmenudynamic)
    * `ReactionMenu.DYNAMIC` [more info](#reactionmenustatic-vs-reactionmenudynamic)
---
## Options of the ReactionMenu constructor [kwargs]
| Name | Type | Default Value | Used for | Info
|------|------|---------------|----------|-------
| `rows_requested` | `int` |`None` | `ReactionMenu.DYNAMIC` | [more info](#dynamic)
| `custom_embed` | `discord.Embed` | `None` | `ReactionMenu.DYNAMIC` | [more info](#dynamic)
| `wrap_in_codeblock` | `str` | `None` | `ReactionMenu.DYNAMIC` | [more info](#dynamic)
| `clear_reactions_after` | `bool` | `True` | `STATIC and DYNAMIC` | delete all reactions after the menu times out
| `timeout` | `float` | `60.0` | `STATIC and DYNAMIC` | timer in seconds for when the menu ends
| `show_page_director` | `bool` | `True` | `STATIC and DYNAMIC` | show/do not show the current page in the embed footer (Page 1/5)
| `name` | `str` | `None` | `STATIC and DYNAMIC` | name of the menu instance
| `style` | `str` | `Page 1/X` | `STATIC and DYNAMIC` | custom page director style
| `all_can_react` | `bool` | `False` | `STATIC and DYNAMIC` | if all members can navigate the menu or only the message author
| `delete_interactions` | `bool` | `True` | `STATIC and DYNAMIC` | delete the bot prompt message and the users message after selecting the page you'd like to go to when using `ButtonType.GO_TO_PAGE`
| `navigation_speed` | `str` | `ReactionMenu.NORMAL` | `STATIC and DYNAMIC` | sets if the user needs to wait for the reaction to be removed by the bot before "turning" the page. Setting the speed to `ReactionMenu.FAST` makes it so that there is no need to wait (reactions are not removed on each press) and can navigate lengthy menu's more quickly
| `delete_on_timeout` | `bool` | `False` | `STATIC and DYNAMIC` | When the menu times out, delete the menu message. This overrides `clear_reactions_after`
| `only_roles` | `List[discord.Role]` | `None` | `STATIC and DYNAMIC` | sets it so that only the members with any of the provided roles can control the menu. The menu owner can always control the menu. This overrides `all_can_react`
> NOTE: All `ReactionMenu` kwargs can also be set using an instance of `ReactionMenu` **except** `rows_requested`
---
## ReactionMenu.STATIC vs ReactionMenu.DYNAMIC
## Static 
A static menu is used when you have a known amount of embed pages you would like to add to the menu
* Associated methods
    * `ReactionMenu.add_page(embed: Embed)`
    * `ReactionMenu.remove_page(page_number: int)`
    * `ReactionMenu.clear_all_pages()`
    * `ReactionMenu.clear_all_custom_pages()`

##### Adding Pages
```py
menu = ReactionMenu(ctx, back_button='◀️', next_button='▶️', config=ReactionMenu.STATIC)
menu.add_page(greeting_embed)
menu.add_page(goodbye_embed)

# NOTE: it can also be used in a loop
member_details = [] # contains embed objects
for member_embed in member_details:
    menu.add_page(member_embed)
```
##### Deleting Pages
You can delete a single page using `menu.remove_page()` or all pages with `menu.clear_all_pages()`. If you have any custom embed pages ( [more on that below](#all-buttontypes) ), you can delete them all with `menu.clear_all_custom_pages()`

## Dynamic
A dynamic menu is used when you do not know how much information will be applied to the menu. For example, if you were to request information from a database, that information can always change. You query something and you might get 1,500 results back, and the next maybe only 800. A dynamic menu pieces all this information together for you and adds it to an embed page by rows of data. `.add_row()` is best used in some sort of `Iterable` where everything can be looped through, but only add the amount of data you want to the menu page.
> NOTE: In a dynamic menu, all added data is placed in the description section of an embed. If you choose to use a `custom_embed`, all text in the description will be overriden with the data you add
* Associated methods
    * `ReactionMenu.add_row(data: str)`
    * `ReactionMenu.clear_all_row_data()`
    * `ReactionMenu.set_main_pages(*embeds: Embed)`
    * `ReactionMenu.set_last_pages(*embeds: Embed)`
* The kwargs specifically made for a dynamic menu are:
    * `rows_requested` - The amount of rows you would like on each embed page before making a new page
        * `ReactionMenu(ctx, ..., rows_requested=5)`
    * `custom_embed` - An embed you have created to use as the embed pages. Used for your menu aesthetic
        * `ReactionMenu(ctx, ..., custom_embed=red_embed)`
    * `wrap_in_codeblock` - The language identifier when wrapping your data in a discord codeblock. 
        * `ReactionMenu(ctx, ..., wrap_in_codeblock='py')`

##### Adding Rows/data
```py
menu = ReactionMenu(ctx, back_button='◀️', next_button='▶️', config=ReactionMenu.DYNAMIC, rows_requested=2)

for my_data in database.request('SELECT * FROM customers'):
    menu.add_row(my_data)

# NOTE: you can also add rows manually 
menu.add_row('Have a')
menu.add_row('great')
menu.add_row('day!')
```
##### Deleting Data
You can remove all the data you've added to a menu by using `menu.clear_all_row_data()`

##### Main/Last Pages
When using a dynamic menu, the only embed pages you see are from the data you've added. But if you would like to show more pages other than just the data, you can use methods `.set_main_pages` and `.set_last_pages`. Setting the main page(s), the embeds you set will be the first embeds that are shown when the menu starts. Setting the last page(s) are the last embeds shown
```py
menu.set_main_pages(welcome_embed, announcement_embed)

for data in get_information():
    menu.add_row(data)

menu.set_last_pages(additonal_info_embed)
# NOTE: setting main/last pages can be set in any order
```
---
## Supported Emojis
In a menu, the places you use emojis are either in the `ReactionMenu`/`TextMenu` constructors with `back_button` and `next_button`. As well as the emoji parameter of `Button`. The format you use can vary:

```py
Button(emoji='😄' , ...)
Button(emoji='<:miscTwitter:705423192818450453>', ...)
Button(emoji='\U000027a1', ...)
Button(emoji='\N{winking face}', ...)
```
> NOTE: These formats are applicable to the `ReactionMenu`/`TextMenu` back and next buttons

Each menu class provides a set of basic emojis (class attributes) to use as your `back_button` and `next_button` for your convenience. As well as additional emojis to use for a `Button`
```py
menu = ReactionMenu(ctx, back_button=ReactionMenu.EMOJI_BACK_BUTTON, next_button=ReactionMenu.EMOJI_NEXT_BUTTON, ...)
```

* ▶️ as `ReactionMenu.EMOJI_NEXT_BUTTON`
* ◀️ as `ReactionMenu.EMOJI_BACK_BUTTON`
* ⏪ as `ReactionMenu.EMOJI_FIRST_PAGE `
* ⏩ as `ReactionMenu.EMOJI_LAST_PAGE`
* 🔢 as `ReactionMenu.EMOJI_GO_TO_PAGE`
* ❌ as `ReactionMenu.EMOJI_END_SESSION`
---
## What are Buttons and ButtonTypes?
Buttons/button types are used when you want to add a reaction to the menu that does a certain function. Buttons and button types work together to achieve the desired action.

##### Parameters of the Button constructor
* `emoji` The emoji you would like to use as the reaction
* `linked_to` When the reaction is clicked, this is what determines what it will do (`ButtonType`)

##### Options of the Button constructor [kwargs]
| Name | Type | Default Value | Used for
|------|------|---------------|----------
| `name` | `str` |`None` | The name of the button object
| `embed` | `discord.Embed` | `None` | When the reaction is pressed, go to the specifed embed. 
| `details` | [more info](#buttons-with-buttontypecaller) | `None` | Assigns the function and it's arguments to call when a `Button` with `ButtonType.CALLER` is pressed

> NOTE: All `Button` kwargs can also be set using an instance of `Button`

* Associated methods
    * `ReactionMenu.add_button(button: Button)`
    * `ReactionMenu.clear_all_buttons()`
    * `ReactionMenu.remove_button(identity: Union[str, Button])`
    * `ReactionMenu.change_appear_order(*emoji_or_button: Union[str, Button])`
    * `ReactionMenu.get_button_by_name(name: str)`
    * `ReactionMenu.help_appear_order()`
    * `ButtonType.caller_details(func, *args, **kwargs)`

##### All ButtonTypes
| Type | Info |
|-------|------|
| `ButtonType.NEXT_PAGE` | Go to the next page in the menu session
| `ButtonType.PREVIOUS_PAGE` | Go to the previous page in the menu session
| `ButtonType.GO_TO_FIRST_PAGE` | Go to the first page in the menu session
| `ButtonType.GO_TO_LAST_PAGE` | Go to the last page in the menu session
| `ButtonType.GO_TO_PAGE` | Prompts you to type in the page you'd like to go to
| `ButtonType.END_SESSION` | Terminates the session and deletes the menu message. This is not like `ReactionMenu.stop()`
| `ButtonType.CUSTOM_EMBED` | Used separately from the navigation buttons. Once clicked, go to the specified embed 
| `ButtonType.CALLER` | Used when specifying the function to call and it's arguments when the button is pressed ( [more info](#buttons-with-buttontypecaller) )

##### Adding Buttons
You can add buttons (reactions) to the menu using a `Button`. By default, two buttons have already been set in the `ReactionMenu` constructor. The `back_button` as `ButtonType.PREVIOUS_PAGE` and `next_button` as `ButtonType.NEXT_PAGE`. It's up to you if you would like additional buttons. Below are examples on how to implement each `ButtonType`. 
> NOTE: Buttons with `ButtonType.CALLER` are a little different, so there is a dedicated section explaining how they work and how to implement them [here](#buttons-with-buttontypecaller)


```py
menu = ReactionMenu(...)

# first and last pages
fpb = Button(emoji='⏪', linked_to=ButtonType.GO_TO_FIRST_PAGE)
lpb = Button(emoji='⏩', linked_to=ButtonType.GO_TO_LAST_PAGE)

# go to page
gtpb = Button(emoji='🔢', linked_to=ButtonType.GO_TO_PAGE)

# end session
esb = Button(emoji='❌', linked_to=ButtonType.END_SESSION)

# custom embed
ceb = Button(emoji='😎', linked_to=ButtonType.CUSTOM_EMBED, embed=discord.Embed(title='Hello'))

menu.add_button(fpb)
menu.add_button(lpb)
menu.add_button(gtpb)
menu.add_button(esb)
menu.add_button(ceb)
```
##### Deleting Buttons
Remove all buttons with `menu.clear_all_buttons()`. You can also remove an individual button using its name if you have it set, or the button object itself with `menu.remove_button()`

##### Buttons with ButtonType.CALLER
`ButtonType.CALLER` buttons are used to implement your own functionality into the menu. Maybe you want to add a button that creates a text channel, sends a message, or add something to a database, whatever it may be. In order to work with `ButtonType.CALLER`, use the class method below.

* `ButtonType.caller_details(func, *args, **kwargs)`
  
This class method is used to setup a function and it's arguments that are later called when the button is pressed. The `Button` constructor has the kwarg `details`, and that's what you'll use with `.caller_details` to assign the values needed. Some examples are below on how to properly implement `ButtonType.CALLER`

```py
@client.command()
async def user(ctx, name, *, message):
    await ctx.send(f"Hi {name}! {message}. We're glad you're here!")

def car(year, make, model):
    print(f"I have a {year} {make} {model}")

ub = Button(emoji='👋', linked_to=ButtonType.CALLER, details=ButtonType.caller_details(user, ctx, 'Defxult', message='Welcome to the server'))
cb = Button(emoji='🚗', linked_to=ButtonType.CALLER, details=ButtonType.caller_details(car, 2021, 'Ford', 'Mustang'))
```
> NOTE: The function you pass in should not return anything. Calling functions with `ButtonType.CALLER` does not store or handle anything returned by that function

---

##### Emoji Order
It is possible to change the order the reactions appear in on the menu.
```py
first_button = Button(emoji='⏪', linked_to=ButtonType.GO_TO_FIRST_PAGE)
close_menu_button = Button(emoji='❌', linked_to=ButtonType.END_SESSION, name='end')

# NOTE 1: When changing the order, you need to include the default back and next buttons because they are there by default. Access the default back/next buttons with menu attributes
# NOTE 2: You can use the emoji or button object 

menu.change_appear_order(first_button, menu.default_back_button, close_menu_button, menu.default_next_button)
```
If you did not make an instance of a Button object to access, you can still get that button object by its name if it is set and has been added to the menu via `menu.add_button()`. Example: `menu.get_button_by_name('end')`. With the helper function `menu.help_appear_order()`, it simply prints out all active buttons to the console so you can copy and paste each emoji in the order you'd like.

---
## Auto-pagination

An auto-pagination menu is a menu that doesn't need a reaction press to go to the next page. It turns pages on it's own every x amount of seconds. This can be useful if you'd like to have a continuous display of information to your server. That information might be server stats, upcoming events, etc. Below is an example of an auto-pagination menu.

![auto-pagin-showcase](https://cdn.discordapp.com/attachments/655186216060321816/842352164713791508/auto-pagin-reduced.gif)

* Associated methods
  * `ReactionMenu.set_as_auto_paginator(turn_every: Union[int, float])`
  * `ReactionMenu.update_turn_every(turn_every: Union[int, float])`
  * `ReactionMenu.refresh_auto_pagination_data(*embeds: Embed)`
  * `ReactionMenu.update_all_turn_every(turn_every: Union[int, float])` (class method)
  * `ReactionMenu.stop_all_auto_sessions()` (class method)
  * `ReactionMenu.auto_turn_every` (property)
  * `ReactionMenu.auto_paginator` (property)

> NOTE: When you only want to create a auto-pagination menu, there's no need to set the `back_button` or `next_button` with an emoji. Simply set them to `None`

Example:
```py
menu = ReactionMenu(ctx, back_button=None, next_button=None, config=ReactionMenu.STATIC)

menu.add_page(server_info_embed)
menu.add_page(social_media_embed)
menu.add_page(games_embed)

menu.set_as_auto_paginator(turn_every=120)
await menu.start()
```
---
## Setting Limits
If you'd like, you can limit the amount of reaction menus that can be active at the same time. You can do this by using the class method above. 
* Associated CLASS Methods
    * `ReactionMenu.set_sessions_limit(limit: int, message: str)` 
    * `ReactionMenu.get_sessions_count()`
    * `await ReactionMenu.stop_all_sessions()`

Example:
```py
from discord.ext import commands
from reactionmenu import ReactionMenu, Button, ButtonType

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
	ReactionMenu.set_sessions_limit(3, 'Sessions are limited')
```

With the above example, only 3 menus can be active at once, and if someone tries to create more before other menus are finished, they will get an error message saying "Sessions are limited".

If you have an excess amount of menu's running, it is possible to stop all sessions. Example:
```py
@commands.command()
@commands.has_role('Admin')
async def stop(self, ctx):
    await ReactionMenu.stop_all_sessions()
```
---
## Starting/Stopping the ReactionMenu
* Associated Methods
    * `await ReactionMenu.start(*, send_to=None)`
    * `await ReactionMenu.stop(*, delete_menu_message=False, clear_reactions=False)`

When starting the menu, you have the option to send the menu to a certain channel. Parameter `send_to` is the channel you'd like to send the menu to. You can set `send_to` as the channel name (`str`), channel ID (`int`), or channel object (`discord.TextChannel`). Example:
```py
menu = ReactionMenu(...)
# channel name
await menu.start(send_to='bot-commands')

# channel ID
await menu.start(send_to=1234567890123456)

# channel object
channel = guild.get_channel(1234567890123456)
await menu.start(send_to=channel)
```

When stopping the menu, you have two options. Delete the reaction menu by setting the first parameter to `True` or only remove all it's reactions, setting the second parameter to `True`

---
## All attributes for ReactionMenu
<details>
    <summary>Click to show all attributes</summary>

| Attribute | Return Type | Info 
|-----------|-------------|----------
| `ReactionMenu.STATIC` | `int` | menu config value (class attribute)
| `ReactionMenu.DYNAMIC` | `int` | menu config value (class attribute)  
| `ReactionMenu.NORMAL` | `str` | menu kwarg value (class attribute)
| `ReactionMenu.FAST` | `str` | menu kwarg value (class attribute)
| `ReactionMenu.EMOJI_NEXT_BUTTON` | `str` | basic next button emoji (class attribute)
| `ReactionMenu.EMOJI_BACK_BUTTON` | `str` | basic back button emoji (class attribute)
| `ReactionMenu.EMOJI_FIRST_PAGE` | `str` | basic first page button emoji (class attribute)
| `ReactionMenu.EMOJI_LAST_PAGE` | `str` | basic last page button emoji (class attribute)
| `ReactionMenu.EMOJI_GO_TO_PAGE` | `str` | basic go-to-page button emoji (class attribute)
| `ReactionMenu.EMOJI_END_SESSION` | `str` | basic end session button emoji (class attribute)
| `ReactionMenu.config` | `int` | menu config value (`STATIC` or `DYNAMIC`)
| `ReactionMenu.is_running` | `bool` | if the menu is currently active
| `ReactionMenu.default_next_button` | `Button` | default next button (in the `ReactionMenu` constructor)
| `ReactionMenu.default_back_button` | `Button` | default back button (in the `ReactionMenu` constructor)
| `ReactionMenu.next_buttons` | `List[Button]` | all active `ButtonType.NEXT_PAGE` buttons
| `ReactionMenu.back_buttons` | `List[Button]` | all active `ButtonType.PREVIOUS_PAGE` buttons
| `ReactionMenu.first_page_buttons` | `List[Button]` | all active `ButtonType.GO_TO_FIRST_PAGE` buttons
| `ReactionMenu.last_page_buttons` | `List[Button]` | all active `ButtonType.GO_TO_LAST_PAGE` buttons
| `ReactionMenu.end_session_buttons` | `List[Button]` | all active `ButtonType.END_SESSION` buttons
| `ReactionMenu.custom_embed_buttons` | `List[Button]` | all active `ButtonType.CUSTOM_EMBED` buttons
| `ReactionMenu.go_to_page_buttons` | `List[Button]` | all active `ButtonType.GO_TO_PAGE` buttons
| `ReactionMenu.caller_buttons` | `List[Button]` | all active `ButtonType.CALLER` buttons
| `ReactionMenu.all_buttons` | `List[Button]` | all active buttons
| `ReactionMenu.rows_requested` | `int` | the amount of rows you have set to request
| `ReactionMenu.timeout` | `float` | value in seconds of when the menu ends
| `ReactionMenu.show_page_director` | `bool` | show/do not show the current page on the embed
| `ReactionMenu.name` | `str` | name of the menu instance
| `ReactionMenu.style` | `str` | custom page director style
| `ReactionMenu.all_can_react` | `bool`  | if all members can navigate the menu or only the message author
| `ReactionMenu.custom_embed` | `discord.Embed` | embed object used for custom pages
| `ReactionMenu.wrap_in_codeblock` | `str` | language identifier when wrapping your data in a discord codeblock
| `ReactionMenu.total_pages` | `int` | total amount of built pages
| `ReactionMenu.delete_interactions` | `bool` | delete the bot prompt message and the users message after selecting the page you'd like to go to when using `ButtonType.GO_TO_PAGE`
| `ReactionMenu.navigation_speed` | `str` | the current setting for the menu navigation speed
| `ReactionMenu.delete_on_timeout` | `bool` | if the menu message will delete upon timeout
| `ReactionMenu.only_roles` | `List[discord.Role]` | the members with those role are the only ones allowed to control the menu. the menu owner can always control the menu
| `ReactionMenu.run_time` | `int` | the amount of time in seconds the menu has been active
| `ReactionMenu.auto_turn_every` | `int` | how frequently an auto-pagination menu should change the page
</details>

## All methods for ReactionMenu
<details>
    <summary>Click to show all methods</summary>

* `ReactionMenu.add_button(button: Button)`
  * Adds a button to the menu. Buttons can also be linked to custom embeds. So when you click the emoji you've assigned, it goes to that page and is seperate from the normal menu
---
* `ReactionMenu.add_page(embed: Embed)`
  * On a static menu, add a page
---
* `ReactionMenu.add_row(data: str)`
  * Used when the menu is set to dynamic. Apply the data recieved to a row in the embed page
---
* `ReactionMenu.change_appear_order(*emoji_or_button: Union[str, Button])`
  * Change the order of the reactions you want them to appear in on the menu
---
* `ReactionMenu.clear_all_buttons()`
  * Delete all buttons that have been added
---
* `ReactionMenu.clear_all_custom_pages()`
  * On a static menu, delete all custom pages that have been added
---
* `ReactionMenu.clear_all_pages()`
  * On a static menu, delete all pages that have been added
---
* `ReactionMenu.clear_all_row_data()`
  * Delete all the data thats been added using `ReactionMenu.add_row()`
---
* `ReactionMenu.get_button_by_name(name: str) -> Button`
  * Retrieve a `Button` object by its name if the kwarg "name" for that `Button` was set
---
* `ReactionMenu.get_sessions_count() -> int`
  * *class method* Returns the number of active sessions
---
* `ReactionMenu.help_appear_order()`
  * Prints all button emojis you've added before this method was called to the console for easy copy and pasting of the desired order. Note: If using Visual Studio Code, if you see a question mark as the emoji, you need to resize the console in order for it to show up.
---
* `ReactionMenu.refresh_auto_pagination_data(*embeds: Embed)`
  * Update the embeds displayed in the auto-pagination menu
---
* `ReactionMenu.remove_button(identity: Union[str, Button])`
  * Remove a button by its name or its object
---
* `ReactionMenu.remove_page(page_number: int)`
  * On a static menu, delete a certain page that has been added
---
* `ReactionMenu.set_as_auto_paginator(turn_every: Union[int, float])`
  * Set the menu to turn pages on it's own every x seconds. If this is set, reactions will not be applied to the menu
---
* `ReactionMenu.set_last_pages(*embeds: Embed)`
  * On a dynamic menu, set the pages you would like to show last. These embeds will be shown after the embeds that contain your data
---
* `ReactionMenu.set_main_pages(*embeds: Embed)`
  * On a dynamic menu, set the pages you would like to show first. These embeds will be shown before the embeds that contain your data
---
* `ReactionMenu.set_sessions_limit(limit: int, message='Too many active reaction menus. Wait for other menus to be finished.')`
  * *class method* Sets the amount of menu sessions that can be concurrently active. Should be set before any menus are started and cannot be called more than once
---
* `await ReactionMenu.start(*, send_to=None)`
  * Starts the reaction menu
---
* `await ReactionMenu.stop(*, delete_menu_message=False, clear_reactions=False)`
  * Stops the process of the reaction menu with the option of deleting the menu's message or clearing reactions upon stop
---
* `await ReactionMenu.stop_all_auto_sessions()`
  * *class method* Stops all auto-paginated sessions that are currently running
---
* `await ReactionMenu.stop_all_sessions()`
  * *class method* Gracefully stops all sessions that are currently running
---
* `await ReactionMenu.stop_session(name: str)`
  * *class method* Stop a specific menu by it's name
---
* `ReactionMenu.update_all_turn_every(turn_every: Union[int, float])`
  * *class method* Update the amount of seconds to wait before going to the next page for all active auto-paginated sessions. When updated, the new value doesn't go into effect until the last round of waiting (`turn_every`) completes for each menu
---
* `ReactionMenu.update_turn_every(turn_every: Union[int, float])`
  * Change the amount of seconds to wait before going to the next page. When updated, the new value doesn't go into effect until the last round of waiting (`turn_every`) completes

</details>

---
---
## TextMenu
A `TextMenu` is a text based version of `ReactionMenu`. No embeds are involved in the pagination process, only plain text is used. Has limited capabilites compared to `ReactionMenu`. One of the limitations of a `TextMenu` is the `ButtonType` that can be used when adding a `Button`. `ButtonType.CUSTOM_EMBED` is not valid for a `TextMenu`
```py
txt = TextMenu(ctx, back_button='◀️', next_button='▶️') 
```

## Showcase
![showcase-text](https://cdn.discordapp.com/attachments/655186216060321816/840161666108620800/text_showcase.gif)

## How to import
```py
from reactionmenu import TextMenu
```

---
## Parameters of the TextMenu constructor
* `ctx` The `discord.ext.commands.Context` object
* `back_button` Emoji used to go to the previous page ([supported emojis](#supported-emojis))
* `next_button` Emoji used to go to the next page ([supported emojis](#supported-emojis))
---

## Options of the TextMenu constructor [kwargs]
The kwargs for `TextMenu` are the same as [ReactionMenu kwargs](#options-of-the-reactionmenu-constructor-kwargs) **except**:
* `rows_requested`
* `custom_embed`
* `wrap_in_codeblock`

Those kwargs are **NOT** valid for a `TextMenu`

---
## TextMenu Specifics
##### Methods
There are only a few methods that are specifc to a `TextMenu`
* `TextMenu.add_content(content: str)`
  * This is similiar to adding a page to a `ReactionMenu`, but each addition is text
* `TextMenu.clear_all_contents()`
  * Delete everything that has been added to the list of contents

In addition to those methods, `TextMenu` also has the same methods as [ReactionMenu methods](#all-methods-for-reactionmenu) **except**:
* `clear_all_row_data()`
* `add_row()`
* `remove_page()`
* `set_main_pages()`
* `set_last_pages()`
* `clear_all_pages()`
* `clear_all_custom_pages()`
* `add_page()`

Those methods are **NOT** valid for a `TextMenu`

##### Attributes
* `TextMenu.contents` (`List[str]`)

`TextMenu` has the same attributes as [ReactionMenu attributes](#all-attributes-for-reactionmenu) **except**:

* `STATIC`
* `DYNAMIC`
* `config`
* `custom_embed_buttons`
* `custom_embed`
* `wrap_in_codeblock`

Those attributes are **NOT** valid for a `TextMenu`

---
## Starting/Stopping the TextMenu

Starting/stopping the menu is the same as `ReactionMenu`. See the [Starting/Stopping the ReactionMenu](#startingstopping-the-reactionmenu) documentation. Of course you will need to use an instance of `TextMenu` instead.

