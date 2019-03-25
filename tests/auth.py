import asyncio
from .fixtures import agent_account, async_agent_account, event_loop, settings
from instagram.agents import WebAgentAccount, AsyncWebAgentAccount
from instagram.entities import Account, Comment, Location, Media, Story, Tag
import pytest
from random import choice, randint, random
from tests.settings import accounts, auth, creds, locations, photos, photo_sets, tags, videos
from time import sleep


@pytest.fixture(scope="function")
def delay():
    if not auth["local_delay"] is None:
        min_delay = auth["local_delay"].get("min", 0)
        max_delay = auth["local_delay"].get("max", 10) 
        return random() * (max_delay - min_delay) + min_delay
    return 0


def setup_function():
    Account.clear_cache()
    Media.clear_cache()
    Location.clear_cache()
    Tag.clear_cache()
    if not auth["global_delay"] is None:
        min_delay = auth["global_delay"].get("min", 0)
        max_delay = auth["global_delay"].get("max", 120)
        sleep(random() * (max_delay - min_delay) + min_delay)


@pytest.mark.asyncio
async def teardown_module(async_agent):
    await async_agent.delete()


def test_update(agent_account, settings):
    data = agent_account.update(settings=settings)

    assert not data is None
    assert not agent_account.id is None
    assert not agent_account.full_name is None
    assert not agent_account.profile_pic_url is None
    assert not agent_account.profile_pic_url_hd is None
    assert not agent_account.biography is None
    assert not agent_account.follows_count is None
    assert not agent_account.followers_count is None
    assert not agent_account.media_count is None
    assert not agent_account.is_private is None
    assert not agent_account.is_verified is None
    assert not agent_account.country_block is None


@pytest.mark.asyncio
async def test_async_update(async_agent_account, settings):
    data = await async_agent_account.update(settings=settings)

    assert not data is None
    assert not async_agent_account.id is None
    assert not async_agent_account.full_name is None
    assert not async_agent_account.profile_pic_url is None
    assert not async_agent_account.profile_pic_url_hd is None
    assert not async_agent_account.biography is None
    assert not async_agent_account.follows_count is None
    assert not async_agent_account.followers_count is None
    assert not async_agent_account.media_count is None
    assert not async_agent_account.is_private is None
    assert not async_agent_account.is_verified is None
    assert not async_agent_account.country_block is None


@pytest.mark.parametrize("username", accounts)
def test_update_account(agent_account, settings, username):
    account = Account(username)
    data = agent_account.update(account, settings=settings)
    
    assert not data is None
    assert not agent_account.id is None
    assert not agent_account.full_name is None
    assert not agent_account.profile_pic_url is None
    assert not agent_account.profile_pic_url_hd is None
    assert not agent_account.biography is None
    assert not agent_account.follows_count is None
    assert not agent_account.followers_count is None
    assert not agent_account.media_count is None
    assert not agent_account.is_private is None
    assert not agent_account.is_verified is None
    assert not agent_account.country_block is None


@pytest.mark.parametrize("username", accounts)
@pytest.mark.asyncio
async def test_async_update_account(async_agent_account, settings, username):
    account = Account(username)
    data = await async_agent_account.update(account, settings=settings)
    
    assert not data is None
    assert not async_agent_account.id is None
    assert not async_agent_account.full_name is None
    assert not async_agent_account.profile_pic_url is None
    assert not async_agent_account.profile_pic_url_hd is None
    assert not async_agent_account.biography is None
    assert not async_agent_account.follows_count is None
    assert not async_agent_account.followers_count is None
    assert not async_agent_account.media_count is None
    assert not async_agent_account.is_private is None
    assert not async_agent_account.is_verified is None
    assert not async_agent_account.country_block is None


@pytest.mark.parametrize("shortcode", [choice(photos + photo_sets + videos)])
def test_update_media(agent_account, settings, shortcode):
    media = Media(shortcode)
    data = agent_account.update(media, settings=settings)

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
async def test_async_update_media(async_agent_account, settings, shortcode):
    media = Media(shortcode)
    data = await async_agent_account.update(media, settings=settings)

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
def test_update_location(agent_account, settings, id):
    location = Location(id)
    data = agent_account.update(location, settings=settings)

    assert not data is None
    assert not location.id is None
    assert not location.slug is None
    assert not location.name is None
    assert not location.has_public_page is None
    assert not location.coordinates is None
    assert not location.media_count is None


@pytest.mark.parametrize("id", locations)
@pytest.mark.asyncio
async def test_async_update_location(async_agent_account, settings, id):
    location = Location(id)
    data = await async_agent_account.update(location, settings=settings)

    assert not data is None
    assert not location.id is None
    assert not location.slug is None
    assert not location.name is None
    assert not location.has_public_page is None
    assert not location.coordinates is None
    assert not location.media_count is None


@pytest.mark.parametrize("name", tags)
def test_update_tag(agent_account, settings, name):
    tag = Tag(name)
    data = agent_account.update(tag, settings=settings)

    assert not data is None
    assert not tag.name is None
    assert not tag.media_count is None
    assert tag.top_posts


@pytest.mark.parametrize("name", tags)
@pytest.mark.asyncio
async def test_async_update_tag(async_agent_account, settings, name):
    tag = Tag(name)
    data = await async_agent_account.update(tag, settings=settings)

    assert not data is None
    assert not tag.name is None
    assert not tag.media_count is None
    assert tag.top_posts


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
def test_get_media_account(agent_account, delay, settings, count, username):
    account = Account(username)
    data, pointer = agent_account.get_media(account, count=count, delay=delay, settings=settings)

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_media_account(async_agent_account, delay, settings, count, username):
    account = Account(username)
    data, pointer = await async_agent_account.get_media(
        account,
        count=count,
        delay=delay,
        settings=settings,
    )

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)


@pytest.mark.parametrize("count, id",  [(randint(100, 500), choice(locations))])
def test_get_media_location(agent_account, delay, settings, count, id):
    location = Location(id)
    data, pointer = agent_account.get_media(location, count=count, delay=delay, settings=settings)

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)


@pytest.mark.parametrize("count, id",  [(randint(100, 500), choice(locations))])
@pytest.mark.asyncio
async def test_async_get_media_location(async_agent_account, delay, settings, count, id):
    location = Location(id)
    data, pointer = await async_agent_account.get_media(
        location,
        count=count,
        delay=delay,
        settings=settings,
    )

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)


@pytest.mark.parametrize("count, name",  [(randint(100, 500), choice(tags))])
def test_get_media_tag(agent_account, delay, settings, count, name):
    tag = Tag(name)
    data, pointer = agent_account.get_media(tag, count=count, delay=delay, settings=settings)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)


@pytest.mark.parametrize("count, name", [(randint(100, 500), choice(tags))])
@pytest.mark.asyncio
async def test_async_get_media_tag(async_agent_account, delay, settings, count, name):
    tag = Tag(name)
    data, pointer = await async_agent_account.get_media(
        tag,
        count=count,
        delay=delay,
        settings=settings,
    )

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)


@pytest.mark.parametrize("shortcode", [choice(photos), choice(photo_sets), choice(videos)])
def test_get_likes(agent_account, settings, shortcode):
    media = Media(shortcode)
    data, _ = agent_account.get_likes(media, settings=settings)

    assert media.likes_count >= len(data)


@pytest.mark.parametrize("shortcode", [choice(photos), choice(photo_sets), choice(videos)])
@pytest.mark.asyncio
async def test_async_get_likes(async_agent_account, settings, shortcode):
    media = Media(shortcode)
    data, _ = await async_agent_account.get_likes(media, settings=settings)

    assert media.likes_count >= len(data)


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(100, 500), shortcode) for shortcode in [
        choice(photos),
        choice(photo_sets),
        choice(videos),
    ]],
)
def test_get_comments(agent_account, delay, settings, count, shortcode):
    media = Media(shortcode)
    data, pointer = agent_account.get_comments(media, count=count, delay=delay, settings=settings)

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
async def test_async_get_comments(async_agent_account, delay, settings, count, shortcode):
    media = Media(shortcode)
    data, pointer = await async_agent_account.get_comments(
        media,
        count=count,
        delay=delay,
        settings=settings,
    )

    assert min(media.comments_count, count) == len(data)
    assert (pointer is None) == (media.comments_count <= count)


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
def test_get_follows(agent_account, delay, settings, count, username):
    account = Account(username)
    data, pointer = agent_account.get_follows(account, count=count, delay=delay, settings=settings)

    assert min(account.follows_count, count) == len(data)
    assert (pointer is None) == (account.follows_count <= count)


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_follows(async_agent_account, delay, settings, count, username):
    account = Account(username)
    data, pointer = await async_agent_account.get_follows(
        account,
        count=count,
        delay=delay,
        settings=settings,
    )

    assert min(account.follows_count, count) == len(data)
    assert (pointer is None) == (account.follows_count <= count)


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
def test_get_followers(agent_account, delay, settings, count, username):
    account = Account(username)
    data, pointer = agent_account.get_followers(
        account,
        count=count,
        delay=delay,
        settings=settings,
    )

    assert min(account.followers_count, count) == len(data)
    assert (pointer is None) == (account.followers_count <= count)


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_followers(async_agent_account, delay, settings, count, username):
    account = Account(username)
    data, pointer = await async_agent_account.get_followers(
        account,
        count=count,
        delay=delay,
        settings=settings,
    )

    assert min(account.followers_count, count) == len(data)
    assert (pointer is None) == (account.followers_count <= count)


@pytest.mark.parametrize("count", [randint(100, 500)])
def test_get_feed(agent_account, delay, settings, count):
    data, pointer = agent_account.feed(count=count, delay=delay, settings=settings)

    assert (count > len(data)) == (pointer is None)


@pytest.mark.parametrize("count", [randint(100, 500)])
@pytest.mark.asyncio
async def test_async_get_feed(async_agent_account, delay, settings, count):
    data, pointer = await async_agent_account.feed(count=count, delay=delay, settings=settings)

    assert (count > len(data)) == (pointer is None)


def test_get_stories(agent_account, settings):
    agent_account.stories(settings=settings)


@pytest.mark.asyncio
async def test_async_get_stories(async_agent_account, settings):
    await async_agent_account.stories(settings=settings)


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
def test_get_media_account_pointer(agent_account, delay, settings, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_media(account, pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (account.media_count == len(data))


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_media_account_pointer(async_agent_account, delay, settings, count,
                                               username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent_account.get_media(
            account,
            pointer=pointer,
            settings=settings,
        )
        await asyncio.sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (account.media_count == len(data))


@pytest.mark.parametrize("count, id", [(randint(1, 10), choice(locations))])
def test_get_media_location_pointer(agent_account, delay, settings, count, id):
    location = Location(id)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_media(location, pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (location.media_count == len(data))


@pytest.mark.parametrize("count, id", [(randint(1, 10), choice(locations))])
@pytest.mark.asyncio
async def test_async_get_media_location_pointer(async_agent_account, delay, settings, count, id):
    location = Location(id)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent_account.get_media(
            location,
            pointer=pointer,
            settings=settings,
        )
        await asyncio.sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (location.media_count == len(data))


@pytest.mark.parametrize("count, name", [(randint(1, 10), choice(tags))])
def test_get_media_tag_pointer(agent_account, delay, settings, count, name):
    tag = Tag(name)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_media(tag, pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (tag.media_count == len(data))


@pytest.mark.parametrize("count, name", [(randint(1, 10), choice(tags))])
@pytest.mark.asyncio
async def test_async_get_media_tag_pointer(async_agent_account, delay, settings, count, name):
    tag = Tag(name)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent_account.get_media(tag, pointer=pointer, settings=settings)
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
def test_get_comments_pointer(agent_account, delay, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_comments(media, pointer=pointer, settings=settings)
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
async def test_async_get_comments_pointer(async_agent_account, delay, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent_account.get_comments(
            media,
            pointer=pointer,
            settings=settings,
        )
        await asyncio.sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (media.likes_count == len(data))


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(1, 10), choice(photos + photo_sets + videos))],
)
def test_get_likes_pointer(agent_account, delay, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent_account.get_likes(media, pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (media.likes_count <= count)


@pytest.mark.parametrize(
    "count, shortcode",
    [(randint(1, 10), choice(photos + photo_sets + videos))],
)
@pytest.mark.asyncio
async def test_async_get_likes_pointer(async_agent_account, delay, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent_account.get_likes(
            media,
            pointer=pointer,
            settings=settings,
        )
        await asyncio.sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (media.likes_count <= count)


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
def test_get_follows_pointer(agent_account, delay, settings, count, username):
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = agent_account.get_follows(account, pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (account.follows_count <= count)


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_follows_pointer(async_agent_account, delay, settings, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent_account.get_follows(
            account,
            pointer=pointer,
            settings=settings,
        )
        await asyncio.sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (account.follows_count <= count)


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
def test_get_followers_pointer(agent_account, delay, settings, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_followers(account, pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (account.followers_count <= count)


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_followers_pointer(async_agent_account, delay, settings, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent_account.get_followers(
            account,
            pointer=pointer,
            settings=settings,
        )
        await asyncio.sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (account.followers_count <= count)


@pytest.mark.parametrize("count", [randint(1, 10)])
def test_get_feed_pointer(agent_account, delay, settings, count):
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.feed(pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)


@pytest.mark.parametrize("count", [randint(1, 10)])
@pytest.mark.asyncio
async def test_async_get_feed_pointer(async_agent_account, delay, settings, count):
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await async_agent_account.feed(pointer=pointer, settings=settings)
        await asyncio.sleep(delay)
        data.extend(tmp)


@pytest.mark.parametrize("shortcode", [choice(photos + photo_sets + videos)])
def test_like_unlike_media(agent_account, delay, settings, shortcode):
    photo = Media(shortcode)

    assert agent_account.like(photo, settings=settings)
    sleep(delay)
    assert agent_account.unlike(photo, settings=settings)


@pytest.mark.parametrize("shortcode", [choice(photos + photo_sets + videos)])
@pytest.mark.asyncio
async def test_async_like_unlike_media(async_agent_account, delay, settings, shortcode):
    photo = Media(shortcode)

    assert await async_agent_account.like(photo, settings=settings)
    await asyncio.sleep(delay)
    assert await async_agent_account.unlike(photo, settings=settings)


@pytest.mark.parametrize("username", [choice(accounts)])
def test_follow_unfollow(agent_account, delay, settings, username):
    account = Account(username)
    agent_account.update(settings=settings)
    follows_count = agent_account.follows_count

    assert agent_account.follow(account, settings=settings)
    sleep(delay)
    agent_account.update(settings=settings)
    assert agent_account.follows_count == follows_count + 1
    assert agent_account.unfollow(account, settings=settings)
    sleep(delay)
    agent_account.update(settings=settings)
    assert agent_account.follows_count == follows_count


@pytest.mark.parametrize("username", [choice(accounts)])
@pytest.mark.asyncio
async def test_async_follow_unfollow(async_agent_account, delay, settings, username):
    account = Account(username)
    await async_agent_account.update(settings=settings)
    follows_count = async_agent_account.follows_count

    assert await async_agent_account.follow(account, settings=settings)
    await asyncio.sleep(delay)
    await async_agent_account.update(settings=settings)
    assert async_agent_account.follows_count == follows_count + 1
    assert await async_agent_account.unfollow(account, settings=settings)
    await asyncio.sleep(delay)
    await async_agent_account.update(settings=settings)
    assert async_agent_account.follows_count == follows_count


@pytest.mark.parametrize("shortcode", [choice(photos + photo_sets + videos)])
def test_comment(agent_account, delay, settings, shortcode):
    media = Media(shortcode)
    comment = agent_account.add_comment(media, "test", settings=settings)
    sleep(delay)

    assert agent_account.delete_comment(comment, settings=settings)


@pytest.mark.parametrize("shortcode", [choice(photos + photo_sets + videos)])
@pytest.mark.asyncio
async def test_async_comment(async_agent_account, delay, settings, shortcode):
    media = Media(shortcode)
    comment = await async_agent_account.add_comment(media, "test", settings=settings)
    await asyncio.sleep(delay)

    assert await async_agent_account.delete_comment(comment, settings=settings)
