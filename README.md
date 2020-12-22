## How to import
```py
from reactionmenu import ReactionMenu, Button, ButtonType
```
## Showcase
![demo](https://cdn.discordapp.com/attachments/655186216060321816/788099328656801852/demo.gif)

This package comes with several methods and options in order to make a reaction menu simple. Once you have imported the proper classes, you will initialize the constructor like so:
```py
menu = ReactionMenu(ctx, back_button='\U000027a1', next_button='\U00002b05', config=ReactionMenu.STATIC) 
```
---
## Parameters of the ReactionMenu constructor
* `ctx` The `discord.ext.commands.Context` object
* `back_button` Emoji used to go the previous page. 
* `next_button` Emoji used to go to the next page. 
* `config` The config of the menu is important. You have two options when it comes to configuration. 
    * `ReactionMenu.STATIC` (details below)
    * `ReactionMenu.DYNAMIC` (details below)
---
## Options of the ReactionMenu constructor [kwargs]
| Name | Type | Default Value | Used for | Info
|------|------|---------------|----------|-------
| `rows_requested` | `int` |`None` | `ReactionMenu.DYNAMIC` | (details below) 
| `custom_embed` | `discord.Embed` | `None` | `ReactionMenu.DYNAMIC` | (details below)
| `wrap_in_codeblock` | `str` | `None` | `ReactionMenu.DYNAMIC` | (details below)
| `clear_reactions_after` | `bool` | `True` | `STATIC and DYNAMIC` | delete all reactions after the menu ends
| `timeout` | `float` | `60.0` | `STATIC and DYNAMIC` | timer in seconds for when the menu ends
| `show_page_director` | `bool` | `True` | `STATIC and DYNAMIC` | show/do not show the current page on the embed
| `name` | `str` | `None` | `STATIC and DYNAMIC` | name of the menu instance
| `style` | `str` | `Page 1/X` | `STATIC and DYNAMIC` | custom page director style
| `all_can_react` | `bool` | `False` | `STATIC and DYNAMIC` | if all members can navigate the menu or only the message author
> NOTE: All kwargs can also be set using an instance of `ReactionMenu` **except** `rows_requested`
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
menu = ReactionMenu(ctx, back_button='\U000027a1', next_button='\U00002b05', config=ReactionMenu.STATIC)
menu.add_page(greeting_embed)
menu.add_page(goodbye_embed)

# NOTE: it can also be used in a loop
member_details = [] # contains embed objects
for member_embed in member_details:
    menu.add_page(member_embed)
```
##### Deleting Pages
You can delete a single page using `menu.remove_page(3)` or all pages with `menu.clear_all_pages()`. If you have any custom pages (more on that below), you can delete them all with `menu.clear_all_custom_pages()`

## Dynamic
A dynamic menu is used when you do not know how much information will be applied to the menu. For example, if you were to request information from a database, that information can always change. You query something and you might get 1,500 results back, and the next maybe only 800. A dynamic menu pieces all this information together for you and adds it to an embed page by rows of data. `.add_row()` is best used in some sort of `Iterable` where everything can be looped through, but only add the amount of data you want to the menu page
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
menu = ReactionMenu(ctx, back_button='\U000027a1', next_button='\U00002b05', config=ReactionMenu.DYNAMIC)

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
## What are Buttons and ButtonTypes?
Buttons/button types are used when you want to add a reaction to the menu that does a certain function. Buttons and buttons types work together to achieve the desired action.
##### Parameters of the Button constructor
* `emoji` The emoji you would like to use as the reaction
* `linked_to` When the reaction is clicked, this is what determines what it will do (`ButtonType`)
> NOTE: The emoji parameter supports all forms of emojis. You can use the emoji itself, unicode (\U000027a1), or a guild emoji <:miscTwitter:705423192818450453>), etc..
* There are 6 button types
    * `ButtonType.NEXT_PAGE`
    * `ButtonType.PREVIOUS_PAGE`
    * `ButtonType.GO_TO_FIRST_PAGE`
    * `ButtonType.GO_TO_LAST_PAGE`
    * `ButtonType.END_SESSION` 
    * `ButtonType.CUSTOM_EMBED`
##### Options of the Button constructor [kwargs]
| Name | Type | Default Value | Used for
|------|------|---------------|----------
| `name` | `str` |`None` | The name of the button object
| `custom_embed` | `discord.Embed` | `None` | When a reaction is pressed, go to the specifed embed. Seperate from going page-to-page 
---
## Button and ButtonType in detail
* Associated methods
    * `ReactionMenu.add_button(button: Button)`
    * `ReactionMenu.clear_all_buttons()`
    * `ReactionMenu.remove_button(identity: Union[str, Button])`
    * `ReactionMenu.change_appear_order(*emoji_or_button: Union[str, Button])`
    * `ReactionMenu.get_button_by_name(name: str)`
    * `ReactionMenu.help_appear_order()`
##### Adding Buttons
You can add buttons (reactions) to the menu using a `Button`. By default, 2 buttons have already been set in the `ReactionMenu` constructor. The `back_button` as `ButtonType.PREVIOUS_PAGE` and `next_button` as `ButtonType.NEXT_PAGE`. It's up to you if you would like additional buttons. 
```py
first_button = Button(emoji='\U000023ea', linked_to=ButtonType.GO_TO_FIRST_PAGE)
server_details_button = Button(emoji='\N{winking face}', linked_to=ButtonType.CUSTOM_EMBED, embed=info_embed)
close_menu_button = Button(emoji='<:miscRed:694466531098099753>', linked_to=ButtonType.END_SESSION, name='end')

menu.add_button(first_button)
menu.add_button(server_details_button)
menu.add_button(close_menu_button)
```
##### Deleting Buttons
Remove all buttons with `menu.clear_all_buttons()`. You can also remove an individual button using its name if you have it set, or the button object itself with `menu.remove_button()`

##### Emoji Order
It is possible to change the order the reactions appear in on the menu.
```py
first_button = Button(emoji='\U000023ea', linked_to=ButtonType.GO_TO_FIRST_PAGE)
close_menu_button = Button(emoji='<:miscRed:694466531098099753>', linked_to=ButtonType.END_SESSION, name='end')

# NOTE 1: When changing the order, you need to include the default back and next buttons because they are there by default. Access the default back/next buttons with menu attributes
# NOTE 2: You can use the emoji or button object 

menu.change_appear_order(first_button, menu.default_back_button, close_menu_button, menu.default_next_button)
```
If you did not make an instance of a Button object to access, you can still get that button object by its name if it is set. Example: `menu.get_button_by_name('end')`. With the helper function `menu.help_appear_order()`, it simply prints out all active buttons to the console so you can copy and paste each emoji in the order you'd like.

---
## Starting/Stopping the Menu
* Associated Methods
    * `await ReactionMenu.start()`
    * `await ReactionMenu.stop(*, delete_menu_message=False, clear_reactions=False)`

When stopping the menu, you have two options. Delete the reaction menu by setting the first parameter to `True` or only remove all it's reactions, setting the second parameter to `True`

---
#### All Attributes
| Attribute | Return Type | Info 
|-----------|-------------|----------
| `ReactionMenu.config` | `int` | menu config value. 0 = static, 1 = dynamic
| `ReactionMenu.is_running` | `bool` | if the menu is currently active
| `ReactionMenu.default_next_button` | `Button` | default next button (in the constructor)
| `ReactionMenu.default_back_button` | `Button` | default back button (in the constructor)
| `ReactionMenu.next_buttons` | `List[Button]` | all active next buttons
| `ReactionMenu.back_buttons` | `List[Button]` | all active back buttons
| `ReactionMenu.first_page_buttons` | `List[Button]` | all active first page buttons
| `ReactionMenu.last_page_buttons` | `List[Button]` | all active last pages buttons
| `ReactionMenu.end_session_buttons` | `List[Button]` | all active end session buttons
| `ReactionMenu.custom_embed_buttons` | `List[Button]` | all active custum embed buttons
| `ReactionMenu.all_buttons` | `List[Button]` | all active buttons
| `ReactionMenu.rows_requested` | `int` | the amount of rows you have set to request
| `ReactionMenu.timeout` | `float` | value in seconds of when the menu ends
| `ReactionMenu.show_page_director` | `bool` | how/do not show the current page on the embed
| `ReactionMenu.name` | `str` | name of the menu instance
| `ReactionMenu.style` | `str` | custom page director style
| `ReactionMenu.all_can_react` | `bool`  | if all members can navigate the menu or only the message author
| `ReactionMenu.custom_embed` | `discord.Embed` | embed object used for custom pages
| `ReactionMenu.wrap_in_codeblock` | `str` | language identifier when wrapping your data in a discord codeblock
