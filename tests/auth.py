import pytest
from random import randint, choice

from instaparser.agents import AgentAccount, AsyncAgentAccount
from instaparser.entities import Account, Comment, Location, Media, Story, Tag

from tests.settings import accounts, creds, locations, photos, photo_sets, tags, videos


@pytest.fixture
def settings():
    return {"headers": {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101",
    }}


@pytest.fixture
def agent(settings):
    return AgentAccount(creds["login"], creds["password"], settings=settings)


@pytest.fixture
@pytest.mark.asyncio
async def async_agent(settings):
    return await AsyncAgentAccount.create(creds["login"], creds["password"], settings=settings)


def test_auth(agent):
    Account.clear_cache()


@pytest.mark.asyncio
async def test_async_auth(event_loop, async_agent):
    Account.clear_cache()


def test_update(agent, settings):
    agent.update(settings=settings)

    assert not getattr(agent, "id") is None

    Account.clear_cache()


@pytest.mark.asyncio
async def test_async_update(event_loop, async_agent, settings):
    await async_agent.update(settings=settings)

    assert not getattr(async_agent, "id") is None

    Account.clear_cache()


@pytest.mark.parametrize("username", [[account] for account in accounts])
def test_update_account(agent, settings, username):
    account = Account(username)
    
    data = agent.update(account, settings=settings)
    
    assert not data is None
    
    Account.clear_cache()


@pytest.mark.parametrize("username", [[account] for account in accounts])
@pytest.mark.asyncio
async def test_async_update_account(event_loop, async_agent, settings, username):
    account = Account(username)

    data = await async_agent.update(account, settings=settings)

    assert not data is None

    Account.clear_cache()


@pytest.mark.parametrize("shortcode", [[photo] for photo in photos])
def test_update_photo(agent, settings, shortcode):
    photo = Media(shortcode)

    agent.update(photo, settings=settings)

    assert not photo.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [[photo] for photo in photos])
@pytest.mark.asyncio
async def test_async_update_photo(event_loop, async_agent, settings, shortcode):
    photo = Media(shortcode)

    await async_agent.update(photo, settings=settings)

    assert not photo.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [[photo_set] for photo_set in photo_sets])
def test_update_photo_set(agent, settings, shortcode):
    photo_set = Media(shortcode)

    agent.update(photo_set, settings=settings)

    assert not photo_set.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [[photo_set] for photo_set in photo_sets])
@pytest.mark.asyncio
async def test_async_update_photo_set(event_loop, async_agent, settings, shortcode):
    photo_set = Media(shortcode)

    await async_agent.update(photo_set, settings=settings)

    assert not photo_set.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [[video] for video in videos])
def test_update_video(agent, settings, shortcode):
    video = Media(shortcode)

    agent.update(video, settings=settings)

    assert video.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [[video] for video in videos])
@pytest.mark.asyncio
async def test_async_update_video(event_loop, async_agent, settings, shortcode):
    video = Media(shortcode)

    await async_agent.update(video, settings=settings)

    assert video.is_video

    Media.clear_cache()


@pytest.mark.parametrize("id", [[location] for location in locations])
def test_update_location(agent, settings, id):
    location = Location(id)

    agent.update(location, settings=settings)

    Location.clear_cache()


@pytest.mark.parametrize("id", [locations])
@pytest.mark.asyncio
async def test_async_update_location(event_loop, async_agent, settings, id):
    location = Location(id)

    await async_agent.update(location, settings=settings)

    Location.clear_cache()


@pytest.mark.parametrize("name", [tags])
def test_update_tag(agent, settings, name):
    tag = Tag(name)

    agent.update(tag, settings=settings)

    Tag.clear_cache()


@pytest.mark.parametrize("name", [tags])
@pytest.mark.asyncio
async def test_async_update_tag(event_loop, async_agent, settings, name):
    tag = Tag(name)

    await async_agent.update(tag, settings=settings)

    Tag.clear_cache()


@pytest.mark.parametrize(
    "count, username",
    [(randint(100, 500), choice(accounts)) for _ in range(3)],
)
def test_get_media_account(agent, settings, count, username):
    account = Account(username)

    data, pointer = agent.get_media(account, count=count, settings=settings)

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize(
    "count, username",
    [(randint(100, 500), choice(accounts)) for _ in range(3)],
)
@pytest.mark.asyncio
async def test_async_get_media_account(event_loop, async_agent, settings, count, username):
    account = Account(username)

    data, pointer = await async_agent.get_media(account, count=count, settings=settings)

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize(
    "count, id", 
    [(randint(100, 500), choice(locations)) for _ in range(3)],
)
def test_get_media_location(agent, settings, count, id):
    location = Location(id)

    data, pointer = agent.get_media(location, count=count, settings=settings)

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize(
    "count, id", 
    [(randint(100, 500), choice(locations)) for _ in range(3)],
)
@pytest.mark.asyncio
async def test_async_get_media_location(event_loop, async_agent, settings, count, id):
    location = Location(id)

    data, pointer = await async_agent.get_media(location, count=count, settings=settings)

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize(
    "count, name", 
    [(randint(100, 500), choice(tags)) for _ in range(3)],
)
def test_get_media_tag(agent, settings, count, name):
    tag = Tag(name)

    data, pointer = agent.get_media(tag, count=count, settings=settings)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize(
    "count, name", 
    [(randint(100, 500), choice(tags)) for _ in range(3)],
)
@pytest.mark.asyncio
async def test_async_get_media_tag(event_loop, async_agent, settings, count, name):
    tag = Tag(name)

    data, pointer = await async_agent.get_media(tag, count=count, settings=settings)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(100, 500), choice(photos + photo_sets + videos)) for _ in range(3)],
)
def test_get_likes(agent, settings, count, shortcode):
    media = Media(shortcode)

    data, pointer = agent.get_likes(media, count=count, settings=settings)

    assert min(media.likes_count, count) == len(data)
    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(100, 500), choice(photos + photo_sets + videos)) for _ in range(3)],
)
@pytest.mark.asyncio
async def test_async_get_likes(event_loop, async_agent, settings, count, shortcode):
    media = Media(shortcode)

    data, pointer = await async_agent.get_likes(media, count=count, settings=settings)

    assert min(media.likes_count, count) == len(data)
    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()


@pytest.mark.parametrize(
    "count, username", 
    [(randint(100, 500), choice(accounts)) for _ in range(3)],
)
def test_get_follows(agent, settings, count, username):
    account = Account(username)

    data, pointer = agent.get_follows(account, count=count, settings=settings)

    assert min(account.follows_count, count) == len(data)
    assert (pointer is None) == (account.follows_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize(
    "count, username", 
    [(randint(100, 500), choice(accounts)) for _ in range(3)],
)
@pytest.mark.asyncio
async def test_async_get_follows(event_loop, async_agent, settings, count, username):
    account = Account(username)

    data, pointer = await async_agent.get_follows(account, count=count, settings=settings)

    assert min(account.follows_count, count) == len(data)
    assert (pointer is None) == (account.follows_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize(
    "count, username", 
    [(randint(100, 500), choice(accounts)) for _ in range(3)],
)
def test_get_followers(agent, settings, count, username):
    account = Account(username)

    data, pointer = agent.get_followers(account, count=count, settings=settings)

    assert min(account.followers_count, count) == len(data)
    assert (pointer is None) == (account.followers_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize(
    "count, username", 
    [(randint(100, 500), choice(accounts)) for _ in range(3)],
)
@pytest.mark.asyncio
async def test_async_get_followers(event_loop, async_agent, settings, count, username):
    account = Account(username)

    data, pointer = await async_agent.get_followers(account, count=count, settings=settings)

    assert min(account.followers_count, count) == len(data)
    assert (pointer is None) == (account.followers_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("count", [[randint(100, 500)]])
def test_get_feed(agent, settings, count):
    data, _ = agent.feed(count=count, settings=settings)

    assert count >= len(data)

    Account.clear_cache()


@pytest.mark.parametrize("count", [[randint(100, 500)]])
@pytest.mark.asyncio
async def test_async_get_feed(event_loop, async_agent, settings, count):
    agent = await AsyncAgentAccount.create(login, password)

    data, _ = await async_agent.feed(count=count, settings=settings)

    assert count >= len(data)

    Account.clear_cache()


def test_get_stories(agent, settings):
    agent.stories(settings=settings)

    Account.clear_cache()
    Story.clear_cache()


@pytest.mark.asyncio
async def test_async_get_stories(event_loop, async_agent, settings):
    await agent.stories(settings=settings)

    Account.clear_cache()
    Story.clear_cache()


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
def test_get_media_account_pointer(agent, settings, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent.get_media(account, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_media_account_pointer(event_loop, async_agent, settings, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent.get_media(account, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count, id", [(randint(1, 10), choice(locations))])
def test_get_media_location_pointer(agent, settings, count, id):
    location = Location(id)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent.get_media(location, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (location.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()
    Location.clear_cache()


@pytest.mark.parametrize("count, id", [(randint(1, 10), choice(locations))])
@pytest.mark.asyncio
async def test_async_get_media_location_pointer(event_loop, async_agent, settings, count, id):
    location = Location(id)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent.get_media(location, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (location.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()
    Location.clear_cache()


@pytest.mark.parametrize("count, name", [(randint(1, 10), choice(tags))])
def test_get_media_tag_pointer(agent, settings, count, name):
    tag = Tag(name)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent.get_media(tag, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (tag.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()
    Tag.clear_cache()


@pytest.mark.parametrize("count, name", [(randint(1, 10), choice(tags))])
@pytest.mark.asyncio
async def test_async_get_media_tag_pointer(event_loop, async_agent, settings, count, name):
    tag = Tag(name)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await async_agent.get_media(tag, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (tag.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()
    Tag.clear_cache()


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(1, 10), choice(photos + photo_sets + videos))],
)
def test_get_likes_pointer(agent, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent.get_likes(media, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (media.likes_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(1, 10), choice(photos + photo_sets + videos))],
)
@pytest.mark.asyncio
async def test_async_get_likes_pointer(event_loop, async_agent, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await async_agent.get_likes(media, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (media.likes_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
def test_get_follows_pointer(agent, settings, count, username):
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent.get_follows(account, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (account.follows_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_follows_pointer(event_loop, async_agent, settings, count, username):
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await async_agent.get_follows(account, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (account.follows_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
def test_get_followers_pointer(agent, count, username):
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent.get_followers(account, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (account.followers_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_followers_pointer(event_loop, async_agent, settings, count, username):
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await async_agent.get_followers(account, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (account.followers_count <= count)

    Account.clear_cache()


@pytest.mark.parametrize("count", [[randint(1, 10)]])
def test_get_feed_pointer(agent, count):
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent.feed(pointer=pointer, settings=settings)
        data.extend(tmp)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count", [[randint(1, 10)]])
@pytest.mark.asyncio
async def test_async_get_feed_pointer(event_loop, async_agent, settings, count):
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await async_agent.feed(pointer=pointer, settings=settings)
        data.extend(tmp)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [photos])
def test_like_unlike_photo(agent, settings, shortcode):
    photo = Media(shortcode)
    
    assert agent.like(photo, settings=settings)
    assert agent.unlike(photo, settings=settings)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [photos])
@pytest.mark.asyncio
async def test_async_like_unlike_photo(event_loop, async_agent, settings, shortcode):
    photo = Media(shortcode)
    
    assert await agent.like(photo, settings=settings)
    assert await agent.unlike(photo, settings=settings)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [photo_sets])
def test_like_unlike_photo_set(agent, settings, shortcode):
    photo_set = Media(shortcode)

    assert agent.like(photo_set, settings=settings)
    assert agent.unlike(photo_set, settings=settings)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [photo_sets])
@pytest.mark.asyncio
async def test_async_like_unlike_photo_set(event_loop, async_agent, settings, shortcode):
    photo_set = Media(shortcode)
    
    assert await agent.like(photo_set, settings=settings)
    assert await agent.unlike(photo_set, settings=settings)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [videos])
def test_like_unlike_video(agent, settings, shortcode):
    video = Media(shortcode)

    assert agent.like(video, settings=settings)
    assert agent.unlike(video, settings=settings)
    
    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [videos])
@pytest.mark.asyncio
async def test_async_like_unlike_video(event_loop, async_agent, settings, shortcode):
    video = Media(shortcode)

    assert await agent.like(video, settings=settings)
    assert await agent.unlike(video, settings=settings)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("username", [accounts])
def test_follow_unfollow(agent, settings, username):
    account = Account(username)

    assert agent.follow(account, settings=settings)
    assert agent.unfollow(account, settings=settings)

    Account.clear_cache()


@pytest.mark.parametrize("username", [accounts])
@pytest.mark.asyncio
async def test_async_follow_unfollow(event_loop, async_agent, settings, username):
    account = Account(username)

    assert await async_agent.follow(account, settings=settings)
    assert await async_agent.unfollow(account, settings=settings)

    Account.clear_cache()


@pytest.mark.parametrize("shortcode", ([choice(photos), choice(photo_sets), choice(videos)]))
def test_comment(agent, settings, shortcode):
    media = Media(shortcode)

    comment = agent.add_comment(media, "test", settings=settings)
    agent.delete_comment(comment, settings=settings)

    Account.clear_cache()
    Media.clear_cache()
    Comment.clear_cache()


@pytest.mark.parametrize("shortcode", ([choice(photos), choice(photo_sets), choice(videos)]))
@pytest.mark.asyncio
async def test_async_comment(event_loop, async_agent, settings, shortcode):
    media = Media(shortcode)

    comment = await async_agent.add_comment(media, "test", settings=settings)
    await async_agent.delete_comment(comment, settings=settings)

    Account.clear_cache()
    Media.clear_cache()
    Comment.clear_cache()
