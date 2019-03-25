import asyncio
from .fixtures import agent, async_agent, event_loop, settings
from instagram.agents import WebAgent, AsyncWebAgent
from instagram.entities import Account, Media, Location, Tag
import pytest
from random import choice, randint, random
from tests.settings import accounts, anon, locations, photos, photo_sets, tags, videos
from time import sleep


@pytest.fixture(scope="function")
def delay():
    if not anon["local_delay"] is None:
        min_delay = anon["local_delay"].get("min", 0)
        max_delay = anon["local_delay"].get("max", 10) 
        return random() * (max_delay - min_delay) + min_delay
    return 0


def setup_function():
    Account.clear_cache()
    Media.clear_cache()
    Location.clear_cache()
    Tag.clear_cache()
    if not anon["global_delay"] is None:
        min_delay = anon["global_delay"].get("min", 0)
        max_delay = anon["global_delay"].get("max", 120)
        sleep(random() * (max_delay - min_delay) + min_delay)


@pytest.mark.asyncio
async def teardown_module(async_agent):
    await async_agent.delete()


def test_update(agent, settings):
    agent.update(settings=settings)

    assert not agent.rhx_gis is None
    assert not agent.csrf_token is None


@pytest.mark.asyncio
async def test_async_update(async_agent, settings):
    await async_agent.update(settings=settings)

    assert not async_agent.rhx_gis is None
    assert not async_agent.csrf_token is None


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


@pytest.mark.parametrize("username", accounts)
@pytest.mark.asyncio
async def test_async_update_account(async_agent, settings, username):
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


@pytest.mark.parametrize("shortcode", [choice(photos + photo_sets + videos)])
def test_update_media(agent, settings, shortcode):
    media = Media(shortcode)
    data = agent.update(media, settings=settings)

    assert not data is None
    assert not media.id is None
    assert not media.code is None
    assert not media.date is None
    assert not media.likes_count is None
    assert not media.comments_count is None
    assert not media.comments_disabled is None
    assert not media.is_video is None
    assert not media.display_url is None
    assert not media.resources is None
    assert not media.is_album is None


@pytest.mark.parametrize("shortcode", [choice(photos + photo_sets + videos)])
@pytest.mark.asyncio
async def test_async_update_media(async_agent, settings, shortcode):
    media = Media(shortcode)
    data = await async_agent.update(media, settings=settings)

    assert not data is None
    assert not media.id is None
    assert not media.code is None
    assert not media.date is None
    assert not media.likes_count is None
    assert not media.comments_count is None
    assert not media.comments_disabled is None
    assert not media.is_video is None
    assert not media.display_url is None
    assert not media.resources is None
    assert not media.is_album is None


@pytest.mark.parametrize("id", locations)
def test_update_location(agent, settings, id):
    location = Location(id)
    data = agent.update(location, settings=settings)

    assert not data is None
    assert not location.id is None
    assert not location.slug is None
    assert not location.name is None
    assert not location.has_public_page is None
    assert not location.coordinates is None
    assert not location.media_count is None


@pytest.mark.parametrize("id", locations)
@pytest.mark.asyncio
async def test_async_update_location(async_agent, settings, id):
    location = Location(id)
    data = await async_agent.update(location, settings=settings)

    assert not data is None
    assert not location.id is None
    assert not location.slug is None
    assert not location.name is None
    assert not location.has_public_page is None
    assert not location.coordinates is None
    assert not location.media_count is None


@pytest.mark.parametrize("name", tags)
def test_update_tag(agent, settings, name):
    tag = Tag(name)
    data = agent.update(tag, settings=settings)

    assert not data is None
    assert not tag.name is None
    assert not tag.media_count is None
    assert tag.top_posts


@pytest.mark.parametrize("name", tags)
@pytest.mark.asyncio
async def test_async_update_tag(async_agent, settings, name):
    tag = Tag(name)
    data = await async_agent.update(tag, settings=settings)

    assert not data is None
    assert not tag.name is None
    assert not tag.media_count is None
    assert tag.top_posts


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
def test_get_media_account(agent, delay, settings, count, username):
    account = Account(username)
    data, pointer = agent.get_media(account, count=count, delay=delay, settings=settings)

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_media_account(async_agent, delay, settings, count, username):
    account = Account(username)
    data, pointer = await async_agent.get_media(
        account,
        count=count,
        delay=delay,
        settings=settings,
    )

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)


@pytest.mark.parametrize("count, id", [(randint(100, 500), choice(locations))])
def test_get_media_location(agent, delay, settings, count, id):
    location = Location(id)
    data, pointer = agent.get_media(location, count=count, delay=delay, settings=settings)

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)


@pytest.mark.parametrize("count, id", [(randint(100, 500), choice(locations))])
@pytest.mark.asyncio
async def test_async_get_media_location(async_agent, delay, settings, count, id):
    location = Location(id)
    data, pointer = await async_agent.get_media(
        location,
        count=count,
        delay=delay,
        settings=settings,
    )

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)


@pytest.mark.parametrize("count, name", [(randint(100, 500), choice(tags))])
def test_get_media_tag(agent, delay, settings, count, name):
    tag = Tag(name)
    data, pointer = agent.get_media(tag, count=count, delay=delay, settings=settings)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)


@pytest.mark.parametrize("count, name", [(randint(100, 500), choice(tags))])
@pytest.mark.asyncio
async def test_async_get_media_tag(async_agent, delay, settings, count, name):
    tag = Tag(name)
    data, pointer = await async_agent.get_media(tag, count=count, delay=delay, settings=settings)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)


@pytest.mark.parametrize("shortcode", [choice(photos), choice(photo_sets), choice(videos)])
def test_get_likes(agent, settings, shortcode):
    media = Media(shortcode)
    data, _ = agent.get_likes(media, settings=settings)

    assert media.likes_count >= len(data)


@pytest.mark.parametrize("shortcode", [choice(photos), choice(photo_sets), choice(videos)])
@pytest.mark.asyncio
async def test_async_get_likes(async_agent, settings, shortcode):
    media = Media(shortcode)
    data, _ = await async_agent.get_likes(media, settings=settings)

    assert media.likes_count >= len(data)


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(100, 500), shortcode) for shortcode in [
        choice(photos),
        choice(photo_sets),
        choice(videos),
    ]],
)
def test_get_comments(agent, delay, settings, count, shortcode):
    media = Media(shortcode)
    data, pointer = agent.get_comments(media, count=count, delay=delay, settings=settings)

    assert min(media.comments_count, count) == len(data)
    assert (pointer is None) == (media.comments_count <= count)


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(100, 500), shortcode) for shortcode in [
        choice(photos),
        choice(photo_sets),
        choice(videos),
    ]],
)
@pytest.mark.asyncio
async def test_async_get_comments(async_agent, delay, settings, count, shortcode):
    media = Media(shortcode)
    data, pointer = await async_agent.get_comments(
        media,
        count=count,
        delay=delay,
        settings=settings,
    )

    assert min(media.comments_count, count) == len(data)
    assert (pointer is None) == (media.comments_count <= count)


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
def test_get_media_account_pointer(agent, delay, settings, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent.get_media(account, pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (account.media_count == len(data))


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_media_account_pointer(async_agent, delay, settings, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent.get_media(account, pointer=pointer, settings=settings)
        await asyncio.sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (account.media_count == len(data))


@pytest.mark.parametrize("count, id", [(randint(1, 10), choice(locations))])
def test_get_media_location_pointer(agent, delay, settings, count, id):
    location = Location(id)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent.get_media(location, pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (location.media_count == len(data))


@pytest.mark.parametrize("count, id", [(randint(1, 10), choice(locations))])
@pytest.mark.asyncio
async def test_async_get_media_location_pointer(async_agent, delay, settings, count, id):
    location = Location(id)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent.get_media(location, pointer=pointer, settings=settings)
        await asyncio.sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (location.media_count == len(data))


@pytest.mark.parametrize("count, name", [(randint(1, 10), choice(tags))])
def test_get_media_tag_pointer(agent, delay, settings, count, name):
    tag = Tag(name)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent.get_media(tag, pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (tag.media_count == len(data))


@pytest.mark.parametrize("count, name", [(randint(1, 10), choice(tags))])
@pytest.mark.asyncio
async def test_async_get_media_tag_pointer(async_agent, delay, settings, count, name):
    tag = Tag(name)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent.get_media(tag, pointer=pointer, settings=settings)
        await asyncio.sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (tag.media_count == len(data))


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(1, 10), shortcode) for shortcode in [
        choice(photos),
        choice(photo_sets),
        choice(videos),
    ]],
)
def test_get_comments_pointer(agent, delay, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent.get_comments(media, pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (media.comments_count == len(data))


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(1, 10), shortcode) for shortcode in [
        choice(photos),
        choice(photo_sets),
        choice(videos),
    ]],
)
@pytest.mark.asyncio
async def test_async_get_comments_pointer(async_agent, delay, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent.get_comments(media, pointer=pointer, settings=settings)
        await asyncio.sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (media.likes_count == len(data))
