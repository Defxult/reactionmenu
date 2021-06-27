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

* `Github: v2.0.1.dev`
* `PyPI: v2.0.0`

---
## Now featuring Buttons! 
![buttons_row](https://cdn.discordapp.com/attachments/655186216060321816/855045265793744916/unknown.png)

Click [here](#buttonsmenu) to go to the `ButtonsMenu` documentation

## How to install
```
pip install reactionmenu
```
#### Python 3.8 or higher is required
---
## Showcase
![showcase](https://cdn.discordapp.com/attachments/655186216060321816/819885696176226314/showcase.gif)
---
## Index
<details>
  <summary>Click to show index</summary>

* [ReactionMenu](#how-to-import)
  * [How to Import](#how-to-import)
  * [Parameters of the ReactionMenu constructor](#parameters-of-the-reactionmenu-constructor)
  * [Options of the ReactionMenu constructor (kwargs)](#options-of-the-reactionmenu-constructor-kwargs)
  * [ReactionMenu.STATIC vs ReactionMenu.DYNAMIC](#reactionmenustatic-vs-reactionmenudynamic)
    * [Static](#static)
    * [Adding Pages](#adding-pages)
    * [Deleting Pages](#deleting-pages)
    * [Dynamic](#dynamic)
    * [Adding Rows/data](#adding-rowsdata)
    * [Deleting Data](#deleting-data)
    * [Main/Last Pages](#mainlast-pages)
  * [Supported Emojis](#supported-emojis)
  * [What are Buttons and ButtonTypes?](#what-are-buttons-and-buttontypes)
    * [Parameters of the Button constructor](#parameters-of-the-button-constructor)
    * [Options of the Button constructor (kwargs)](#options-of-the-button-constructor-kwargs)
    * [All ButtonTypes](#all-buttontypes)
    * [Adding Buttons](#adding-buttons)
    * [Deleting Buttons](#deleting-buttons)
    * [Buttons with ButtonType.CALLER](#buttons-with-buttontypecaller)
    * [Emoji Order](#emoji-order)
  * [Auto-pagination](#auto-pagination)
  * [Relays](#relays)
  * [Setting Limits](#setting-limits)
  * [Starting/Stopping the ReactionMenu](#startingstopping-the-reactionmenu)
  * [All attributes for ReactionMenu](#all-attributes-for-reactionmenu)
  * [All methods for ReactionMenu](#all-methods-for-reactionmenu)

* [TextMenu](#textmenu)
  * [How to import](#how-to-import-1)
  * [Parameters of the TextMenu constructor](#parameters-of-the-textmenu-constructor)
  * [TextMenu Specifics](#textmenu-specifics)
  * [Starting/Stopping the TextMenu](#startingstopping-the-textmenu)

* [ButtonsMenu](#buttonsmenu)
  * [How to import](#how-to-import-2)
  * [Initial setup](#initial-setup)
  * [Parameters of the ButtonsMenu constructor](#parameters-of-the-buttonsmenu-constructor)
  * [Options of of ButtonsMenu constructor (kwargs)](#options-of-the-buttonsmenu-constructor-kwargs)
  * [Pages for ButtonsMenu](#pages-for-buttonmenu)
    * [Adding Pages](#adding-pages-1)
  * [Buttons for ButtonsMenu](#buttons-for-buttonsmenu)
  * [ComponentsButton](#componentsbutton)
  * [Parameters of the ComponentsButton constructor](#parameters-of-the-componentsbutton-constructor)
  * [Attributes for ComponentsButton](#attributes-for-componentsbutton)
  * [Adding a ComponentsButton](#adding-a-componentsbutton)
  * [Updating ComponentsButton and Pages](#updating-componentsbutton-and-pages)
    * [Updating a Button](#updating-a-button)
    * [Updating Pages and Buttons](#updating-pages-and-buttons)
  * [Starting/Stopping the ButtonsMenu](#startingstopping-the-buttonsmenu)
  * [All attributes for ButtonsMenu](#all-attributes-for-buttonsmenu)
  * [All methods for ButtonsMenu](#all-methods-for-buttonsmenu)
</details>

---

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
* `back_button` (`str`) Emoji used to go to the previous page ([supported emojis](#supported-emojis))
* `next_button` (`str`) Emoji used to go to the next page ([supported emojis](#supported-emojis))
* `config` (`int`) The config of the menu is important. You have two options when it comes to configuration. 
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
| `style` | `str` | `Page 1/X` | `STATIC and DYNAMIC` | custom page director style. Character "$" represents the current page, and "&" represents the total amount of pages. So the default style is `ReactionMenu(..., style='Page $/&')`
| `all_can_react` | `bool` | `False` | `STATIC and DYNAMIC` | if all members can navigate the menu or only the message author
| `delete_interactions` | `bool` | `True` | `STATIC and DYNAMIC` | delete the bot prompt message and the users message after selecting the page you'd like to go to when using `ButtonType.GO_TO_PAGE`
| `navigation_speed` | `str` | `ReactionMenu.NORMAL` | `STATIC and DYNAMIC` | sets if the user needs to wait for the reaction to be removed by the bot before "turning" the page. Setting the speed to `ReactionMenu.FAST` makes it so that there is no need to wait (reactions are not removed on each press) and can navigate lengthy menu's more quickly
| `delete_on_timeout` | `bool` | `False` | `STATIC and DYNAMIC` | when the menu times out, delete the menu message. This overrides `clear_reactions_after`
| `only_roles` | `List[discord.Role]` | `None` | `STATIC and DYNAMIC` | sets it so that only the members with any of the provided roles can control the menu. The menu owner can always control the menu. This overrides `all_can_react`
> **NOTE:** All `ReactionMenu` kwargs can also be set using an instance of `ReactionMenu` **except** `rows_requested`
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
> **NOTE:** In a dynamic menu, all added data is placed in the description section of an embed. If you choose to use a `custom_embed`, all text in the description will be overridden with the data you add
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
> **NOTE:** These formats are applicable to the `ReactionMenu`/`TextMenu` back and next buttons

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
* `emoji` (`str`) The emoji you would like to use as the reaction
* `linked_to` (`ButtonType`) When the reaction is clicked, this is what determines what it will do

##### Options of the Button constructor [kwargs]
| Name | Type | Default Value | Used for
|------|------|---------------|----------
| `name` | `str` |`None` | The name of the button object
| `embed` | `discord.Embed` | `None` | When the reaction is pressed, go to the specifed embed. 
| `details` | [more info](#buttons-with-buttontypecaller) | `None` | Assigns the function and it's arguments to call when a `Button` with `ButtonType.CALLER` is pressed

> **NOTE:** All `Button` kwargs can also be set using an instance of `Button`

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
| `ButtonType.END_SESSION` | Stops the session and deletes the menu message
| `ButtonType.CUSTOM_EMBED` | Used separately from the navigation buttons. Once clicked, go to the specified embed 
| `ButtonType.CALLER` | Used when specifying the function to call and it's arguments when the button is pressed ( [more info](#buttons-with-buttontypecaller) )

##### Adding Buttons
You can add buttons (reactions) to the menu using a `Button`. By default, two buttons have already been set in the `ReactionMenu` constructor. The `back_button` as `ButtonType.PREVIOUS_PAGE` and `next_button` as `ButtonType.NEXT_PAGE`. It's up to you if you would like additional buttons. Below are examples on how to implement each `ButtonType`. 
> **NOTE:** Buttons with `ButtonType.CALLER` are a little different, so there is a dedicated section explaining how they work and how to implement them [here](#buttons-with-buttontypecaller)


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
@bot.command()
async def user(ctx, name, *, message):
    await ctx.send(f"Hi {name}! {message}. We're glad you're here!")

def car(year, make, model):
    print(f"I have a {year} {make} {model}")

ub = Button(emoji='👋', linked_to=ButtonType.CALLER, details=ButtonType.caller_details(user, ctx, 'Defxult', message='Welcome to the server'))
cb = Button(emoji='🚗', linked_to=ButtonType.CALLER, details=ButtonType.caller_details(car, 2021, 'Ford', 'Mustang'))
```
> **NOTE:** The function you pass in should not return anything. Calling functions with `ButtonType.CALLER` does not store or handle anything returned by that function

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
  * `await ReactionMenu.stop_all_auto_sessions()` (class method)
  * `ReactionMenu.auto_turn_every` (property)
  * `ReactionMenu.auto_paginator` (property)

> **NOTE:** When you only want to create a auto-pagination menu, there's no need to set the `back_button` or `next_button` with an emoji. Simply set them to `None`

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
## Relays
Menu relays are functions that are called anytime a reaction that is apart of a menu is pressed. It is considered as an extension of a `Button` with `ButtonType.CALLER`. Unlike `ButtonType.CALLER` which provides no details about the interactions on the menu, relays do.
* Associated method
  * `ReactionMenu.set_relay(Callable[[NamedTuple], None])`

When creating a function for your relay, that function must contain a single positional argument. When a reaction is pressed, a `RelayPayload` object (a named tuple) is passed to that function. The attributes of `RelayPayload` are:
* member (`discord.Member`) The person who pressed the reaction
* button (`Button`) The [button](#what-are-buttons-and-buttontypes) that was pressed
* time (`datetime`) What time in UTC for when the reaction was pressed
* menu (`ReactionMenu`) The menu object

Example:
```py
async def vote_relay(payload):
    register_vote(payload.member.name, payload.time)
    channel = payload.menu.message.channel
    await channel.send(f'{payload.member.mention}, thanks for voting!', delete_after=1)

menu = ReactionMenu(ctx, ...)
menu.set_relay(vote_relay)
```
> **NOTE:** The relay function should not return anything because nothing is stored or handled from a return

---
## Setting Limits
If you'd like, you can limit the amount of reaction menus that can be active at the same time *per* "guild", "member", or "channel" 
* Associated CLASS Methods
    * `ReactionMenu.set_sessions_limit(limit: int, per='guild', message='Too many active reaction menus. Wait for other menus to be finished.')` 
    * `ReactionMenu.remove_limit()`
    * `ReactionMenu.get_sessions_count()`
    * `await ReactionMenu.stop_all_sessions()`

Example:
```py
from discord.ext import commands
from reactionmenu import ReactionMenu, Button, ButtonType

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
	ReactionMenu.set_sessions_limit(3, per='member', message='Sessions are limited to 3 per member')
```

With the above example, only 3 menus can be active at once for each member, and if they try to create more before their other menu's are finished, they will get an error message saying "Sessions are limited to 3 per member".

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
> **NOTE:** `send_to` is not valid if a menu was started in DM's

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
| `ReactionMenu.message` | `discord.Message` | the message object the menu is operating from
| `ReactionMenu.owner` | `discord.Member` | the person who started the menu
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
* `ReactionMenu.get_all_dm_sessions() -> list`
  * *class method* Returns all active DM menu sessions
---
* `ReactionMenu.get_all_sessions()`
  * *class method* Returns all active menu sessions
---
* `ReactionMenu.get_button_by_name(name: str)`
  * Retrieve a `Button` object by its name if the kwarg "name" for that `Button` was set
---
* `ReactionMenu.get_menu_from_message(message_id: int)`
  * *class method* Return the menu object associated with the message with the given ID
---
* `ReactionMenu.get_session(name: str)`
  * *class method* Return a menu instance by it's name. Can return a `list` of menu instances if multiple instances of the menu with the supplied name are running. Can also return `None` if the menu with the supplied name was not found in the list of active sessions
---
* `ReactionMenu.get_sessions_count()`
  * *class method* Returns the number of active sessions
---
* `ReactionMenu.help_appear_order()`
  * Prints all button emojis you've added before this method was called to the console for easy copy and pasting of the desired order. Note: If using Visual Studio Code, if you see a question mark as the emoji, you need to resize the console in order for it to show up.
---
* `ReactionMenu.refresh_auto_pagination_data(*embeds: Embed)`
  * Update the embeds displayed in the auto-pagination menu. When refreshed, the new embeds don't go into effect until the last round of waiting (what you set for `turn_every`) completes
---
* `ReactionMenu.remove_button(identity: Union[str, Button])`
  * Remove a button by its name or its object
---
* `ReactionMenu.remove_limit()`
  * *class method* Remove the limits currently set for reaction menu's
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
* `ReactionMenu.set_on_timeout(func: object)`
  * Set the function to be called when the menu times out
---
* `ReactionMenu.set_relay(func)`
  * Set a function to be called with a given set of information when a reaction is pressed on the menu
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
* `await ReactionMenu.stop_session(name: str, include_all=False)`
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
from reactionmenu import TextMenu, Button, ButtonType
```

---
## Parameters of the TextMenu constructor
* `ctx` The `discord.ext.commands.Context` object
* `back_button` (`str`) Emoji used to go to the previous page ([supported emojis](#supported-emojis))
* `next_button` (`str`) Emoji used to go to the next page ([supported emojis](#supported-emojis))
---

## Options of the TextMenu constructor [kwargs]
The kwargs for `TextMenu` are the same as [ReactionMenu kwargs](#options-of-the-reactionmenu-constructor-kwargs) **except**:
* `rows_requested`
* `custom_embed`
* `wrap_in_codeblock`

Those kwargs are **NOT** valid for a `TextMenu`

---
## TextMenu Specifics
##### Constructor kwargs
* `allowed_mentions` (`discord.AllowedMentions`)

##### Methods
There are only a few methods that are specific to a `TextMenu`
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
* `TextMenu.allowed_mentions` (`discord.AllowedMentions`)

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

---
---
## ButtonsMenu
A `ButtonsMenu` is just like a reacton menu except it uses discords new Buttons feature. With buttons, you can enable and disable them, set a certain color for them with emojis, have buttons that send hidden messages, and add hyperlinks. This package offers a broader range of functionalities such as who clicked the button, how many times it was clicked and more. It uses [dislash.py](https://github.com/EQUENOS/dislash.py) to implement the Buttons functionality, but uses some of it's own methods in order to make a Button pagination menu simple.

## Showcase
![buttons_showcase](https://cdn.discordapp.com/attachments/655186216060321816/855818139450081280/buttons_showcase_reduced.gif)

---

## How to import
```py
from reactionmenu import ButtonsMenu, ComponentsButton
```
It should be noted that those two classes are the only classes that should be used when creating a Buttons pagination menu. All other classes in this package are *not* related and should not be used when creating a `ButtonsMenu`

```py
menu = ButtonsMenu(ctx, menu_type=ButtonsMenu.TypeEmbed)
```
---
## Initial setup
Before we get into the details of creating a buttons menu, you first need to allow your bot to be compatible with components. If you skip this step, `ButtonsMenu` will not work.

```py
from discord.ext import commands

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
ButtonsMenu.initialize(bot) # <-------- THIS IS REQUIRED

bot.run(...)
```
### Important note for initial setup
If you're using dislash.py separately, there's no need to call `ButtonsMenu.initialize(..)` at all since the discord.py `Messageable.send` has already been altered by `SlashClient`
```py
# dislash.py example
bot = commands.Bot(command_prefix="!")
SlashClient(bot)

# ButtonsMenu.initialize(bot) <----- NOT needed
```

---
## Parameters of the ButtonsMenu constructor
* `ctx` The `discord.ext.commands.Context` object
* `menu_type` (`int`) The configuration of the menu. Class variables:
  * `ButtonsMenu.TypeEmbed`, a normal embed pagination menu.
  * `ButtonsMenu.TypeEmbedDynamic`, an embed pagination menu with dynamic data. See ReactionMenu's description [here](#dynamic)
  * `ButtonsMenu.TypeText`, a text only pagination menu.
---
## Options of the ButtonsMenu constructor [kwargs]
| Name | Type | Default Value | Used for | Info 
-------|------|---------------|----------|------
| `wrap_in_codeblock` | `str` | `None` | `ButtonsMenu.TypeEmbedDynamic` | The discord codeblock language identifier to wrap your data in. Example: `ButtonsMenu(ctx, ..., wrap_in_codeblock='py')`
| `custom_embed` | `discord.Embed` | `None` | `ButtonsMenu.TypeEmbedDynamic` | Embed object to use when adding data with `ButtonsMenu.add_row()`. Used for styling purposes
| `delete_on_timeout` | `bool` | `False` | `All menu types` | Delete the menu when it times out
| `disable_buttons_on_timeout` | `bool` | `True` | `All menu types` | Disable the buttons on the menu when the menu times out
| `remove_buttons_on_timeout` | `bool` | `False` | `All menu types` | Remove the buttons on the menu when the menu times out
| `only_roles` | `List[discord.Role]` | `None` | `All menu types` | If set, only members with any of the given roles are allowed to control the menu. The menu owner can always control the menu
| `timeout` | `Union[int, float, None]` | `60.0` | `All menu types` | The timer for when the menu times out. Can be `None` for no timeout
| `show_page_director` | `bool` | `True` | `All menu types` | Shown at the botttom of each embed page. "Page 1/20"
| `name` | `str` | `None` | `All menu types` | A name you can set for the menu
| `style` | `str` | `"Page $/&"` | `All menu types` | A custom page director style you can select. "$" represents the current page, "&" represents the total amount of pages. Example: `ButtonsMenu(ctx, ..., style='On $ out of &')`
| `all_can_click` | `bool` | `False` | `All menu types` | Sets if everyone is allowed to control when pages are 'turned' when buttons are clicked
| `delete_interactions` | `bool` | `True` | `All menu types` | Delete the prompt message by the bot and response message by the user when asked what page they would like to go to when using `ComponentsButton.ID_GO_TO_PAGE`
| `rows_requested` | `int` | `None` | `ButtonsMenu.TypeEmbedDynamic` | The amount of information per `ButtonsMenu.add_row()` you would like applied to each embed page

---
## Pages for ButtonMenu
Depending on the `menu_type`, pages can either be a `str` or `discord.Embed`
* If the `menu_type` is `ButtonsMenu.TypeEmbed`, use embeds
* If the `menu_type` is `ButtonsMenu.TypeText` or `ButtonsMenu.TypeEmbedDynamic`, use strings.
* Associated methods
  * `ButtonsMenu.add_page(Union[discord.Embed, str])`
  * `ButtonsMenu.add_row(data: str)`
  * `ButtonsMenu.clear_all_pages()`
  * `ButtonsMenu.clear_all_row_data()`
  * `ButtonsMenu.remove_page(page_number: int)`
  * `ButtonsMenu.set_main_pages(*embeds: Embed)`
  * `ButtonsMenu.set_last_pages(*embeds: Embed)`

> **NOTE**: For an overview of `ButtonsMenu.TypeEmbedDynamic`, click [here](#dynamic). They are just like `ReactionMenu`'s dynamic setting, just with buttons instead

##### Adding Pages
```py
# ButtonsMenu.TypeEmbed
menu = ButtonsMenu(ctx, menu_type=ButtonsMenu.TypeEmbed)
menu.add_page(summer_embed)
menu.add_page(winter_embed)

# ButtonsMenu.TypeText
menu = ButtonsMenu(ctx, menu_type=ButtonsMenu.TypeText)
menu.add_page('Its so hot!')
menu.add_page('Its so cold!')

# ButtonsMenu.TypeEmbedDynamic
menu = ButtonsMenu(ctx, menu_type=ButtonsMenu.TypeEmbedDynamic, rows_requested=5)
for data in get_information():
  menu.add_row(data)
```
---
## Buttons for ButtonsMenu
Buttons are what you use to interact with the menu. Unlike reactions, they look cleaner, provides less rate limit issues, and offer more in terms of interactions. Enable and disable buttons, use markdown hyperlinks in it's messages, and even send hidden messages.

![discord_buttons](https://discord.com/assets/7bb017ce52cfd6575e21c058feb3883b.png)


* Associated methods
  * `ButtonsMenu.add_button(button: ComponentsButton)`
  * `ButtonsMenu.disable_all_buttons()`
  * `ButtonsMenu.disable_button(button: ComponentsButton)`
  * `ButtonsMenu.enable_all_buttons()`
  * `ButtonsMenu.enable_button(button: ComponentsButton)`
  * `ButtonsMenu.get_button(identity: str, *, search_by='label')`
  * `ButtonsMenu.remove_all_buttons()`
  * `ButtonsMenu.remove_button(button: ComponentsButton)`
  * `await ButtonsMenu.refresh_menu_buttons()`

## ComponentsButton
A `ComponentsButton` is a class that represents the discord button. It is a subclass of [dislash.py's](https://github.com/EQUENOS/dislash.py) `Button`.
```
class ComponentsButton(*, style: ButtonStyle, label: str, custom_id=None, emoji=None, url=None, disabled=False, followup=None)
```
The following are the rules set by Discord for Buttons:
* Link buttons don't send interactions to the Discord App, so link button statistics (it's properties) are not tracked
* Non-link buttons **must** have a `custom_id`, and cannot have a `url`
* Link buttons **must** have a `url`, and cannot have a `custom_id`
* There cannot be more than 25 buttons per message
---
## Parameters of the ComponentsButton constructor
* `style` (`ButtonStyle`) The button style
* `label` (`str`) The text on the button
* `custom_id` (`str`) An ID to determine what action that button should take. Just like ReactionMenu's [ButtonTypes](#all-buttontypes). Available IDs:
  * `ComponentsButton.ID_NEXT_PAGE`
  * `ComponentsButton.ID_PREVIOUS_PAGE`
  * `ComponentsButton.ID_GO_TO_FIRST_PAGE` 
  * `ComponentsButton.ID_GO_TO_LAST_PAGE`
  * `ComponentsButton.ID_GO_TO_PAGE`
  * `ComponentsButton.ID_END_SESSION`
  * `ComponentsButton.ID_CALLER`
  * `ComponentsButton.ID_SEND_MESSAGE`
* `emoji` (`discord.PartialEmoji`) Emoji used for the button
* `url` (`str`) URL for a button with style `ComponentsButton.style.link`
* `disabled` (`bool`) If the button should be disabled
* `followup` (`ComponentsButton.Followup`) The message sent after the button is clicked. Only available for buttons that have a `custom_id` of `ComponentsButton.ID_CALLER` or `ComponentsButton.ID_SEND_MESSAGE`. `ComponentsButton.Followup` is a class that has parameters similiar to discord.py's `Messageable.send()`, and is used to control if a message is ephemeral (hidden), contains a file, embed, tts, etc...

##### Attributes for ComponentsButton
The following attributes (properties) are made specifically for a `ComponentsButton`
| Property | Return Type | Info
|----------|-------------|------
| `clicked_by` | `Set[discord.Member]` | The members who clicked the button
| `total_clicks` | `int` | Amount of clicks from the button
| `last_clicked` | `datetime` | The time in UTC for when the button was last clicked

##### Adding a ComponentsButton
```py
from reactionmenu import ButtonsMenu, ComponentsButton

menu = ButtonsMenu(ctx, menu_type=ButtonsMenu.TypeEmbed)

# Link Button
link_button = ComponentsButton(style=ComponentsButton.style.link, emoji='🌍', label='Link to Google', url='https://google.com')

# ComponentsButton.ID_PREVIOUS_PAGE
back_button = ComponentsButton(style=ComponentsButton.style.primary, label='Back', custom_id=ComponentsButton.ID_PREVIOUS_PAGE)

# ComponentsButton.ID_NEXT_PAGE
next_button = ComponentsButton(style=ComponentsButton.style.secondary, label='Next', custom_id=ComponentsButton.ID_NEXT_PAGE)

# All other ComponentsButton are created the same way as the last 2 EXCEPT
# 1 - ComponentsButton.ID_CALLER
# 2 - ComponentsButton.ID_SEND_MESSAGE

# ComponentsButton.ID_SEND_MESSAGE
message_followup = ComponentsButton.Followup('This message is hidden!', ephemeral=True)
message_button = ComponentsButton(style=ComponentsButton.style.green, label='Message', custom_id=ComponentsButton.ID_SEND_MESSAGE, followup=message_followup)

# ComponentsButton.ID_CALLER
def say_hello(name: str):
    print('Hello', name)

call_followup = ComponentsButton.Followup()
call_followup.set_caller_details(say_hello, 'John')
caller_button = ComponentsButton(style=ComponentsButton.style.red, label='Say Hi', custom_id=ComponentsButton.ID_CALLER, followup=call_followup)

menu.add_button(link_button)
menu.add_button(back_button)
menu.add_button(next_button)
menu.add_button(message_button)
menu.add_button(caller_button)
```
---
> **NOTE:** When it comes to buttons with a `custom_id` of `ComponentsButton.ID_CALLER`, `ComponentsButton.ID_SEND_MESSAGE`, or link buttons, you can add as many as you'd like as long as in total it's 25 buttons or less. For all other button ID's, each menu can only have one.

## Updating ComponentsButton and Pages
* Associated methods
  * `await ButtonsMenu.refresh_menu_buttons()`
  * `await ButtonsMenu.update(new_pages: Union[List[Union[Embed, str]], None], new_buttons: Union[List[ComponentsButton], None])`

When the menu is running, you can update the pages or buttons on the menu. Using `ButtonsMenu.update(...)`, you can replace the pages and buttons. Using `ButtonsMenu.refresh_menu_buttons()` updates the buttons you have changed.

##### Updating a Button
```py
@bot.command()
async def menu(ctx):
    menu = ButtonsMenu(..., name='test')
    link_button = ComponentsButton(..., label='Link')
    
    menu.add_button(link_button)
    menu.add_page(...)

    await menu.start()


@bot.command()
async def disable(ctx):
    menu = ButtonsMenu.get_session('test')
    link_button = menu.get_button('Link', search_by='label')
    
    menu.disable_button(link_button)
    await menu.refresh_menu_buttons()
```
If the buttons are not refreshed with `ButtonsMenu.refresh_menu_buttons()`, the menu will not be updated when changing a button.

##### Updating Pages and Buttons
Method `ButtonsMenu.update(...)` is used when you want to replace all or a few of the buttons on the menu. 
```py
menu = ButtonsMenu(...)

# in a different .command()
await menu.update(new_pages=[hello_embed, goodbye_embed], new_buttons=[link_button, next_button])
```

> **NOTE**: When using `ButtonsMenu.update(...)`, there is no need to use `ButtonsMenu.refresh_menu_buttons()` because they are updated during the update call. 

---
## Starting/Stopping the ButtonsMenu
* Associated methods
  * `await ButtonsMenu.start(*, send_to=None)`
  * `await ButtonsMenu.stop(*, delete_menu_message=False, remove_buttons=False, disable_buttons=False)`

When starting the menu, you have the option to send the menu to a certain channel. Parameter `send_to` is the channel you'd like to send the menu to. You can set `send_to` as the channel name (`str`), channel ID (`int`), or channel object (`discord.TextChannel`). Example:
```py
menu = ButtonsMenu(...)
# channel name
await menu.start(send_to='bot-commands')

# channel ID
await menu.start(send_to=1234567890123456)

# channel object
channel = guild.get_channel(1234567890123456)
await menu.start(send_to=channel)
```
> **NOTE:** `send_to` is not valid if a menu was started in DM's

Only one option is available when stopping the menu. If you have multiple parameters as `True`, only one will execute
- `delete_menu_message` > `disable_buttons`
- `disable_buttons` > `remove_buttons`
---
## All attributes for ButtonsMenu
<details>
    <summary>Click to show all attributes</summary>

| Attribute | Return Type | Info
|-----------|-------------|-----
| `wrap_in_codeblock` | `str` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `custom_embed` | `discord.Embed` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `delete_on_timeout` | `bool` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `disable_buttons_on_timeout` | `bool` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `remove_buttons_on_timeout` | `bool` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `only_roles` | `List[discord.Role]` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `timeout` | `Union[int, float, None]` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `show_page_director` | `bool` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `name` | `str` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `style` | `str` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `all_can_click` | `bool` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `delete_interactions` | `bool` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `allowed_mentions` | `discord.AllowedMentions` | [info here](#options-of-the-buttonsmenu-constructor-kwargs)
| `is_running` | `bool` | if the menu is currently active (property)
| `owner` | `discord.Member` | the person who started the menu (property)
| `message` | `discord.Message` | the message the menu is operating from (property)
| `buttons`    | `List[ComponentsButton]` | the buttons registered to the menu (property)
| `buttons_most_clicked` | `List[ComponentsButton]` | buttons registered to the menu ordered from most clicks to least clicks (property)
| `in_dms` | `bool` | if the menu is in a DM (property)
| `pages` | `list` | the pages registered to the menu (property)

</details>

## All methods for ButtonsMenu
<details>
    <summary>Click to show all methods</summary>

* `ButtonsMenu.add_button(button: ComponentsButton)`
  * Register a button to the menu
---
* `ButtonsMenu.add_page(page: Union[Embed, str])`
  * Add a page to the menu
---
* `ButtonsMenu.add_row(data: str)`
  * Add text to the embed page by rows of data
---
* `ButtonsMenu.clear_all_pages()`
  * Remove all pages from the menu
---
* `ButtonsMenu.clear_all_row_data()`
  * Delete all the data thats been added using `ButtonsMenu.add_row()`
---
* `ButtonsMenu.disable_all_buttons()`
  * Disable all buttons on the menu
---
* `ButtonsMenu.disable_button(button: ComponentsButton)`
  * Disable a button on the menu
---
* `ButtonsMenu.enable_all_buttons()`
  * Enable all buttons on the menu
---
* `ButtonsMenu.enable_button(button: ComponentsButton)`
  * Enable the specified button
---
* `ButtonsMenu.get_all_sessions() -> Union[List[ButtonsMenu], None]`
  * *class method* Get all active menu sessions
---
* `ButtonsMenu.get_button(identity: str, *, search_by='label') -> Union[ComponentsButton, List[ComponentsButton], None]`
  * Get a button that has been registered to the menu by it's label or custom_id
---
* `ButtonsMenu.get_menu_from_message(message_id: int) -> Union[ButtonsMenu, None]`
  * *class method* Return the `ButtonsMenu` object associated with the message with the given ID
---
* `ButtonsMenu.get_session(name: str) -> Union[ButtonsMenu, List[ButtonsMenu], None]`
  * *class method* Get a `ButtonsMenu` instance by its name
---
* `ButtonsMenu.get_sessions_count() -> int`
  * *class method* Get the amount of active menu sessions
---
* `ButtonsMenu.initialize(bot: Union[Bot, AutoShardedBot])`
  * *static method* The initial setup needed in order to use Discord Components (Buttons)
---
* `await ButtonsMenu.refresh_menu_buttons()`
  * When the menu is running, update the message to reflect the buttons that were removed, disabled, or added
---
* `ButtonsMenu.remove_all_buttons()`
  * Remove all buttons from the menu
---
* `ButtonsMenu.remove_button(button: ComponentsButton)`
  * Remove a button from the menu
---
* `ButtonsMenu.remove_page(page_number: int)`
  * Remove a page from the menu
---
* `ButtonsMenu.set_last_pages(*embeds: Embed)`
  * On a menu with a menu_type of `ButtonsMenu.TypeEmbedDynamic`, set the pages you would like to show last. These embeds will be shown after the embeds that contain your data
---
* `ButtonsMenu.set_main_pages(*embeds: Embed)`
  * On a menu with a menu_type of `ButtonsMenu.TypeEmbedDynamic`, set the pages you would like to show first. These embeds will be shown before the embeds that contain your data
---
* `ButtonsMenu.set_on_timeout(func: object)`
  * Set the function to be called when the menu times out
---
* `await ButtonsMenu.start(*, send_to=None)`
  * Start the menu
---
* `await ButtonsMenu.stop(*, delete_menu_message=False, remove_buttons=False, disable_buttons=False)`
  * Stops the process of the menu with the option of deleting the menu's message, removing the buttons, or disabling the buttons upon stop
---
* `await ButtonsMenu.stop_all_sessions()`
  * *class method* Stop all active menu sessions
---
* `await ButtonsMenu.stop_session(name: str, include_all=False)`
  * *class method* Stop a menu session by it's name
---
* `await ButtonsMenu.update(new_pages: Union[List[Union[Embed, str]], None], new_buttons: Union[List[ComponentsButton], None])`
  * When the menu is running, update the pages or buttons

</details>

[Jump to top](#github-updates-vs-pypi-updates)
