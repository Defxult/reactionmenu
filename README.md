![logo](https://cdn.discordapp.com/attachments/655186216060321816/820162226316378162/discord.jpg)
<div align="center">

[![Downloads](https://pepy.tech/badge/reactionmenu)](https://pepy.tech/project/reactionmenu) 
[![Downloads](https://pepy.tech/badge/reactionmenu/month)](https://pepy.tech/project/reactionmenu)
[![Downloads](https://pepy.tech/badge/reactionmenu/week)](https://pepy.tech/project/reactionmenu)

![python_version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)
</div>

## GitHub Updates vs PyPI Updates
The GitHub version of this library will always have the latest changes, fixes, and additions before the [PyPI](https://pypi.org/project/reactionmenu/) version. You can install the GitHub version by doing:
```
$ pip install git+https://github.com/Defxult/reactionmenu
```

You must have [Git](https://git-scm.com/) installed in order to do this. With that said, the current README.md documentation represents the GitHub version of this library. If you are using the PyPI version of this library, it is suggested to read the README.md that matches your PyPI version [here](https://github.com/Defxult/reactionmenu/releases) because documentation may have changed.

* `GitHub: v3.0.0`
* `PyPI: v3.0.0`

---

## How to install
```
$ pip install reactionmenu
```

## Notice
With the discontinuation of discord.py, this library is now dependent on [Pycord](https://github.com/Pycord-Development/pycord). Pycord has been released and is currently in beta. Until it is out of beta, pip installing this library will not automatically install Pycord. When it comes to installing Pycord, you have a few options:

* Option 1 - Install their most recent PyPI 2.0 version [here](https://pypi.org/project/py-cord/#history)
* Option 2 - Install their development version of the library following their [instructions](https://github.com/Pycord-Development/pycord#installing)

---
## Documentation
* Jump to [ReactionMenu](#reactionmenu)
* Jump to [ViewMenu](#viewmenu)

---
## Intents
Minimum intents needed
```py
bot = commands.Bot(..., intents=discord.Intents(messages=True, guilds=True, reactions=True, members=True))
```
---
## ReactionMenu

```
class reactionmenu.ReactionMenu(ctx: Context, *, menu_type: int, **kwargs)
```
![showcase](https://cdn.discordapp.com/attachments/655186216060321816/819885696176226314/showcase.gif)
### How to import
```py
from reactionmenu import ReactionMenu, ReactionButton
```
This library comes with several methods and options in order to make a discord reaction menu simple. Once you have imported the proper classes, you will initialize the constructor like so:
```py
menu = ReactionMenu(ctx, menu_type=ReactionMenu.TypeEmbed)
```


### Parameters of the ReactionMenu constructor
* `ctx` (`discord.ext.commands.Context`) A context object
* `menu_type` (`int`) The configuration of the menu
  * `ReactionMenu.TypeEmbed`, a normal embed pagination menu
  * `ReactionMenu.TypeEmbedDynamic`, an embed pagination menu with dynamic data
  * `ReactionMenu.TypeText`, a text only pagination menu


### Kwargs of the ReactionMenu constructor
| Name | Type | Default Value | Used for | Info 
-------|------|---------------|----------|------
| `wrap_in_codeblock` | `str` | `None` | `ReactionMenu.TypeEmbedDynamic` | The discord codeblock language identifier to wrap your data in. Example: `ReactionMenu(ctx, ..., wrap_in_codeblock='py')`
| `custom_embed` | `discord.Embed` | `None` | `ReactionMenu.TypeEmbedDynamic` | Embed object to use when adding data with `ReactionMenu.add_row()`. Used for styling purposes
| `delete_on_timeout` | `bool` | `False` | `All menu types` | Delete the menu when it times out
| `clear_reactions_after` | `bool` | `True` | `All menu types` | delete all reactions after the menu times out
| `navigation_speed` | `str` | `ReactionMenu.NORMAL` | `All menu types` | Sets if the user needs to wait for the reaction to be removed by the bot before "turning" the page. Setting the speed to `ReactionMenu.FAST` makes it so that there is no need to wait (reactions are not removed on each press) and can navigate lengthy menu's more quickly
| `only_roles` | `List[discord.Role]` | `None` | `All menu types` | If set, only members with any of the given roles are allowed to control the menu. The menu owner can always control the menu
| `timeout` | `Union[int, float, None]` | `60.0` | `All menu types` | The timer for when the menu times out. Can be `None` for no timeout
| `show_page_director` | `bool` | `True` | `All menu types` | Shown at the bottom of each embed page. "Page 1/20"
| `name` | `str` | `None` | `All menu types` | A name you can set for the menu
| `style` | `str` | `"Page $/&"` | `All menu types` | A custom page director style you can select. "$" represents the current page, "&" represents the total amount of pages. Example: `ReactionMenu(ctx, ..., style='On $ out of &')`
| `all_can_click` | `bool` | `False` | `All menu types` | Sets if everyone is allowed to control when pages are 'turned' when buttons are clicked
| `delete_interactions` | `bool` | `True` | `All menu types` | Delete the prompt message by the bot and response message by the user when asked what page they would like to go to when using `ReactionButton.Type.GO_TO_PAGE`
| `rows_requested` | `int` | `None` | `ReactionMenu.TypeEmbedDynamic` | The amount of information per `ReactionMenu.add_row()` you would like applied to each embed page
| `remove_extra_emojis` | `bool` | `False` | `All menu types` | If `True`, all emojis (reactions) added to the menu message that were not originally added to the menu will be removed
---

### Pages for ReactionMenu
Depending on the `menu_type`, pages can either be a `str` or `discord.Embed`
* If the `menu_type` is `ReactionMenu.TypeEmbed`, use embeds (embed only menu)
* If the `menu_type` is `ReactionMenu.TypeText` (text only menu) or `ReactionMenu.TypeEmbedDynamic` (embed only menu), use strings.
* Associated methods
  * `ReactionMenu.add_page(Union[discord.Embed, str])`
  * `ReactionMenu.add_pages(pages: Sequence[Union[discord.Embed, str]])`
  * `ReactionMenu.add_row(data: str)`
  * `ReactionMenu.remove_all_pages()`
  * `ReactionMenu.clear_all_row_data()`
  * `ReactionMenu.remove_page(page_number: int)`
  * `ReactionMenu.set_main_pages(*embeds: Embed)`
  * `ReactionMenu.set_last_pages(*embeds: Embed)`


#### Adding Pages
```py
# ReactionMenu.TypeEmbed
menu = ReactionMenu(ctx, menu_type=ReactionMenu.TypeEmbed)
menu.add_page(summer_embed)
menu.add_page(winter_embed)

# ReactionMenu.TypeText
menu = ReactionMenu(ctx, menu_type=ReactionMenu.TypeText)
menu.add_page('Its so hot!')
menu.add_page('Its so cold!')
```

#### ReactionMenu.TypeText
A `TypeText` menu is a text based pagination menu. No embeds are involved in the pagination process, only plain text is used.

![showcase-text](https://cdn.discordapp.com/attachments/655186216060321816/929172629947027466/text_showcase.gif)

#### ReactionMenu.TypeEmbedDynamic
A dynamic menu is used when you do not know how much information will be applied to the menu. For example, if you were to request information from a database, that information can always change. You query something and you might get 1,500 results back, and the next maybe only 800. A dynamic menu pieces all this information together for you and adds it to an embed page by rows of data. `ReactionMenu.add_row()` is best used in some sort of `Iterable` where everything can be looped through, but only add the amount of data you want to the menu page.
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
menu = ReactionMenu(ctx, menu_type=ReactionMenu.TypeEmbedDynamic, rows_requested=5)

for data in database.request('SELECT * FROM customers'):
    menu.add_row(data)
```
##### Deleting Data
You can remove all the data you've added to a menu by using `menu.clear_all_row_data()`

##### Main/Last Pages
When using a dynamic menu, the only embed pages you see are from the data you've added. But if you would like to show more pages other than just the data, you can use methods `ReactionMenu.set_main_pages()` and `ReactionMenu.set_last_pages()`. Setting the main page(s), the embeds you set will be the first embeds that are shown when the menu starts. Setting the last page(s) are the last embeds shown
```py
menu.set_main_pages(welcome_embed, announcement_embed)

for data in get_information():
    menu.add_row(data)

menu.set_last_pages(additional_info_embed)
# NOTE: setting main/last pages can be set in any order
```

### ReactionButtons and ButtonTypes
Buttons/button types are used when you want to add a reaction to the menu that does a certain function. Buttons and button types work together to achieve the desired action.
```
class reactionmenu.ReactionButton(*, emoji: str, linked_to: ButtonType, **kwargs)
```
### Parameters of the ReactionButton constructor
* `emoji` (`str`) The emoji you would like to use as the reaction
* `linked_to` (`ReactionButton.Type`) When the reaction is pressed, this is what determines what it will do

### Kwargs of the ReactionButton constructor
| Name | Type | Default Value | Used for
|------|------|---------------|----------
| `embed` | `discord.Embed` | `None` | When the reaction is pressed, go to the specified embed
| `name` | `str` | `None` | The name of the button
| `details` | [info below](#reactionbuttons-with-reactionbuttontypecaller) | `None` | Assigns the function and it's arguments to call when a `ReactionButton` with `ReactionButton.Type.CALLER` is pressed
| `event` | `ReactionButton.Event` | `None` | Determine when a button should be removed depending on how many times it has been pressed
| `skip` | `ReactionButton.Skip` | `None` | Set the action and the amount of pages to skip when using a `linked_to` of `ReactionButton.Type.SKIP`

### Attributes for ReactionButton
| Property | Return Type | Info
|----------|-------------|------
| `clicked_by` | `Set[discord.Member]` | The members who clicked the button
| `total_clicks` | `int` | Amount of clicks from the button
| `last_clicked` | `datetime.datetime` | The time in UTC for when the button was last clicked
| `menu` | `ReactionMenu` | The menu the button is attached to

* Associated methods
    * `ReactionMenu.add_button(button: ReactionButton)`
    * `ReactionMenu.remove_all_buttons()`
    * `ReactionMenu.remove_button(button: ReactionButton)`
    * `ReactionMenu.get_button(identity: Union[str, int], *, search_by='name')`
    * `ReactionButton.set_caller_details(func: Callable[..., None], *args, **kwargs)`


### All ButtonTypes
| Type | Info |
|-------|------|
| `ReactionButton.Type.NEXT_PAGE` | Go to the next page in the menu session
| `ReactionButton.Type.PREVIOUS_PAGE` | Go to the previous page in the menu session
| `ReactionButton.Type.GO_TO_FIRST_PAGE` | Go to the first page in the menu session
| `ReactionButton.Type.GO_TO_LAST_PAGE` | Go to the last page in the menu session
| `ReactionButton.Type.GO_TO_PAGE` | Prompts you to type in the page you'd like to go to
| `ReactionButton.Type.END_SESSION` | Stops the session and deletes the menu message
| `ReactionButton.Type.CUSTOM_EMBED` | Used separately from the navigation buttons. Once pressed, go to the specified embed 
| `ReactionButton.Type.CALLER` | Used when specifying the function to call and it's arguments when the button is pressed
| `ReactionButton.Type.SKIP` | Used to paginate through multiple pages in a single button press


### Adding Buttons
You can add buttons (reactions) to the menu using a `ReactionButton`. Below are examples on how to use each `ButtonType`. 
> **NOTE:** ReactionButtons with `ReactionButton.Type.CALLER` are a little different, so there is a dedicated section explaining how they work and how to implement them further below

```py
menu = ReactionMenu(...)

# first and last pages
fpb = ReactionButton(emoji='⏪', linked_to=ReactionButton.Type.GO_TO_FIRST_PAGE)
lpb = ReactionButton(emoji='⏩', linked_to=ReactionButton.Type.GO_TO_LAST_PAGE)

# go to page
gtpb = ReactionButton(emoji='🔢', linked_to=ReactionButton.Type.GO_TO_PAGE)

# end session
esb = ReactionButton(emoji='⏹️', linked_to=ReactionButton.Type.END_SESSION)

# custom embed
ceb = ReactionButton(emoji='😎', linked_to=ReactionButton.Type.CUSTOM_EMBED, embed=discord.Embed(title='Hello'))

# skip button
sb = ReactionButton(emoji='5️⃣', linked_to=ReactionButton.Type.SKIP, skip=ReactionButton.Skip(action='+', amount=5))

menu.add_button(fpb)
menu.add_button(lpb)
menu.add_button(gtpb)
menu.add_button(esb)
menu.add_button(ceb)
menu.add_button(sb)
```
### Deleting Buttons
Remove all buttons with `menu.remove_all_buttons()`. You can also remove an individual button using its name if you have it set, or the button object itself with `menu.remove_button()`

### ReactionButtons with ReactionButton.Type.CALLER
`ReactionButton.Type.CALLER` buttons are used to implement your own functionality into the menu. Maybe you want to add a button that creates a text channel, sends a message, or add something to a database, whatever it may be. In order to work with `ReactionButton.Type.CALLER`, use the class method below.

* `ReactionButton.set_caller_details(func: Callable[..., None], *args, **kwargs)`
  
This class method is used to setup a function and it's arguments that are later called when the button is pressed. The `ReactionButton` constructor has the kwarg `details`, and that's what you'll use with `.set_caller_details()` to assign the values needed. Some examples are below on how to properly implement `ReactionButton.Type.CALLER`

```py
@bot.command()
async def user(ctx, name, *, message):
    await ctx.send(f"Hi {name}! {message}. We're glad you're here!")

def car(year, make, model):
    print(f"I have a {year} {make} {model}")

ub = ReactionButton(emoji='👋', linked_to=ReactionButton.Type.CALLER, details=ReactionButton.set_caller_details(user, ctx, 'Defxult', message='Welcome to the server'))
cb = ReactionButton(emoji='🚗', linked_to=ReactionButton.Type.CALLER, details=ReactionButton.set_caller_details(car, 2021, 'Ford', 'Mustang'))
```
> **NOTE:** The function you pass in should not return anything. Calling functions with `ReactionButton.Type.CALLER` does not store or handle anything returned by that function
---

### ReactionButton Methods
The `ReactionButton` class comes with a set factory methods (class methods) that returns a `ReactionButton` with parameters set according to their `linked_to`.

* `ReactionButton.back()`
  * `emoji`: "◀️"
  * `linked_to`: `ReactionButton.Type.PREVIOUS_PAGE`
* `ReactionButton.next()`
	* `emoji`: "▶️"
	* `linked_to`: `ReactionButton.Type.NEXT_PAGE`
* `ReactionButton.go_to_first_page()`
	* `emoji`: "⏪"
	* `linked_to`: `ReactionButton.Type.GO_TO_FIRST_PAGE`
* `ReactionButton.go_to_last_page()`
	* `emoji`: "⏩"
	* `linked_to`: `ReactionButton.Type.GO_TO_LAST_PAGE`
* `ReactionButton.go_to_page()`
	* `emoji`: "🔢"
	* `linked_to`: `ReactionButton.Type.GO_TO_PAGE`
* `ReactionButton.end_session()`
	* `emoji`: "⏹️"
	* `linked_to`: `ReactionButton.Type.END_SESSION`
* `ReactionButton.all()`
  * Returns a `list` of `ReactionButton` in the following order
  * `.go_to_first_page()` `.back()` `.next()` `.go_to_last_page()` `.go_to_page()` `.end_session()`
* `ReactionButton.skip(emoji: str, action: str, amount: int)`
  * `emoji`: `<emoji>`
  * `linked_to`: `ReactionButton.Type.SKIP`

### Auto-pagination

An auto-pagination menu is a menu that doesn't need a reaction press to go to the next page. It turns pages on it's own every x amount of seconds. This can be useful if you'd like to have a continuous display of information to your server. That information might be server stats, upcoming events, etc. Below is an example of an auto-pagination menu.

![auto-pagin-showcase](https://cdn.discordapp.com/attachments/655186216060321816/842352164713791508/auto-pagin-reduced.gif)

* Associated methods
  * `ReactionMenu.set_as_auto_paginator(*, turn_every: Union[int, float])`
  * `ReactionMenu.update_turn_every(*, turn_every: Union[int, float])`
  * `ReactionMenu.refresh_auto_pagination_data(*data: Union[str, discord.Embed])`
  * `ReactionMenu.update_all_turn_every(*, turn_every: Union[int, float])` (class method)
  * `await ReactionMenu.stop_all_auto_sessions()` (class method)
  * `ReactionMenu.auto_turn_every` (property)
  * `ReactionMenu.auto_paginator` (property)

Example:
```py
menu = ReactionMenu(ctx, menu_type=ReactionMenu.TypeEmbed)

menu.add_page(server_info_embed)
menu.add_page(social_media_embed)
menu.add_page(games_embed)

menu.set_as_auto_paginator(turn_every=120)
await menu.start()
```
---
### Setting Limits
If you'd like, you can limit the amount of reaction menus that can be active at the same time *per* "guild", "member", or "channel" 
* Associated CLASS Methods
    * `ReactionMenu.set_sessions_limit(limit: int, per='guild', message='Too many active menus. Wait for other menus to be finished.')` 
    * `ReactionMenu.remove_limit()`
    * `ReactionMenu.get_sessions_count()`
    * `await ReactionMenu.stop_all_sessions()`

Example:
```py
@bot.command()
async def limit(ctx):
    ReactionMenu.set_sessions_limit(3, per='member', message='Sessions are limited to 3 per member')
```

With the above example, only 3 menus can be active at once for each member, and if they try to create more before their other menu's are finished, they will get an error message saying "Sessions are limited to 3 per member".

### ReactionButton Events
You can set a `ReactionButton` to be removed when it has been pressed a certain amount of times

```
class ReactionButton.Event(event_type: str, value: int)
```

#### Parameters for ReactionButton.Event
* `event_type` (`str`) The action to take. The only available option is "remove"
* `value` (`int`) The amount set for the specified event. Must be >= 1. If value is <= 0, it is implicitly set to 1

Example:
```py
menu = ReactionMenu(ctx, ...)

# remove a button after 10 clicks
button = ReactionButton(..., event=ReactionButton.Event('remove', 10))
menu.add_button(button)
```
> **NOTE:** Not ideal for buttons with a `linked_to` of `ReactionButton.Type.END_SESSION`
---
### ReactionMenu Relays
Menu relays are functions that are called anytime a button that is apart of a menu is pressed. It is considered as an extension of a `ReactionButton` with a `linked_to` of `ReactionButton.Type.CALLER`. Unlike caller buttons which provides no details about the interactions on the menu, relays do.
* Associated methods
  * `ReactionMenu.set_relay(func: Callable[[NamedTuple], None], *, only: List[ReactionButton]=None)`
  * `ReactionMenu.remove_relay()`

When creating a function for your relay, that function must contain a single positional argument. When a button is pressed, a `RelayPayload` object (a named tuple) is passed to that function. The attributes of `RelayPayload` are:
* `member` (`discord.Member`) The person who pressed the button
* `button` (`ReactionButton`) The button that was pressed

Example:
```py
async def enter_giveaway(payload):
    member = payload.member
    channel = payload.button.menu.message.channel
    await channel.send(f"{member.mention}, you've entered the giveaway!")

menu = ReactionMenu(ctx, ...)
menu.set_relay(enter_giveaway)
```
The `set_relay` method comes with the `only` parameter. If that parameter is `None`, all buttons that are pressed will be relayed. You can provide a `list` of buttons to that parameter so only button presses from those specified buttons will be relayed.
```py
def example(payload):
    ...

menu = ReactionMenu(ctx, ...)

back_button = ReactionButton.back()
next_button = ReactionButton.next()

menu.set_relay(example, only=[back_button])
```

---
### Starting/Stopping the ReactionMenu
* Associated methods
  * `await ReactionMenu.start(*, send_to=None, reply=False)`
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

### Full Example
Here is a basic implementation of `ReactionMenu` that you can copy & paste for a quick demonstration.
```py
import discord
from discord.ext import commands
from reactionmenu import ReactionMenu, ReactionButton

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.command()
async def example(ctx):
    menu = ReactionMenu(ctx, menu_type=ReactionMenu.TypeEmbed)
    
    for member in ctx.guild.members:
        if member.avatar:
            embed = discord.Embed(description=f'Joined {member.joined_at.strftime("%b. %d, %Y")}')
            embed.set_author(name=member.name, icon_url=member.avatar.url)
            menu.add_page(embed)
    
    menu.add_button(ReactionButton.back())
    menu.add_button(ReactionButton.next())
    menu.add_button(ReactionButton.end_session())
    
    await menu.start()

bot.run(...)
```

---
---


## ViewMenu
```
class reactionmenu.ViewMenu(ctx: Context, *, menu_type: int, **kwargs)
```

A `ViewMenu` is a menu that uses discords Buttons feature. With buttons, you can enable and disable them, set a certain color for them with emojis, have buttons that send hidden messages, and add hyperlinks. This library offers a broader range of functionalities such as who pressed the button, how many times it was pressed and more. It uses views (`discord.ui.View`) to implement the Buttons functionality, but uses some of it's own methods in order to make a Button pagination menu simple.

![image](https://cdn.discordapp.com/attachments/655186216060321816/855818139450081280/buttons_showcase_reduced.gif)

### How to import
```py
from reactionmenu import ViewMenu, ViewButton
```
---

### Parameters of the ViewMenu constructor
* `ctx` (`discord.ext.commands.Context`) A context object
* `menu_type` (`int`) The configuration of the menu
  * `ViewMenu.TypeEmbed`, a normal embed pagination menu
  * `ViewMenu.TypeEmbedDynamic`, an embed pagination menu with dynamic data
  * `ViewMenu.TypeText`, a text only pagination menu

---
### Kwargs of the ViewMenu constructor
| Name | Type | Default Value | Used for | Info 
-------|------|---------------|----------|------
| `wrap_in_codeblock` | `str` | `None` | `ViewMenu.TypeEmbedDynamic` | The discord codeblock language identifier to wrap your data in. Example: `ViewMenu(ctx, ..., wrap_in_codeblock='py')`
| `custom_embed` | `discord.Embed` | `None` | `ViewMenu.TypeEmbedDynamic` | Embed object to use when adding data with `ViewMenu.add_row()`. Used for styling purposes
| `delete_on_timeout` | `bool` | `False` | `All menu types` | Delete the menu when it times out
| `disable_buttons_on_timeout` | `bool` | `True` | `All menu types` | Disable the buttons on the menu when the menu times out
| `remove_buttons_on_timeout` | `bool` | `False` | `All menu types` | Remove the buttons on the menu when the menu times out
| `only_roles` | `List[discord.Role]` | `None` | `All menu types` | If set, only members with any of the given roles are allowed to control the menu. The menu owner can always control the menu
| `timeout` | `Union[int, float, None]` | `60.0` | `All menu types` | The timer for when the menu times out. Can be `None` for no timeout
| `show_page_director` | `bool` | `True` | `All menu types` | Shown at the bottom of each embed page. "Page 1/20"
| `name` | `str` | `None` | `All menu types` | A name you can set for the menu
| `style` | `str` | `"Page $/&"` | `All menu types` | A custom page director style you can select. "$" represents the current page, "&" represents the total amount of pages. Example: `ViewMenu(ctx, ..., style='On $ out of &')`
| `all_can_click` | `bool` | `False` | `All menu types` | Sets if everyone is allowed to control when pages are 'turned' when buttons are clicked
| `delete_interactions` | `bool` | `True` | `All menu types` | Delete the prompt message by the bot and response message by the user when asked what page they would like to go to when using `ViewButton.ID_GO_TO_PAGE`
| `rows_requested` | `int` | `None` | `ViewMenu.TypeEmbedDynamic` | The amount of information per `ViewMenu.add_row()` you would like applied to each embed page
---

### Pages for ViewMenu
Depending on the `menu_type`, pages can either be a `str` or `discord.Embed`
* If the `menu_type` is `ViewMenu.TypeEmbed`, use embeds (embed only menu)
* If the `menu_type` is `ViewMenu.TypeText` (text only menu) or `ViewMenu.TypeEmbedDynamic` (embed only menu), use strings.
* Associated methods
  * `ViewMenu.add_page(Union[discord.Embed, str])`
  * `ViewMenu.add_pages(pages: Sequence[Union[discord.Embed, str]])`
  * `ViewMenu.add_row(data: str)`
  * `ViewMenu.remove_all_pages()`
  * `ViewMenu.clear_all_row_data()`
  * `ViewMenu.remove_page(page_number: int)`
  * `ViewMenu.set_main_pages(*embeds: Embed)`
  * `ViewMenu.set_last_pages(*embeds: Embed)`

#### Adding Pages
```py
# ViewMenu.TypeEmbed
menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)
menu.add_page(summer_embed)
menu.add_page(winter_embed)

# ViewMenu.TypeText
menu = ViewMenu(ctx, menu_type=ViewMenu.TypeText)
menu.add_page('Its so hot!')
menu.add_page('Its so cold!')
```

#### ViewMenu.TypeText
A `TypeText` menu is a text based pagination menu. No embeds are involved in the pagination process, only plain text is used.

![text_view_showcase](https://cdn.discordapp.com/attachments/655186216060321816/929744985656549386/text_view_showcase.gif)

#### ViewMenu.TypeEmbedDynamic
A dynamic menu is used when you do not know how much information will be applied to the menu. For example, if you were to request information from a database, that information can always change. You query something and you might get 1,500 results back, and the next maybe only 800. A dynamic menu pieces all this information together for you and adds it to an embed page by rows of data. `ViewMenu.add_row()` is best used in some sort of `Iterable` where everything can be looped through, but only add the amount of data you want to the menu page.
> **NOTE:** In a dynamic menu, all added data is placed in the description section of an embed. If you choose to use a `custom_embed`, all text in the description will be overridden with the data you add
* Associated methods
    * `ViewMenu.add_row(data: str)`
    * `ViewMenu.clear_all_row_data()`
    * `ViewMenu.set_main_pages(*embeds: Embed)`
    * `ViewMenu.set_last_pages(*embeds: Embed)`
* The kwargs specifically made for a dynamic menu are:
    * `rows_requested` - The amount of rows you would like on each embed page before making a new page
        * `ViewMenu(ctx, ..., rows_requested=5)`
    * `custom_embed` - An embed you have created to use as the embed pages. Used for your menu aesthetic
        * `ViewMenu(ctx, ..., custom_embed=red_embed)`
    * `wrap_in_codeblock` - The language identifier when wrapping your data in a discord codeblock. 
        * `ViewMenu(ctx, ..., wrap_in_codeblock='py')`

##### Adding Rows/data
```py
menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbedDynamic, rows_requested=5)

for data in database.request('SELECT * FROM customers'):
    menu.add_row(data)
```
##### Deleting Data
You can remove all the data you've added to a menu by using `menu.clear_all_row_data()`

##### Main/Last Pages
When using a dynamic menu, the only embed pages you see are from the data you've added. But if you would like to show more pages other than just the data, you can use methods `ViewMenu.set_main_pages()` and `ViewMenu.set_last_pages()`. Setting the main page(s), the embeds you set will be the first embeds that are shown when the menu starts. Setting the last page(s) are the last embeds shown
```py
menu.set_main_pages(welcome_embed, announcement_embed)

for data in get_information():
    menu.add_row(data)

menu.set_last_pages(additional_info_embed)
# NOTE: setting main/last pages can be set in any order
```

### Buttons for ViewMenu
Buttons are what you use to interact with the menu. Unlike reactions, they look cleaner, provides less rate limit issues, and offer more in terms of interactions. Enable and disable buttons, use markdown hyperlinks in it's messages, and even send hidden messages.

![discord_buttons](https://discord.com/assets/7bb017ce52cfd6575e21c058feb3883b.png)


* Associated methods
  * `ViewMenu.add_button(button: ViewButton)`
  * `ViewMenu.disable_all_buttons()`
  * `ViewMenu.disable_button(button: ViewButton)`
  * `ViewMenu.enable_all_buttons()`
  * `ViewMenu.enable_button(button: ViewButton)`
  * `ViewMenu.get_button(identity: str, *, search_by='label')`
  * `ViewMenu.remove_all_buttons()`
  * `ViewMenu.remove_button(button: ViewButton)`
  * `await ViewMenu.refresh_menu_buttons()`

#### ViewButton
```
class reactionmenu.ViewButton(*, style=discord.ButtonStyle.secondary, label=None, disabled=False, custom_id=None, url=None, emoji=None, followup=None, event=None, **kwargs)
```

A `ViewButton` is a class that represents the discord button. It is a subclass of `discord.ui.Button`.

The following are the rules set by Discord for Buttons:
* Link buttons don't send interactions to the Discord App, so link button statistics (it's properties) are not tracked
* Non-link buttons **must** have a `custom_id`, and cannot have a `url`
* Link buttons **must** have a `url`, and cannot have a `custom_id`
* There cannot be more than 25 buttons per message
---
#### Parameters of the ViewButton constructor
* `style` (`discord.ButtonStyle`) The button style
* `label` (`str`) The text on the button
* `custom_id` (`str`) An ID to determine what action that button should take. Available IDs:
  * `ViewButton.ID_NEXT_PAGE`
  * `ViewButton.ID_PREVIOUS_PAGE`
  * `ViewButton.ID_GO_TO_FIRST_PAGE` 
  * `ViewButton.ID_GO_TO_LAST_PAGE`
  * `ViewButton.ID_GO_TO_PAGE`
  * `ViewButton.ID_END_SESSION`
  * `ViewButton.ID_CALLER`
  * `ViewButton.ID_SEND_MESSAGE`
  * `ViewButton.ID_CUSTOM_EMBED` (only valid with menu type `ViewMenu.TypeEmbedDynamic`)
  * `ViewButton.ID_SKIP`
* `emoji` (`Union[str, discord.PartialEmoji]`) Emoji used for the button
  * `ViewButton(..., emoji='😄')` 
  * `ViewButton(..., emoji='<:miscTwitter:705423192818450453>')`
  * `ViewButton(..., emoji='\U000027a1')`
  * `ViewButton(..., emoji='\N{winking face}')`
* `url` (`str`) URL for a button with style `discord.ButtonStyle.link`
* `disabled` (`bool`) If the button should be disabled
* `followup` (`ViewButton.Followup`) The message sent after the button is pressed. Only available for buttons that have a `custom_id` of `ViewButton.ID_CALLER` or `ViewButton.ID_SEND_MESSAGE`. `ViewButton.Followup` is a class that has parameters similar to `discord.abc.Messageable.send()`, and is used to control if a message is ephemeral (hidden), contains a file, embed, tts, etc...
* `event` (`ViewButton.Event`) Set a button to be disabled or removed when it has been pressed a certain amount of times

#### Kwargs of the ViewButton constructor
| Name | Type | Default Value | Used for
|------|------|---------------|----------
| `name` | `str` | `None` | The name of the button
| `skip` | `ViewButton.Skip` | `None` | Set the action and the amount of pages to skip when using a `custom_id` of `ViewButton.ID_SKIP`

#### Attributes for ViewButton
| Property | Return Type | Info
|----------|-------------|------
| `clicked_by` | `Set[discord.Member]` | The members who clicked the button
| `total_clicks` | `int` | Amount of clicks from the button
| `last_clicked` | `datetime.datetime` | The time in UTC for when the button was last clicked
| `menu` | `ViewMenu` | The menu the button is attached to

#### Adding a ViewButton
```py
from reactionmenu import ViewMenu, ViewButton

menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)

# Link button
link_button = ViewButton(style=discord.ButtonStyle.link, emoji='🌍', label='Link to Google', url='https://google.com')
menu.add_button(link_button)

# Skip button
skip = ViewButton(style=discord.ButtonStyle.primary, label='+5', custom_id=ViewButton.ID_SKIP, skip=ViewButton.Skip(action='+', amount=5))
menu.add_button(skip)

# ViewButton.ID_PREVIOUS_PAGE
back_button = ViewButton(style=discord.ButtonStyle.primary, label='Back', custom_id=ViewButton.ID_PREVIOUS_PAGE)
menu.add_button(back_button)

# ViewButton.ID_NEXT_PAGE
next_button = ViewButton(style=discord.ButtonStyle.secondary, label='Next', custom_id=ViewButton.ID_NEXT_PAGE)
menu.add_button(next_button)

# All other ViewButton are created the same way as the last 2 EXCEPT
# 1 - ViewButton.ID_CALLER
# 2 - ViewButton.ID_SEND_MESSAGE
# 3 - ViewButton.ID_CUSTOM_EMBED


# ViewButton.ID_CALLER
def say_hello(name: str):
    print('Hello', name)

call_followup = ViewButton.Followup(details=ViewButton.Followup.set_caller_details(say_hello, 'John'))
menu.add_button(ViewButton(label='Say hi', custom_id=ViewButton.ID_CALLER, followup=call_followup))

# ViewButton.ID_SEND_MESSAGE
msg_followup = ViewButton.Followup('This message is hidden!', ephemeral=True)
menu.add_button(ViewButton(style=discord.ButtonStyle.green, label='Message', custom_id=ViewButton.ID_SEND_MESSAGE, followup=msg_followup))

# ViewButton.ID_CUSTOM_EMBED
custom_embed_button = ViewButton(style=discord.ButtonStyle.blurple, label='Social Media Info', custom_id=ViewButton.ID_CUSTOM_EMBED, followup=ViewButton.Followup(embed=discord.Embed(...)))
```
---
> **NOTE:** When it comes to buttons with a `custom_id` of `ViewButton.ID_CALLER`, `ViewButton.ID_SEND_MESSAGE`, `ViewButton.ID_CUSTOM_EMBED`, or link buttons, you can add as many as you'd like as long as in total it's 25 buttons or less. For all other button ID's, each menu can only have one.

### Updating ViewButton and Pages
* Associated methods
  * `await ViewMenu.refresh_menu_buttons()`
  * `await ViewMenu.update(*, new_pages: Union[List[Union[Embed, str]], None], new_buttons: Union[List[ViewButton], None])`

When the menu is running, you can update the pages or buttons on the menu. Using `ViewMenu.update()`, you can replace the pages and buttons. Using `ViewMenu.refresh_menu_buttons()` updates the buttons you have changed.

#### Updating a Button
```py
@bot.command()
async def menu(ctx):
    menu = ViewMenu(..., name='test')
    link_button = ViewButton(..., label='Link')
    
    menu.add_button(link_button)
    menu.add_page(...)

    await menu.start()


@bot.command()
async def disable(ctx):
    menu = ViewMenu.get_session('test')
    link_button = menu[0].get_button('Link', search_by='label')
    
    menu.disable_button(link_button)
    await menu.refresh_menu_buttons()
```
If the buttons are not refreshed with `ViewMenu.refresh_menu_buttons()`, the menu will not be updated when changing a button.

#### Updating Pages and Buttons
Method `ViewMenu.update(...)` is used when you want to replace all or a few of the buttons on the menu. 
```py
menu = ViewMenu(...)

# in a different .command()
await menu.update(new_pages=[hello_embed, goodbye_embed], new_buttons=[link_button, next_button])
```

> **NOTE**: When using `ViewMenu.update(...)`, there is no need to use `ViewMenu.refresh_menu_buttons()` because they are updated during the update call. 

---
#### ViewButton Methods
The `ViewButton` class comes with a set factory methods (class methods) that returns a `ViewButton` with parameters set according to their `custom_id` (excluding link buttons).

* `ViewButton.link(label: str, url: str)`
  * `style`: `discord.ButtonStyle.link`
  * `label`: `<label>`
  * `url`: `<url>`
* `ViewButton.back()`
  * `style`: `discord.ButtonStyle.gray`
  * `label`: "Back"
  * `custom_id`: `ViewButton.ID_PREVIOUS_PAGE`
* `ViewButton.next()`
	* `style`: `discord.ButtonStyle.gray`
	* `label`: "Next"
	* `custom_id`: `ViewButton.ID_NEXT_PAGE`
* `ViewButton.go_to_first_page()`
	* `style`: `discord.ButtonStyle.gray`
	* `label`: "First Page"
	* `custom_id`: `ViewButton.ID_GO_TO_FIRST_PAGE`
* `ViewButton.go_to_last_page()`
	* `style`: `discord.ButtonStyle.gray`
	* `label`: "Last Page"
	* `custom_id`: `ViewButton.ID_GO_TO_LAST_PAGE`
* `ViewButton.go_to_page()`
	* `style`: `discord.ButtonStyle.gray`
	* `label`: "Page Selection"
	* `custom_id`: `ViewButton.ID_GO_TO_PAGE`
* `ViewButton.end_session()`
	* style: `discord.ButtonStyle.gray`
	* label: "Close"
	* custom_id: `ViewButton.ID_END_SESSION`
* `ViewButton.all()`
  * Returns a `list` of `ViewButton` in the following order
  * `.go_to_first_page()` `.back()` `.next()` `.go_to_last_page()` `.go_to_page()` `.end_session()`
* `ViewButton.skip(label: str, action: str, amount: int)`
  * `style`: `discord.ButtonStyle.gray`
  * `label`: `<label>`
  * `custom_id`: `ViewButton.ID_SKIP`

```py
menu = ViewMenu(ctx, ...)
menu.add_page(...)
menu.add_page(...)

menu.add_button(ViewButton.back())
menu.add_button(ViewButton.next())

await menu.start()
```
---
### ViewButton Events
You can set a `ViewButton` to be disabled or removed when it has been pressed a certain amount of times

```
class ViewButton.Event(event_type: str, value: int)
```

#### Parameters for ViewButton.Event
* `event_type` (`str`) The action to take. Can either be "disable" or "remove"
* `value` (`int`) The amount set for the specified event. Must be >= 1. If value is <= 0, it is implicitly set to 1

Example:
```py
menu = ViewMenu(ctx, ...)

# disable a button after 5 clicks
button_1 = ViewButton(..., event=ViewButton.Event('disable', 5))
menu.add_button(button_1)

# remove a button after 10 clicks
button_2 = ViewButton(..., event=ViewButton.Event('remove', 10))
menu.add_button(button_2)
```
> **NOTE:** Not valid for link buttons. Also not ideal for buttons with a `custom_id` of `ViewButton.ID_END_SESSION`
---
### ViewMenu Relays
Menu relays are functions that are called anytime a button that is apart of a menu is pressed. It is considered as an extension of a `ViewButton` with an ID of `ViewButton.ID_CALLER`. Unlike caller buttons which provides no details about the interactions on the menu, relays do.
* Associated methods
  * `ViewMenu.set_relay(func: Callable[[NamedTuple], None], *, only: List[ViewButton]=None)`
  * `ViewMenu.remove_relay()`

When creating a function for your relay, that function must contain a single positional argument. When a button is pressed, a `RelayPayload` object (a named tuple) is passed to that function. The attributes of `RelayPayload` are:
* `member` (`discord.Member`) The person who pressed the button
* `button` (`ViewButton`) The button that was pressed

Example:
```py
async def enter_giveaway(payload):
    member = payload.member
    channel = payload.button.menu.message.channel
    await channel.send(f"{member.mention}, you've entered the giveaway!")

menu = ViewMenu(ctx, ...)
menu.set_relay(enter_giveaway)
```
The `set_relay` method comes with the `only` parameter. If that parameter is `None`, all buttons that are pressed will be relayed (except link buttons because they don't send interaction events). You can provide a `list` of buttons to that parameter so only button presses from those specified buttons will be relayed.
```py
def example(payload):
    ...

menu = ViewMenu(ctx, ...)

back_button = ViewButton.back()
next_button = ViewButton.next()

menu.set_relay(example, only=[back_button])
```

---
### Starting/Stopping the ViewMenu
* Associated methods
  * `await ViewMenu.start(*, send_to=None, reply=False)`
  * `await ViewMenu.stop(*, delete_menu_message=False, remove_buttons=False, disable_buttons=False)`

When starting the menu, you have the option to send the menu to a certain channel. Parameter `send_to` is the channel you'd like to send the menu to. You can set `send_to` as the channel name (`str`), channel ID (`int`), or channel object (`discord.TextChannel`). Example:
```py
menu = ViewMenu(...)
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

### Full Example
Here is a basic implementation of `ViewMenu` that you can copy & paste for a quick demonstration.
```py
import discord
from discord.ext import commands
from reactionmenu import ViewMenu, ViewButton

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.command()
async def example(ctx):
    menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)
    
    for member in ctx.guild.members:
        if member.avatar:
            embed = discord.Embed(description=f'Joined {member.joined_at.strftime("%b. %d, %Y")}')
            embed.set_author(name=member.name, icon_url=member.avatar.url)
            menu.add_page(embed)
    
    menu.add_button(ViewButton.back())
    menu.add_button(ViewButton.next())
    menu.add_button(ViewButton.end_session())
    
    await menu.start()

bot.run(...)
```
