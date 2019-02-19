import pytest
from random import randint, choice

from instaparser.agents import Agent, AsyncAgent
from instaparser.entities import Account, Media, Location, Tag

from tests.settings import accounts, locations, photos, photo_sets, tags, videos



def test_update():
    anon = Agent()
    
    anon.update()
    
    assert not getattr(anon, "rhx_gis", None) is None
    assert not getattr(anon, "csrf_token", None) is None


@pytest.mark.asyncio
async def test_async_update(event_loop):
    anon = AsyncAgent()
    await anon.__ainit__()

    await anon.update()

    assert not getattr(anon, "rhx_gis", None) is None
    assert not getattr(anon, "csrf_token", None) is None


@pytest.mark.parametrize("username", accounts)
def test_update_account(username):
    anon = Agent()
    account = Account(username)
    
    data = anon.update(account)
    
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
async def test_async_update_account(event_loop, username):
    anon = AsyncAgent()
    await anon.__ainit__()
    account = Account(username)
    
    data = await anon.update(account)
    
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
def test_update_photo(shortcode):
    anon = Agent()
    photo = Media(shortcode)

    anon.update(photo)

    assert not photo.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", photos)
@pytest.mark.asyncio
async def test_async_update_photo(event_loop, shortcode):
    anon = AsyncAgent()
    await anon.__ainit__()
    photo = Media(shortcode)

    await anon.update(photo)

    assert not photo.is_video

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", photo_sets)
def test_update_photo_set(shortcode):
    anon = Agent()
    photo_set = Media(shortcode)
    
    anon.update(photo_set)
    
    assert not photo_set.is_video
    
    Media.clear_cache()


@pytest.mark.parametrize("shortcode", photo_sets)
@pytest.mark.asyncio
async def test_async_update_photo_set(event_loop, shortcode):
    anon = AsyncAgent()
    await anon.__ainit__()
    photo_set = Media(shortcode)
    
    await anon.update(photo_set)
    
    assert not photo_set.is_video
    
    Media.clear_cache()


@pytest.mark.parametrize("shortcode", videos)
def test_update_video(shortcode):
    anon = Agent()
    video = Media(shortcode)
    
    anon.update(video)
    
    assert video.is_video
    
    Media.clear_cache()


@pytest.mark.parametrize("shortcode", videos)
@pytest.mark.asyncio
async def test_async_update_video(event_loop, shortcode):
    anon = AsyncAgent()
    await anon.__ainit__()
    video = Media(shortcode)
    
    await anon.update(video)
    
    assert video.is_video
    
    Media.clear_cache()


@pytest.mark.parametrize("id", locations)
def test_update_location(id):
    anon = Agent()
    location = Location(id)
    
    anon.update(location)
    
    Location.clear_cache()


@pytest.mark.parametrize("id", locations)
@pytest.mark.asyncio
async def test_async_update_location(event_loop, id):
    anon = AsyncAgent()
    await anon.__ainit__()
    location = Location(id)
    
    await anon.update(location)
    
    Location.clear_cache()


@pytest.mark.parametrize("name", tags)
def test_update_tag(name):
    anon = Agent()
    tag = Tag(name)
    
    anon.update(tag)
    
    Tag.clear_cache()


@pytest.mark.parametrize("name", tags)
@pytest.mark.asyncio
async def test_async_update_tag(event_loop, name):
    anon = AsyncAgent()
    await anon.__ainit__()
    tag = Tag(name)
    
    await anon.update(tag)
    
    Tag.clear_cache()


@pytest.mark.parametrize("count,username",
                         [(randint(100, 500), choice(accounts))  for i in range(3)])
def test_get_media_account(count, username):
    anon = Agent()
    account = Account(username)
    
    data, pointer = anon.get_media(account, count=count)

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count,username",
                         [(randint(100, 500), choice(accounts))  for i in range(3)])
@pytest.mark.asyncio
async def test_async_get_media_account(event_loop, count, username):
    anon = AsyncAgent()
    await anon.__ainit__()
    account = Account(username)
    
    data, pointer = await anon.get_media(account, count=count)

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count,id", [(randint(100, 500), choice(locations)) for i in range(3)])
def test_get_media_location(count, id):
    anon = Agent()
    location = Location(id)
    
    data, pointer = anon.get_media(location, count=count)

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count,id", [(randint(100, 500), choice(locations)) for i in range(3)])
@pytest.mark.asyncio
async def test_async_get_media_location(event_loop, count, id):
    anon = AsyncAgent()
    await anon.__ainit__()
    location = Location(id)
    
    data, pointer = await anon.get_media(location, count=count)

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count,name", [(randint(100, 500), choice(tags)) for i in range(3)])
def test_get_media_tag(count, name):
    anon = Agent()
    tag = Tag(name)
    
    data, pointer = anon.get_media(tag, count=count)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count,name", [(randint(100, 500), choice(tags)) for i in range(3)])
@pytest.mark.asyncio
async def test_async_get_media_tag(event_loop, count, name):
    anon = AsyncAgent()
    await anon.__ainit__()
    tag = Tag(name)
    
    data, pointer =await anon.get_media(tag, count=count)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [choice(photos), choice(photo_sets), choice(videos)])
def test_get_likes(shortcode):
    anon = Agent()
    media = Media(shortcode)
    
    data, _ = anon.get_likes(media)
    
    assert media.likes_count >= len(data)

    Media.clear_cache()


@pytest.mark.parametrize("shortcode", [choice(photos), choice(photo_sets), choice(videos)])
@pytest.mark.asyncio
async def test_async_get_likes(event_loop, shortcode):
    anon = AsyncAgent()
    await anon.__ainit__()
    media = Media(shortcode)
    
    data, _ = await anon.get_likes(media)
    
    assert media.likes_count >= len(data)

    Media.clear_cache()


@pytest.mark.parametrize("count,shortcode",
                         [(randint(100, 500), shortcode) \
                             for shortcode in [choice(photos), choice(photo_sets), choice(videos)]])
def test_get_comments(count, shortcode):
    anon = Agent()
    media = Media(shortcode)
    
    data, pointer = anon.get_comments(media, count=count)
    
    assert min(media.comments_count, count) == len(data)
    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()


@pytest.mark.parametrize("count,shortcode",
                         [(randint(100, 500), shortcode) \
                             for shortcode in [choice(photos), choice(photo_sets), choice(videos)]])
@pytest.mark.asyncio
async def test_async_get_comments(event_loop, count, shortcode):
    anon = AsyncAgent()
    await anon.__ainit__()
    media = Media(shortcode)
    
    data, pointer = await anon.get_comments(media, count=count)
    
    assert min(media.comments_count, count) == len(data)
    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()


@pytest.mark.parametrize("count,username", [(randint(1, 10), choice(accounts))])
def test_get_media_account_pointer(count, username):
    anon = Agent()
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = anon.get_media(account, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count,username", [(randint(1, 10), choice(accounts))])
@pytest.mark.asyncio
async def test_async_get_media_account_pointer(event_loop, count, username):
    anon = AsyncAgent()
    await anon.__ainit__()
    account = Account(username)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await anon.get_media(account, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (account.media_count <= count)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count,id", [(randint(1, 10), choice(locations))])
def test_get_media_location_pointer(count, id):
    anon = Agent()
    location = Location(id)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = anon.get_media(location, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (location.media_count <= count)

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count,id", [(randint(1, 10), choice(locations))])
@pytest.mark.asyncio
async def test_async_get_media_location_pointer(event_loop, count, id):
    anon = AsyncAgent()
    await anon.__ainit__()
    location = Location(id)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await anon.get_media(location, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (location.media_count <= count)

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count,name", [(randint(1, 10), choice(tags))])
def test_get_media_tag_pointer(count, name):
    anon = Agent()
    tag = Tag(name)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = anon.get_media(tag, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (tag.media_count <= count)

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count,name", [(randint(1, 10), choice(tags))])
@pytest.mark.asyncio
async def test_async_get_media_tag_pointer(event_loop, count, name):
    anon = AsyncAgent()
    await anon.__ainit__()
    tag = Tag(name)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = await anon.get_media(tag, pointer=pointer)
        data.extend(tmp)

    assert (pointer is None) == (tag.media_count <= count)

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count,shortcode",
                         [(randint(1, 10), shortcode) \
                             for shortcode in [choice(photos), choice(photo_sets), choice(videos)]])
def test_get_comments_pointer(count, shortcode):
    anon = Agent()
    media = Media(shortcode)
    pointer = None
    data = []
    
    for _ in range(count):
        tmp, pointer = anon.get_comments(media, pointer=pointer)
        data.extend(tmp)
    
    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()


@pytest.mark.parametrize("count,shortcode",
                         [(randint(1, 10), shortcode) \
                             for shortcode in [choice(photos), choice(photo_sets), choice(videos)]])
@pytest.mark.asyncio
async def test_async_get_comments_pointer(event_loop, count, shortcode):
    anon = AsyncAgent()
    await anon.__ainit__()
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = await anon.get_comments(media, pointer=pointer)
        data.extend(tmp)
    
    assert (pointer is None) == (media.likes_count <= count)

    Media.clear_cache()
