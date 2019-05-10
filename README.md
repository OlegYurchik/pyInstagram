# pyInstagram
[![MIT license](https://img.shields.io/badge/license-MIT-blue.svg)](
https://github.com/OlegYurchik/InstaParser/blob/master/LICENSE)
[![built with Python3](https://img.shields.io/badge/built%20with-Python3-red.svg)](
https://www.python.org/)
[![paypal](https://img.shields.io/badge/-PayPal-blue.svg)](
https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=YHRDQM5C3MJ3U)

### What's new?
* Version 2.1
* Add logger
* Add new methods for handle geolocation verify 
* Fix bugs
### Description
This is a simple and easy-to-use library for interacting with the Instagram. The library works
through the web interface of the Instagram and does not depend on the official API

User Guide
=================

* [Getting Started](#getting-started)
  * [Basic Installation](#basic-installation)
* [Quick Start](#quick-start)
* [Entities](#entities)
  * [Account](#account)
  * [Media](#media)
  * [Story](#story)
  * [Location](#location)
  * [Tag](#tag)
  * [Comment](#comment)
* [Agents](#agents)
  * [Anonymous agent](#anonymous-agent)
  * [Authorized agent](#authorized-agent)
* [Exception Handler](#exception-handler)
* [Examples](#examples)
* [Help the author](#help-the-author)
  * [Test the library](#test-the-library)
  * [Contribute repo](#contribute-repo)
  * [Donate](#donate)
## Getting Started
## Basic Installation
To basic installation you should have git, python3 (prefer python3.6 or later), pip (optionally) in
your system
```bash
1. git clone https://github.com/olegyurchik/pyInstagram.git
2. cd pyInstagram
3. pip install .
or
3. python setup.py install
```
## Quick Start
After installation, you can use the library in your code. Below is a sneak example of using the
library
```python3
from instagram import Account, Media, WebAgent

agent = WebAgent()
account = Account("zuck")

media1, pointer = agent.get_media(account)
media2, pointer = agent.get_media(account, pointer=pointer, count=50, delay=1)
```
This code allows you to download brief information about the first media from Mark Zuckerberg's
public page in the Instagram
## Entities
All the entities in the Instagram were represented in the library as:
1. Account
2. Media
3. Story
4. Location
5. Tag
6. Comment

Each entity has a unique key:
* **Account** - **username**
* **Media** - **code**
* **Story** - **id**
* **Location** - **id**
* **Tag** - **name**
* **Comment** - **id**

Below is an example of creating all entities
```python3
from instagram import Account, Media, Story, Location, Tag, Comment

account = Account("zuck")
media = Media("Bk09NSFn3IX")
story = Story(54312313)
location = Location(4132822)
tag = Tag("instagram")
comment = Comment(17961800224030417, media=media, owner=account,  text="Nice pic Yaz...",
                  created_at=1531512139)
```
Do not be afraid to create entities with the same keys, so each key belongs to only one object and
it can not be broken
```python3
from instagram import Account

a = Account("test")
b = Account("test")
print(a is b) # True
```
## Account
To create an Account entity as an argument, the constructor should pass the user name
```python3
account = Account("zuck")
```
The Account object has the following fields:
* id
* username
* full_name
* profile_pic_url
* profile_pic_url_hd
* fb_page
* biography
* follows_count
* followers_count
* media_count
* is_private
* is_verified
* country_block
* media
* follows
* followers
## Media
To create an Media entity as an argument, the constructor should pass the shortcode
```python3
media = Media("Bk09NSFn3IX")
```
The Media object has the following fields:
* id
* code
* caption
* owner
* date
* location
* likes_count
* comments_count
* comments_disabled
* is_video
* video_url
* is_ad
* display_url
* is_album
* resources
* album
* likes
* comments
## Story
To create an Story entity as an argument constructor should pass the story's id
```python3
story = Story(1234124)
```
The Story object has the following fields:
* id
## Location
To create an Location entity as an argument, the constructor should pass the id
```python3
location = Location(4132822)
```
The Location object has the following fields:
* id
* slug
* name
* has_public_page
* directory
* coordinates
* media_count
* media
* top_posts
## Tag
To create an Tag entity as an argument, the constructor should pass the name
```python3
tag = Tag("instagram")
```
The Tag object has the following fields:
* name
* media_count
* media
* top_posts
## Comment
To create an Comment entity as an argument, the constructor should pass the id, Media object, owner
(Account object), text and created time in unix format
```python3
comment = Comment(18019322278024340, media=media, owner=account, text="It is a comment",
                  created_at=1546548300)
```
The Comment object has the following fields:
* id
* media
* owner
* text
* created_at
## Agents
An agent is an object that produces all actions with Instagram. The agent can be **anonymous** and
**authorized**

Each agent method can take a "settings" argument, which is a dictionary and contains the necessary
settings for connecting to the Internet and Instagram. In the "settings" dictionary, you can
directly specify the parameters for the "requests" library requests, if you use WebAgent and
WebAgentAccount, or for the requests of the "aiohttp" library, if you use AsyncWebAgent and
AsyncWebAgentAccount.
## Anonymous agent
or simple agent - agent that does not require authorization to work with Instagram. In contrast to
the authorized agent has some limitations

You can create simple anonymous agent as follows
```python3
from instagram import WebAgent

agent = WebAgent()
```
Or asyncio simple anonymous agent as follows
```python3
from instagram import AsyncWebAgent

agent = AsyncWebAgent()
```
What anonymous agent can do?

**__init__(self, cookies=None, logger=None)**

It is agent constructor:
* cookies - cookies, if you want continue last session
* logger - logger from library "logging" for logging any actions

**update(self, obj=None, settings=None)**

This method updates the information about the transferred entity:
* obj - entity for updating (Account, Media, Location, Tag)
* settings - dict with settings for connection

**get_media(self, obj, pointer=None, count=12, limit=50, delay=0, settings=None)**

This metod return list of entity media and pointer for next page with medias:
* obj - entity (Account, Location, Tag)
* pointer - pointer for next page with medias
* count - number of last media records
* limit - limit of medias in one request
* delay - delay between requests
* settings - dict with settings for connection

**get_likes(self, media, pointer=None, count=20, limit=50, delay=0, settings=None)**

This metod return list of media likes:
* media - media entity
* pointer - pointer for next page with likes
* count - number of last like records
* limit - limit of likes in one request
* delay - delay between requests
* settings - dict with settings for connection

**get_comments(self, media, pointer=None, count=35, limit=32, settings=None)**

This metod return list of media comments and pointer for next page with comments:
* media - media entity
* pointer - pointer for next page with comments
* count - number of last comments records
* delay - delay between requests
* limit - limit of comments in one request
* settings - dict with settings for connection
## Authorized agent
Agent who requires authorization for login and password for work

You can create simple authorized agent as follows
```python3
from instagram import WebAgentAccount

agent = WebAgentAccount("username")
```
or asyncio authorized agent as follows
```python3
from instagram inport AsyncWebAgentAccount

agent = AsyncWebAgentAccount("username")
```
What authorized agent can do?

**__init__(self, username, cookies=None, logger=None)**

It is agent constructor:
* username - account username which agent will use
* cookies - cookies, if you want continue last session
* logger - logger from library "logging" for logging any actions

**auth(self, password, settings=None)**

Method for sign in agent in Instagram:
* password - password for account
* settings - dict with settings for connection

**checkpoint_handle(self, url, settings=None)**

This method receives all the information from the account verification page, which the agent
receives if the Instagram does not allow you to log in and requires confirmation:
* url - url with checkpoint page
* settings - dict with settings for connection

**checkpoint_send(self, checkpoint_url, forward_url, choice, settings=None)**

This method asks for verification code:
* checkpoint_url - url with checkpoint page
* forward_url - url with page for entering code
* choice - where are you want to get code
* settings - dict with settings for connection

**checkpoint_replay(self, forward_url, replay_url, settings=None)**

This method resend verification code:
* forward_url - url with page for entering code
* replay_url - url with page for resend code
* settings - dict with settings for connection

**checkpoint(self, url, code, settings=None)**

This method enter code for verification auth:
* url - url for entering code
* code - recived code
* settings - dict with settings for connection

**update(self, obj=None, settings=None)**

This method updates the information about the transferred entity:
* obj - entity for updating (Account, Media, Location, Tag)
* settings - dict with settings for connection

**get_media(self, obj, pointer=None, count=12, limit=12, delay=0, settings=None)**

This metod return list of entity media and pointer for next page with medias:
* obj - entity (Account, Location, Tag)
* pointer - pointer for next page with medias
* count - number of last media records
* limit - limit of comments in one request
* delay - delay between requests
* settings - dict with settings for connection

**get_follows(self, account=None, pointer=None, count=20, limit=50, delay=0, settings=None)**

This metod return list of account follows and pointer for next page with follows:
* account - account entity
* pointer - pointer for next page with follows
* count - number of last follows records
* limit - limit of follows in one request
* delay - delay between requests
* settings - dict with settings for connection

**get_followers(self, account=None, pointer=None, count=20, limit=50, delay=0, settings=None)**

This metod return list of followers follows and pointer for next page with followers:
* account - account entity
* pointer - pointer for next page with followers
* count - number of last followers records
* limit - limit of followers in one request
* delay - delay between requests
* settings - dict with settings for connection

**stories(self, settings=None)**

This method return all stories in feed:
* settings - dict with settings for connection

**feed(self, pointer=None, count=12, limit=50, delay=0, settings=None)**

This metod return feed and pointer for next page:
* pointer - pointer for next page
* count - number of last records
* limit - limit of followers in one request
* delay - delay between requests
* settings - dict with settings for connection

**like(self, media, settings=None)**

This method like media:
* media - media entity
* settings - dict with settings for connection

**unlike(self, media, settings=None)**

This method unlike media:
* media - media entity
* settings - dict with settings for connection

**add_comment(self, media, text, settings=None)**

This method create a comment under media:
* media - media entity
* text - text for comment
* settings - dict with settings for connection

**delete_comment(self, comment, settings=None)**

This method delete a comment:
* comment - comment for deleting
* settings - dict with settings for connection

**follow(self, account, settings=None)**

This method follow to user:
* account - account for following
* settings - dict with settings for connection

**unfollow(self, account, settings=None)**

This method unfollow to user:
* account - account for unfollowing
* settings - dict with settings for connection
## Exception handler
## Examples
Any useful examples with pyInstagram

* Parsing all photos from feed (the method is suitable for all list structures)
```python3
from instagram import WebAgentAccount, Media

photos = []
agent = WebAgentAccount("username")
agent.auth("password")

medias, pointer = agent.feed()
for media in medias:
    if not media.is_video:
        photos.append(media.display_url)

while not pointer is None:
    medias, pointer = agent.feed(pointer=pointer)
    for media in medias:
        if not media.is_video:
            photos.append(media.display_url)
```
* Use proxy
```python3
from instagram import WebAgent

settings = {
    "proxies": {
        "http": "http://example.net:8888",
        "https": "https://example.net:8888",
    },
}

agent = WebAgent()
agent.update(settings=settings)
```
* Change http handler
```python3
from instagram import WebAgent, exception_handler
from requests.exceptions import HTTPError

def handler(exception, *args, **kwargs):
    print("I think it is not a critical error. Maybe, try again with new parameters?")
    args.append("It is new parameter")
    return (args, kwargs)

exception_handler[HTTPError] = handler
```
## Help the author
You can help me in three ways:
## Test the library
You can test the library using tests that are in the repository in the "tests" folder. Testing is
done using **PyTest**. 

You can run the tests like that:
```bash
py.test --random-order -v "tests/entities.py" "tests/anon.py" "tests/auth.py"
```
For testing in the folder "tests", you need to create a config.json file, the template file is also
located in the folder "tests" - .config.json

You can also test the library for syntax errors using PyLint. I do not know how to solve some
problems that the PyLint gives out, and I will be glad if you will offer possible solutions
```bash
files=$(find "$src_dir" -name "*.py")
IFS="
"
for file in ${files[@]}
do
    pylint "$file"
done
``` 
## Contribute repo
Also you can add a new feature and send it using the requester pull
## Donate 
A win-win option is to send me a couple of cents for a cup of coffee
[![paypal](https://img.shields.io/badge/-PayPal-blue.svg)](
https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=YHRDQM5C3MJ3U)
