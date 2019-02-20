import pytest
from random import randint, choice

from instaparser.agents import Agent, AsyncAgent
from instaparser.entities import Account, Media, Location, Tag

from tests.settings import accounts, locations, photos, photo_sets, tags, videos


@pytest.fixture
def settings():
    return {"headers": {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101",
    }}


@pytest.fixture
def agent(settings):
    return Agent(settings=settings)


@pytest.fixture
@pytest.mark.asyncio
async def async_agent(settings):
    return await AsyncAgent.create(settings=settings)


def test_update(agent, settings):
    agent.update(settings=settings)

    assert not getattr(agent, "rhx_gis", None) is None
    assert not getattr(agent, "csrf_token", None) is None


@pytest.mark.asyncio
async def test_async_update(event_loop, async_agent, settings):
    await async_agent.update(settings=settings)

    assert not getattr(async_agent, "rhx_gis", None) is None
    assert not getattr(async_agent, "csrf_token", None) is None


@pytest.mark.parametrize("username", accounts)
def test_update_account(agent, settings, username):
    account = Account(username)

    data = agent.update(account, settings=settings)

    assert not data is None
    assert not account.id is None
    assert not account.full_name is None
    assert not account.profile_pic_url is None
    assert not account.profile_pic_url_hd is None
    assert not account.biography is None
    assert not account.follows_count is None
    assert not account.followers_count is None
    assert not account.media_count is None
    assert not account.is_private is None
    assert not account.is_verified is None
    assert not account.country_block is None

    Account.clear_cache()


@pytest.mark.parametrize("username", accounts)
@pytest.mark.asyncio
async def test_async_update_account(event_loop, async_agent, settings, username):
    account = Account(username)

    data = await async_agent.update(account, settings=settings)

    assert not data is None
    assert not account.id is None
    assert not account.full_name is None
    assert not account.profile_pic_url is None
    assert not account.profile_pic_url_hd is None
    assert not account.biography is None
    assert not account.follows_count is None
    assert not account.followers_count is None
    assert not account.media_count is None
    assert not account.is_private is None
    assert not account.is_verified is None
    assert not account.country_block is None

    Account.clear_cache()


@pytest.mark.parametrize("shortcode", photos)
def test_update_photo(agent, settings, shortcode):
    photo = Media(shortcode)

    agent.update(photo, settings=settings)

    assert not photo.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", photos)
@pytest.mark.asyncio
async def test_async_update_photo(event_loop, async_agent, settings, shortcode):
    photo = Media(shortcode)

    await async_agent.update(photo, settings=settings)

    assert not photo.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", photo_sets)
def test_update_photo_set(agent, settings, shortcode):
    photo_set = Media(shortcode)

    agent.update(photo_set, settings=settings)

    assert not photo_set.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", photo_sets)
@pytest.mark.asyncio
async def test_async_update_photo_set(event_loop, async_agent, settings, shortcode):
    photo_set = Media(shortcode)

    await async_agent.update(photo_set, settings=settings)

    assert not photo_set.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", videos)
def test_update_video(agent, settings, shortcode):
    video = Media(shortcode)

    agent.update(video, settings=settings)

    assert video.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", videos)
@pytest.mark.asyncio
async def test_async_update_video(event_loop, async_agent, settings, shortcode):
    video = Media(shortcode)

    await async_agent.update(video, settings=settings)

    assert video.is_video

    Media.clear_cache()


@pytest.mark.parametrize("id", locations)
def test_update_location(agent, settings, id):
    location = Location(id)

    agent.update(location, settings=settings)

    Location.clear_cache()


@pytest.mark.parametrize("id", locations)
@pytest.mark.asyncio
async def test_async_update_location(event_loop, async_agent, settings, id):
    location = Location(id)

    await async_agent.update(location, settings=settings)

    Location.clear_cache()


@pytest.mark.parametrize("name", tags)
def test_update_tag(agent, name):
    tag = Tag(name)

    agent.update(tag)

    Tag.clear_cache()


@pytest.mark.parametrize("name", tags)
@pytest.mark.asyncio
async def test_async_update_tag(event_loop, async_agent, settings, name):
    tag = Tag(name)

    await async_agent.update(tag, settings=settings)

    Tag.clear_cache()


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
def test_get_media_account(agent, settings, count, username):
    account = Account(username)

    data, pointer = agent.get_media(account, count=count, settings=settings)

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_media_account(event_loop, async_agent, settings, count, username):
    account = Account(username)

    data, pointer = await async_agent.get_media(account, count=count, settings=settings)

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count, id", [(randint(100, 500), choice(locations))])
def test_get_media_location(agent, settings, count, id):
    location = Location(id)

    data, pointer = agent.get_media(location, count=count, settings=settings)

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count, id", [(randint(100, 500), choice(locations))])
@pytest.mark.asyncio
async def test_async_get_media_location(event_loop, async_agent, settings, count, id):
    location = Location(id)

    data, pointer = await async_agent.get_media(location, count=count, settings=settings)

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count, name", [(randint(100, 500), choice(tags))])
def test_get_media_tag(agent, settings, count, name):
    tag = Tag(name)

    data, pointer = agent.get_media(tag, count=count, settings=settings)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count, name", [(randint(100, 500), choice(tags))])
@pytest.mark.asyncio
async def test_async_get_media_tag(event_loop, async_agent, settings, count, name):
    tag = Tag(name)

    data, pointer =await async_agent.get_media(tag, count=count, settings=settings)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [choice(photos), choice(photo_sets), choice(videos)])
def test_get_likes(agent, settings, shortcode):
    media = Media(shortcode)

    data, _ = agent.get_likes(media, settings=settings)

    assert media.likes_count >= len(data)

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [choice(photos), choice(photo_sets), choice(videos)])
@pytest.mark.asyncio
async def test_async_get_likes(event_loop, async_agent, settings, shortcode):
    media = Media(shortcode)

    data, _ = await async_agent.get_likes(media, settings=settings)

    assert media.likes_count >= len(data)

    Media.clear_cache()


@pytest.mark.parametrize(
    "count,shortcode",
    [(randint(100, 500), shortcode) for shortcode in [
        choice(photos),
        choice(photo_sets),
        choice(videos),
    ]],
)
def test_get_comments(agent, settings, count, shortcode):
    media = Media(shortcode)

    data, pointer = agent.get_comments(media, count=count, settings=settings)

    assert min(media.comments_count, count) == len(data)
    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()


@pytest.mark.parametrize(
    "count,shortcode",
    [(randint(100, 500), shortcode) for shortcode in [
        choice(photos),
        choice(photo_sets),
        choice(videos),
    ]],
)
@pytest.mark.asyncio
async def test_async_get_comments(event_loop, async_agent, settings, count, shortcode):
    media = Media(shortcode)

    data, pointer = await async_agent.get_comments(media, count=count, settings=settings)

    assert min(media.comments_count, count) == len(data)
    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
def test_get_media_account_pointer(agent, count, settings, username):
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

    Location.clear_cache()
    Media.clear_cache()


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

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count, name", [(randint(1, 10), choice(tags))])
def test_get_media_tag_pointer(agent, settings, count, name):
    tag = Tag(name)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent.get_media(tag, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (tag.media_count <= count)

    Tag.clear_cache()
    Media.clear_cache()


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

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(1, 10), shortcode) for shortcode in [
        choice(photos),
        choice(photo_sets),
        choice(videos),
    ]],
)
def test_get_comments_pointer(agent, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent.get_comments(media, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(1, 10), shortcode) for shortcode in [
        choice(photos),
        choice(photo_sets),
        choice(videos),
    ]],
)
@pytest.mark.asyncio
async def test_async_get_comments_pointer(event_loop, async_agent, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent.get_comments(media, pointer=pointer, settings=settings)
        data.extend(tmp)

    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()
