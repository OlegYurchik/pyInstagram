from typing import (
    Any,
    Dict,
    Iterable,
)
from urllib.parse import urljoin


class EntityConstructor(type):
    def __new__(cls, name: str, classes: Iterable[type], fields: Dict[str, Any]):
        fields["cache"] = dict()

        return super().__new__(cls, name, classes, fields)


class Entity(metaclass=EntityConstructor):
    def __new__(cls, key, *args, **kwargs):
        if not str(key) in cls.cache:
            cls.cache[str(key)] = super().__new__(cls)

        return cls.cache[str(key)]

    def __repr__(self):
        return str(self.__getattribute__(self.primary_key))

    def delete(self):
        key = self.__getattribute__(self.primary_key)
        if key in self.cache:
            del self.cache[key]

    @classmethod
    def clear_cache(cls):
        cls.cache.clear()

    @property
    def primary_key(self):
        raise NotImplementedError


class UpdatableEntity(Entity):
    def get_web_path(self):
        return urljoin(self.web_base_path, str(getattr(self, self.primary_key)))

    @classmethod
    def get_from_web_entry_data_path(cls, data):
        for key in cls.web_entry_data_path:
            data = data[key]
        return data

    @property
    def web_entry_data_path(self):
        raise NotImplementedError

    @property
    def web_base_path(self):
        raise NotImplementedError

    def set_web_data(self, data):
        raise NotImplementedError

    def set_mobile_data(self, data):
        raise NotImplementedError


class HasMediaEntity(UpdatableEntity):
    @classmethod
    def get_from_web_media_path(cls, data):
        for key in cls.web_media_path:
            data = data[key]
        return data

    @property
    def web_media_path(self):
        raise NotImplementedError

    @property
    def web_media_query_hash(self):
        raise NotImplementedError


class Account(HasMediaEntity):
    primary_key = "username"
    web_entry_data_path = ("ProfilePage", 0, "graphql", "user")
    web_base_path = ""
    web_media_path = ("user", "edge_owner_to_timeline_media")
    web_media_query_hash = "c6809c9c025875ac6f02619eae97a80e"

    def __init__(self, username):
        self.id = None
        self.username = username
        self.full_name = None
        self.profile_pic_url = None
        self.profile_pic_url_hd = None
        self.fb_page = None
        self.biography = None
        self.follows_count = None
        self.followers_count = None
        self.media_count = None
        self.is_private = None
        self.is_verified = None
        self.country_block = None

        self.media = set()
        self.follows = set()
        self.followers = set()

    def set_web_data(self, data):
        self.id = data["id"]
        self.full_name = data["full_name"]
        self.profile_pic_url = data["profile_pic_url"]
        self.profile_pic_url_hd = data["profile_pic_url_hd"]
        self.fb_page = data["connected_fb_page"]
        self.biography = data["biography"]
        self.follows_count = data["edge_follow"]["count"]
        self.followers_count = data["edge_followed_by"]["count"]
        self.media_count = data["edge_owner_to_timeline_media"]["count"]
        self.is_private = data["is_private"]
        self.is_verified = data["is_verified"]
        self.country_block = data["country_block"]

    def set_mobile_data(self, data):
        self.id = data["pk"]
        self.full_name = data["full_name"]
        self.profile_pic_url = data["profile_pic_url"]
        self.profile_pic_url_hd = data["hd_profile_pic_url_info"]["url"]
        # self.fb_page = data["connected_fb_page"]
        self.biography = data["biography"]
        self.follows_count = data["following_count"]
        self.followers_count = data["follower_count"]
        self.media_count = data["media_count"]
        self.is_private = data["is_private"]
        self.is_verified = data["is_verified"]
        # self.country_block = data["country_block"]


class Media(UpdatableEntity):
    primary_key = "code"
    web_entry_data_path = ("PostPage", 0, "graphql", "shortcode_media")
    web_base_path = "p/"

    def __init__(self, code):
        self.id = None
        self.code = code
        self.caption = None
        self.owner = None
        self.date = None
        self.location = None
        self.likes_count = None
        self.comments_count = None
        self.comments_disabled = None
        self.is_video = None
        self.video_url = None
        self.is_ad = None
        self.display_url = None
        self.resources = None
        self.is_album = None

        self.album = set()
        self.likes = set()
        self.comments = set()

    def set_web_data(self, data):
        self.id = data["id"]
        self.code = data["shortcode"]
        if data["edge_media_to_caption"]["edges"]:
            self.caption = data["edge_media_to_caption"]["edges"][0]["node"]["text"]
        else:
            self.caption = None
        if "username" in data["owner"]:
            self.owner = Account(data["owner"]["username"])
        self.date = data["taken_at_timestamp"]
        if "location" in data and data["location"] and "id" in data["location"]:
            self.location = Location(data["location"]["id"])
        if "edge_media_preview_like" in data:
            self.likes_count = data["edge_media_preview_like"]["count"]
        elif "edge_liked_by":
            self.likes_count = data["edge_liked_by"]
        if "edge_media_to_comment" in data:
            self.comments_count = data["edge_media_to_comment"]["count"]
        else:
            self.comments_count = data["edge_media_to_parent_comment"]["count"]
        self.comments_disabled = data["comments_disabled"]
        self.is_video = data["is_video"]
        if self.is_video and "video_url" in data:
            self.video_url = data["video_url"]
        if "is_ad" in data:
            self.is_ad = data["is_ad"]
        self.display_url = data["display_url"]
        if "display_resources" in data:
            self.resources = [resource["src"] for resource in data["display_resources"]]
        else:
            self.resources = [resource["src"] for resource in data["thumbnail_resources"]]
        self.album = set()
        self.is_album = data.get("__typename") == "GraphSidecar"
        if "edge_sidecar_to_children" in data:
            for edge in data["edge_sidecar_to_children"]["edges"]:
                if edge["node"].get("shortcode", self.code) != self.code:
                    child = Media(edge["node"]["shortcode"])
                    child.id = edge["node"]["id"]
                    child.is_video = edge["node"]["is_video"]
                    if child.is_video and "video_url" in edge["node"]:
                        child.video_url = edge["node"]["video_url"]
                    child.display_url = edge["node"]["display_url"]
                    if "display_resources" in edge["node"]:
                        child.resources = [resource["src"] for resource in edge["node"]["display_resources"]]
                    elif "thumbnail_resources" in edge["node"]:
                        child.resources = [resource["src"] for resource in edge["node"]["thumbnail_resources"]]
                    child.is_album = False
                    self.album.add(child)


class Story(Entity):
    primary_key = "id"

    def __init__(self, id):
        self.id = id


class Location(HasMediaEntity):
    primary_key = "id"
    web_entry_data_path = ("LocationsPage", 0, "graphql", "location")
    web_base_path = "explore/locations/"
    web_media_path = ("location", "edge_location_to_media")
    web_media_query_hash = "ac38b90f0f3981c42092016a37c59bf7"

    def __init__(self, id):
        self.id = id
        self.slug = None
        self.name = None
        self.has_public_page = None
        self.directory = None
        self.coordinates = None
        self.media_count = None

        self.media = set()
        self.top_posts = set()

    def set_web_data(self, data):
        self.id = data["id"]
        self.slug = data["slug"]
        self.name = data["name"]
        self.has_public_page = data["has_public_page"]
        if "directory" in data:
            self.directory = data["directory"]
        self.coordinates = (data["lat"], data["lng"])
        self.media_count = data["edge_location_to_media"]["count"]
        for node in data["edge_location_to_top_posts"]["edges"]:
            self.top_posts.add(Media(node["node"]["shortcode"]))


class Tag(HasMediaEntity):
    primary_key = "name"
    web_entry_data_path = ("TagPage", 0, "graphql", "hashtag")
    web_base_path = "explore/tags/"
    web_media_path = ("hashtag", "edge_hashtag_to_media")
    web_media_query_hash = "ded47faa9a1aaded10161a2ff32abb6b"

    def __init__(self, name):
        self.name = name
        self.media_count = None

        self.media = set()
        self.top_posts = set()

    def set_web_data(self, data):
        self.name = data["name"]
        self.media_count = data["edge_hashtag_to_media"]["count"]
        for node in data["edge_hashtag_to_top_posts"]["edges"]:
            self.top_posts.add(Media(node["node"]["shortcode"]))


class Comment(Entity):
    primary_key = "id"

    def __init__(self, id, media, owner, text, created_at):
        self.id = id
        self.media = media
        self.owner = owner
        self.text = text
        self.created_at = created_at
