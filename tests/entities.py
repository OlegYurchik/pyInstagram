import pytest

from instaparser.entities import Account, Comment, Location, Media, Story, Tag


def test_clear_cache_account():
    Account("test")
    
    Account.clear_cache()
    
    assert Account.cache == dict()


def test_clear_cache_media():
    Media("test")
    
    Media.clear_cache()
    
    assert Media.cache == dict()


def test_clear_cache_location():
    location = Location(1488)
    
    Location.clear_cache()
    
    assert Location.cache == dict()


def test_clear_cache_tag():
    Tag("test")

    Tag.clear_cache()
    
    assert Tag.cache == dict()


def test_clear_cache_comment():
    account = Account("test")
    media = Media("test")
    Comment(1488, media=media, owner=account, text="test", created_at=0)
    
    Media.clear_cache()
    Comment.clear_cache()
    
    assert Comment.cache == dict()
    assert Media.cache == dict()


def test_clear_cache_story():
    Account("test")
    Story("test")
    
    Story.clear_cache()

    assert Story.cache == dict()
