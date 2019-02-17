# pyInstaParser
[![MIT license](https://img.shields.io/badge/license-MIT-blue.svg)](
https://github.com/OlegYurchik/InstaParser/blob/master/LICENSE)
[![built with Python3](https://img.shields.io/badge/built%20with-Python3-red.svg)](
https://www.python.org/)
[![paypal](https://img.shields.io/badge/-PayPal-blue.svg)](
https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=YHRDQM5C3MJ3U)

### Important Message

I want to create pyInstaParser with async code. Do you need it? If you have any minds about it, please, tell me it in https://github.com/OlegYurchik/pyInstaParser/issues/35

### What's new?

* Version 1.1
* Add new method for AgentAccount - stories(). This method return all stories from account's feed.
* New entity - Story
* Now Media entities have new fields: resources, album and is_album. Media resources - it is all
resources for this post with different dimensions. is_album - is this post is album? Album - it is
all media is this album (if this post is album).
* Add new test for getting stories

### Description
This is a simple and easy-to-use library for interacting with the Instagram. The library works
through the web interface of the Instagram and does not depend on the official API

User Guide
=================

* [Getting Started](#getting-started)
  * [Basic Installation](#basic-installation)
  * [Installation via Virtualenv](#installation-via-virtualenv)
* [Quick Start](#quick-start)
* [Entities](#entities)
  * [Account](#account)
  * [Media](#media)
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
1. git clone https://github.com/olegyurchik/pyInstaParser.git
2. cd pyInstaParser
3. pip install .
or
3. python setup.py install
``` 

## Installation via Virtualenv

To installation via Virtualenv, you should have git, python3 (prefer python3.6 or later), pip
(optionally) and virtualenv in your system

```bash
1. git clone https://github.com/olegyurchik/pyInstaParser.git
2. cd pyInstaParser
3. source venv/bin/activate
4. pip install .
or
4. python setup.py install
5. deactivate
```

## Quick Start

After installation, you can use the library in your code. Below is a sneak example of using the
library

```python3
from instaparser.agents import Agent
from instaparser.entities import Account, Media

agent = Agent()
account = Account("zuck")

media1, pointer = agent.get_media(account)
media2, pointer = agent.get_media(account, count=50, pointer=pointer)
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
from instaparser.entities import Account, Media, Story, Location, Tag, Comment

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
from instaparser.entities import Account

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
* login
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

The Tag object has the following fields:
* id
* media
* owner
* text
* created_at

## Agents

An agent is an object that produces all actions with Instagram. The agent can be **anonymous** and
**authorized**

Each method of agents can take a "setting" argument, which is a dictionary and contains the
necessary settings for connecting to the Internet and instagram. The dictionary with the settings
is directly passed to the request method of the "requists" library, so it is necessary to specify
the settings in the format in which their methods of "requests" are accepted

## Anonymous agent

or simple agent - agent that does not require authorization to work with Instagram. In contrast to
the authorized agent has some limitations

You can create anonymous agent as follows

```python3
from instaparser.agents import Agent

agent = Agent()
```

What anonymous agent can do?

* update(self, obj=None, settings={})

This method updates the information about the transferred entity

obj - entity for updating (Account, Media, Location, Tag)

settings - dict with settings for connection

* get_media(self, obj, pointer=None, count=12, settings={}, limit=50)

This metod return list of entity media and pointer for next page with medias

obj - entity (Account, Location, Tag)

pointer - pointer for next page with medias

count - number of last media records

settings - dict with settings for connection

limit - limit of medias in one request

* get_likes(self, media, settings={})

This metod return list of media likes

media - media entity

settings - dict with settings for connection

* get_comments(self, media, pointer=None, count=35, settings={}, limit=50)

This metod return list of media comments and pointer for next page with comments

media - media entity

pointer - pointer for next page with comments

count - number of last comments records

settings - dict with settings for connection

limit - limit of comments in one request

## Authorized agent

Agent who requires authorization for login and password for work

You can create authorized agent as follows

```python3
from instaparser.agents import Agent

agent = AgentAccount("username", "password")
```

What authorized agent can do?

* update(self, obj=None, settings={})

This method updates the information about the transferred entity

obj - entity for updating (Account, Media, Location, Tag)

settings - dict with settings for connection

* get_media(self, obj, pointer=None, count=12, settings={}, limit=12)

This metod return list of entity media and pointer for next page with medias

obj - entity (Account, Location, Tag)

pointer - pointer for next page with medias

count - number of last media records

settings - dict with settings for connection

limit - limit of medias in one request

* get_likes(self, media, pointer=None, count=20, settings={}, limit=50)

This metod return list of media likes and pointer for next page with likes

media - media entity

pointer - pointer for next page with likes

count - number of last likes records

settings - dict with settings for connection

limit - limit of likes in one request

* get_follows(self, account=None, pointer=None, count=20, settings={}, limit=50)

This metod return list of account follows and pointer for next page with follows

account - account entity

pointer - pointer for next page with follows

count - number of last follows records

settings - dict with settings for connection

limit - limit of follows in one request

* get_followers(self, account=None, pointer=None, count=20, settings={}, limit=50)

This metod return list of followers follows and pointer for next page with followers

account - account entity

pointer - pointer for next page with followers

count - number of last followers records

settings - dict with settings for connection

limit - limit of followers in one request

* feed(self, pointer=None, count=12, settings={}, limit=50)

This metod return feed and pointer for next page

pointer - pointer for next page

count - number of last records

settings - dict with settings for connection

limit - limit of medias in one request

* stories(self, settings={})

This method return all stories in feed

settings - dict with settings for connection

* like(self, media, settings={})

This method like media

media - media entity

settings - dict with settings for connection

* unlike(self, media, settings={})

This method unlike media

media - media entity

settings - dict with settings for connection

* add_comment(self, media, text, settings={})

This method create a comment under media

media - media entity

text - text for comment

settings - dict with settings for connection

* delete_comment(self, comment, settings={})

This method delete a comment

comment - comment for deleting

settings - dict with settings for connection

* follow(self, account, settings={})

This method follow to user

account - account for following

settings - dict with settings for connection

* unfollow(self, account, settings={})

This method unfollow to user

account - account for unfollowing

settings - dict with settings for connection

## Exception handler

## Examples

Any useful examples with InstaParser

* Parsing all photos from feed (the method is suitable for all list structures)

```python3
from instaparser.agents import AgentAccount
from instaparser.entities import Media

photos = []
agent = AgentAccount("username", "password")

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
from instaparser.agents import Agent

settings = {"proxies": {"any_ip": any_port}}

agent = Agent(settings=settings)
```

* Change http handler

```python3
from instaparser.agents import Agent, exception_handler
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

You can run the tests in the following ways:

1. PyTest from OS

```bash
py.test -v -s "tests/entities.py" "tests/anon.py" "tests/auth.py"
```

2. PyTest from Virtualenv

```bash
source VENV/bin/activate
py.test -v -s "tests/entities.py" "tests/anon.py" "tests/auth.py"
deactivate
```

For testing in the folder "tests", you need to create a config.json file, the template file is also
located in the folder "tests" - .config.json

You can also test the library for syntax errors using PyLint. I do not know how to solve some
problems that the PyLint gives out, and I will be glad if you will offer possible solutions

1. PyLint from OS

```bash
files=$(find "$src_dir" -name "*.py")
IFS="
"
for file in ${files[@]}
do
    pylint "$file"
done
```

2. PyLint from Virtualenv

```bash
source VENV/bin/activate
files=$(find "$src_dir" -name "*.py")
IFS="
"
for file in ${files[@]}
do
    pylint "$file"
done
deactivate
```
 
## Contribute repo

Also you can add a new feature and send it using the requester pool

## Donate 

A win-win option is to send me a couple of cents for a cup of coffee
