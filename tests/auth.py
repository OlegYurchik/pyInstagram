import pytest
from random import randint, choice

from instaparser.agents import AgentAccount, AsyncAgentAccount
from instaparser.entities import Account, Comment, Location, Media, Story, Tag

from tests.settings import accounts, creds, locations, photos, photo_sets, tags, videos



def parametrize(*args):
    result = []
    for variable in zip(*args):
        result.append((creds["login"], creds["password"], *variable))
    return result



@pytest.mark.parametrize("login,password", [(creds["login"], creds["password"])])
def test_auth(login, password):
    AgentAccount(login, password)
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password", [(creds["login"], creds["password"])])
@pytest.mark.asyncio
async def test_async_auth(event_loop, login, password):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password", [(creds["login"], creds["password"])])
def test_update(login, password):
    agent = AgentAccount(login, password)
    
    agent.update()
    
    assert not getattr(agent, "id") is None
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password", [(creds["login"], creds["password"])])
@pytest.mark.asyncio
async def test_async_update(event_loop, login, password):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    
    await agent.update()
    
    assert not getattr(agent, "id") is None
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password,username", parametrize(accounts))
def test_update_account(login, password, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    
    data = agent.update(account)
    
    assert not data is None
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password,username", parametrize(accounts))
@pytest.mark.asyncio
async def test_async_update_account(event_loop, login, password, username):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    account = Account(username)

    data = await agent.update(account)
    
    assert not data is None
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photos))
def test_update_photo(login, password, shortcode):
    agent = AgentAccount(login, password)
    photo = Media(shortcode)

    agent.update(photo)

    assert not photo.is_video

    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photos))
@pytest.mark.asyncio
async def test_async_update_photo(event_loop, login, password, shortcode):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    photo = Media(shortcode)

    await agent.update(photo)

    assert not photo.is_video

    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photo_sets))
def test_update_photo_set(login, password, shortcode):
    agent = AgentAccount(login, password)
    photo_set = Media(shortcode)
    
    agent.update(photo_set)
    
    assert not photo_set.is_video
    
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photo_sets))
@pytest.mark.asyncio
async def test_async_update_photo_set(event_loop, login, password, shortcode):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    photo_set = Media(shortcode)
    
    await agent.update(photo_set)
    
    assert not photo_set.is_video
    
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(videos))
def test_update_video(login, password, shortcode):
    agent = AgentAccount(login, password)
    video = Media(shortcode)
    
    agent.update(video)
    
    assert video.is_video
    
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(videos))
@pytest.mark.asyncio
async def test_async_update_video(event_loop, login, password, shortcode):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    video = Media(shortcode)
    
    await agent.update(video)
    
    assert video.is_video
    
    Media.clear_cache()


@pytest.mark.parametrize("login,password,id", parametrize(locations))
def test_update_location(login, password, id):
    agent = AgentAccount(login, password)
    location = Location(id)
    
    agent.update(location)
    
    Location.clear_cache()


@pytest.mark.parametrize("login,password,id", parametrize(locations))
@pytest.mark.asyncio
async def test_async_update_location(event_loop, login, password, id):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    location = Location(id)
    
    await agent.update(location)
    
    Location.clear_cache()


@pytest.mark.parametrize("login,password,name", parametrize(tags))
def test_update_tag(login, password, name):
    agent = AgentAccount(login, password)
    tag = Tag(name)
    
    agent.update(tag)
    
    Tag.clear_cache()


@pytest.mark.parametrize("login,password,name", parametrize(tags))
@pytest.mark.asyncio
async def test_async_update_tag(event_loop, login, password, name):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    tag = Tag(name)
    
    await agent.update(tag)
    
    Tag.clear_cache()


@pytest.mark.parametrize("login,password,count,username",
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(accounts) for i in range(3)]))
def test_get_media_account(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    
    data, pointer = agent.get_media(account, count=count)

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,username",
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(accounts) for i in range(3)]))
@pytest.mark.asyncio
async def test_async_get_media_account(event_loop, login, password, count, username):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    account = Account(username)
    
    data, pointer = await agent.get_media(account, count=count)

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,id", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(locations) for i in range(3)]))
def test_get_media_location(login, password, count, id):
    agent = AgentAccount(login, password)
    location = Location(id)
    
    data, pointer = agent.get_media(location, count=count)

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,id", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(locations) for i in range(3)]))
@pytest.mark.asyncio
async def test_async_get_media_location(event_loop, login, password, count, id):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    location = Location(id)
    
    data, pointer = await agent.get_media(location, count=count)

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,name", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(tags) for i in range(3)]))
def test_get_media_tag(login, password, count, name):
    agent = AgentAccount(login, password)
    tag = Tag(name)
    
    data, pointer = agent.get_media(tag, count=count)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,name", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(tags) for i in range(3)]))
@pytest.mark.asyncio
async def test_async_get_media_tag(event_loop, login, password, count, name):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    tag = Tag(name)
    
    data, pointer = await agent.get_media(tag, count=count)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,shortcode",
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(photos+photo_sets+videos)]))
def test_get_likes(login, password, count, shortcode):
    agent = AgentAccount(login, password)
    media = Media(shortcode)
    
    data, pointer = agent.get_likes(media, count=count)
    
    assert min(media.likes_count, count) == len(data)
    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,shortcode",
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(photos+photo_sets+videos)]))
@pytest.mark.asyncio
async def test_async_get_likes(event_loop, login, password, count, shortcode):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    media = Media(shortcode)
    
    data, pointer = await agent.get_likes(media, count=count)
    
    assert min(media.likes_count, count) == len(data)
    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(accounts) for i in range(3)]))
def test_get_follows(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    
    data, pointer = agent.get_follows(account, count=count)

    assert min(account.follows_count, count) == len(data)
    assert (pointer is None) == (account.follows_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(accounts) for i in range(3)]))
@pytest.mark.asyncio
async def test_async_get_follows(event_loop, login, password, count, username):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    account = Account(username)
    
    data, pointer = await agent.get_follows(account, count=count)

    assert min(account.follows_count, count) == len(data)
    assert (pointer is None) == (account.follows_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(accounts) for i in range(3)]))
def test_get_followers(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    
    data, pointer = agent.get_followers(account, count=count)

    assert min(account.followers_count, count) == len(data)
    assert (pointer is None) == (account.followers_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(accounts) for i in range(3)]))
@pytest.mark.asyncio
async def test_async_get_followers(event_loop, login, password, count, username):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    account = Account(username)
    
    data, pointer = await agent.get_followers(account, count=count)

    assert min(account.followers_count, count) == len(data)
    assert (pointer is None) == (account.followers_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count", parametrize([randint(100, 500) for i in range(3)]))
def test_get_feed(login, password, count):
    agent = AgentAccount(login, password)
    
    data, _ = agent.feed(count=count)

    assert count >= len(data)
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password,count", parametrize([randint(100, 500) for i in range(3)]))
@pytest.mark.asyncio
async def test_async_get_feed(event_loop, login, password, count):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    
    data, _ = await agent.feed(count=count)

    assert count >= len(data)
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password", [(creds["login"], creds["password"])])
def test_get_stories(login, password):
    agent = AgentAccount(login, password)

    agent.stories()

    Account.clear_cache()
    Story.clear_cache()


@pytest.mark.parametrize("login,password", [(creds["login"], creds["password"])])
@pytest.mark.asyncio
async def test_async_get_stories(event_loop, login, password):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)

    await agent.stories()

    Account.clear_cache()
    Story.clear_cache()


@pytest.mark.parametrize("login,password,count,username",
                         parametrize([randint(1, 10)], [choice(accounts)]))
def test_get_media_account_pointer(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent.get_media(account, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,username",
                         parametrize([randint(1, 10)], [choice(accounts)]))
@pytest.mark.asyncio
async def test_async_get_media_account_pointer(event_loop, login, password, count, username):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await agent.get_media(account, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,id", 
                         parametrize([randint(1, 10)], [choice(locations)]))
def test_get_media_location_pointer(login, password, count, id):
    agent = AgentAccount(login, password)
    location = Location(id)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent.get_media(location, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (location.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()
    Location.clear_cache()


@pytest.mark.parametrize("login,password,count,id", 
                         parametrize([randint(1, 10)], [choice(locations)]))
@pytest.mark.asyncio
async def test_async_get_media_location_pointer(event_loop, login, password, count, id):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    location = Location(id)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await agent.get_media(location, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (location.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()
    Location.clear_cache()


@pytest.mark.parametrize("login,password,count,name", 
                         parametrize([randint(1, 10)], [choice(tags)]))
def test_get_media_tag_pointer(login, password, count, name):
    agent = AgentAccount(login, password)
    tag = Tag(name)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent.get_media(tag, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (tag.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()
    Tag.clear_cache()


@pytest.mark.parametrize("login,password,count,name", 
                         parametrize([randint(1, 10)], [choice(tags)]))
@pytest.mark.asyncio
async def test_async_get_media_tag_pointer(event_loop, login, password, count, name):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    tag = Tag(name)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await agent.get_media(tag, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (tag.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()
    Tag.clear_cache()


@pytest.mark.parametrize("login,password,count,shortcode",
                         parametrize([randint(1, 10)], [choice(photos+photo_sets+videos)]))
def test_get_likes_pointer(login, password, count, shortcode):
    agent = AgentAccount(login, password)
    media = Media(shortcode)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent.get_likes(media, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (media.likes_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,shortcode",
                         parametrize([randint(1, 10)], [choice(photos+photo_sets+videos)]))
@pytest.mark.asyncio
async def test_async_get_likes_pointer(event_loop, login, password, count, shortcode):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    media = Media(shortcode)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await agent.get_likes(media, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (media.likes_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(1, 10)], [choice(accounts)]))
def test_get_follows_pointer(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent.get_follows(account, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (account.follows_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(1, 10)], [choice(accounts)]))
@pytest.mark.asyncio
async def test_async_get_follows_pointer(event_loop, login, password, count, username):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await agent.get_follows(account, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (account.follows_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(1, 10)], [choice(accounts)]))
def test_get_followers_pointer(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent.get_followers(account, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (account.followers_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(1, 10)], [choice(accounts)]))
@pytest.mark.asyncio
async def test_async_get_followers_pointer(event_loop, login, password, count, username):
    agent = AgentAccount()
    await agent.__ainit__(login, password)
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await agent.get_followers(account, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (account.followers_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count", parametrize([randint(1, 10)]))
def test_get_feed_pointer(login, password, count):
    agent = AgentAccount(login, password)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent.feed(pointer=pointer)
        data.extend(tmp)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count", parametrize([randint(1, 10)]))
@pytest.mark.asyncio
async def test_async_get_feed_pointer(event_loop, login, password, count):
    agent = AsycnAgentAccount()
    await agent.__ainit__(login, password)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await agent.feed(pointer=pointer)
        data.extend(tmp)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photos))
def test_like_unlike_photo(login, password, shortcode):
    agent = AgentAccount(login, password)
    photo = Media(shortcode)
    
    assert agent.like(photo)
    assert agent.unlike(photo)
    
    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photos))
@pytest.mark.asyncio
async def test_async_like_unlike_photo(event_loop, login, password, shortcode):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    photo = Media(shortcode)
    
    assert await agent.like(photo)
    assert await agent.unlike(photo)
    
    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photo_sets))
def test_like_unlike_photo_set(login, password, shortcode):
    agent = AgentAccount(login, password)
    photo_set = Media(shortcode)
    
    assert agent.like(photo_set)
    assert agent.unlike(photo_set)
    
    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photo_sets))
@pytest.mark.asyncio
async def test_async_like_unlike_photo_set(login, password, shortcode):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    photo_set = Media(shortcode)
    
    assert await agent.like(photo_set)
    assert await agent.unlike(photo_set)
    
    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(videos))
def test_like_unlike_video(login, password, shortcode):
    agent = AgentAccount(login, password)
    video = Media(shortcode)
    
    assert agent.like(video)
    assert agent.unlike(video)
    
    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(videos))
@pytest.mark.asyncio
async def test_async_like_unlike_video(event_loop, login, password, shortcode):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    video = Media(shortcode)
    
    assert await agent.like(video)
    assert await agent.unlike(video)
    
    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,username", parametrize(accounts))
@pytest.mark.asyncio
async def test_async_follow_unfollow(event_loop, login, password, username):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    account = Account(username)
    
    assert await agent.follow(account)
    assert await agent.unfollow(account)

    Account.clear_cache()


@pytest.mark.parametrize("login,password,shortcode",
                         parametrize([choice(photos), choice(photo_sets), choice(videos)]))
def test_comment(login, password, shortcode):
    agent = AgentAccount(login, password)
    media = Media(shortcode)
    
    comment = agent.add_comment(media, "test")
    agent.delete_comment(comment)
    
    Account.clear_cache()
    Media.clear_cache()
    Comment.clear_cache()


@pytest.mark.parametrize("login,password,shortcode",
                         parametrize([choice(photos), choice(photo_sets), choice(videos)]))
@pytest.mark.asyncio
async def test_async_comment(event_loop, login, password, shortcode):
    agent = AsyncAgentAccount()
    await agent.__ainit__(login, password)
    media = Media(shortcode)

    comment = await agent.add_comment(media, "test")
    await agent.delete_comment(comment)

    Account.clear_cache()
    Media.clear_cache()
    Comment.clear_cache()
