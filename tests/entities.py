import pytest

from instaparser.entities import Account, Media, Location, Tag, Comment


def test_clear_cache_account():
    account = Account("test")
    
    Account.clear_cache()
    
    assert(Account._cache == dict())


def test_clear_cache_media():
    media = Media("test")
    
    Media.clear_cache()
    
    assert(Media._cache == dict())


def test_clear_cache_location():
    location = Location(1488)
    
    Location.clear_cache()
    
    assert(Location._cache == dict())


def test_clear_cache_tag():
    tag = Tag("test")

    Tag.clear_cache()
    
    assert(Tag._cache == dict())


def test_clear_cache_comment():
    account = Account("test")
    media = Media("test")
    comment = Comment(1488, media=media, owner=account, text="test",
                      created_at=0)
    
    Media.clear_cache()
    Comment.clear_cache()
    
    assert(Comment._cache == dict())
    assert(Media._cache == dict())
