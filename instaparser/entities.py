# Cache metaclass for optimized memory
class ElementConstructor(type):
    def __new__(mcs, name, classes, fields):
        def delete(self):
            key = self.__getattribute__(self._primary_key)
            if key in self._cache:
                del self._cache[key]

        @classmethod
        def clear_cache(cls):
            cls._cache.clear()

        fields["__del__"] = delete
        fields["clear_cache"] = clear_cache
        fields["__str__"] = lambda self: str(self.__getattribute__(self._primary_key))
        fields["__repr__"] = lambda self: str(self.__getattribute__(self._primary_key))
        fields["_cache"] = dict()

        return super().__new__(mcs, name, classes, fields)

    def __call__(cls, key, *args, **kwargs):
        if not str(key) in cls._cache:
            cls._cache[str(key)] = super().__call__(str(key), *args, **kwargs)

        return cls._cache[str(key)]
        


# Common abstract classes 
class Element(metaclass=ElementConstructor):
    def _primary_key(self):
        raise NotImplementedError


class UpdatableElement(Element):
    def _entry_data_path(self):
        raise NotImplementedError


    def _base_url(self):
        raise NotImplementedError


    def _set_data(self):
        raise NotImplementedError


class HasMediaElement(UpdatableElement):
    def _media_path(self):
        raise NotImplementedError
    
    def _media_query_hash(self):
        raise NotImplementedError



# Entity classes
class Account(HasMediaElement):
    _primary_key = "login"
    _entry_data_path = ("ProfilePage", 0, "graphql", "user")
    _base_url = ""
    _media_path = ("user", "edge_owner_to_timeline_media")
    _media_query_hash = "c6809c9c025875ac6f02619eae97a80e"


    def __init__(self, login):
        self.id = None
        self.login = login
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


    def _set_data(self, data):
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


class Media(UpdatableElement):
    _primary_key = "code"
    _entry_data_path = ("PostPage", 0, "graphql", "shortcode_media")
    _base_url = "p/"


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
        self.dimensions = None

        self.likes = set()
        self.comments = set()


    def _set_data(self, data):
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
        self.likes_count = data["edge_media_preview_like"]["count"]
        self.comments_count = data["edge_media_to_comment"]["count"]
        self.comments_disabled = data["comments_disabled"]
        self.is_video = data["is_video"]
        if self.is_video and "video_url" in data:
            self.video_url = data["video_url"]
        if "is_ad" in data:
            self.is_ad = data["is_ad"]
        self.display_url = data["display_url"]


class Location(HasMediaElement):
    _primary_key = "id"
    _entry_data_path = ("LocationsPage", 0, "graphql", "location")
    _base_url = "explore/locations/"
    _media_path = ("location", "edge_location_to_media")
    _media_query_hash = "ac38b90f0f3981c42092016a37c59bf7"


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


    def _set_data(self, data):
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


class Tag(HasMediaElement):
    _primary_key = "name"
    _entry_data_path = ("TagPage", 0, "graphql", "hashtag")
    _base_url = "explore/tags/"
    _media_path = ("hashtag", "edge_hashtag_to_media")
    _media_query_hash = "ded47faa9a1aaded10161a2ff32abb6b"


    def __init__(self, name):
        self.name = name
        self.media_count = None

        self.media = set()
        self.top_posts = set()


    def _set_data(self, data):
        self.name = data["name"]
        self.media_count = data["edge_hashtag_to_media"]["count"]
        for node in data["edge_hashtag_to_top_posts"]["edges"]:
            self.top_posts.add(Media(node["node"]["shortcode"]))

class Comment(Element):
    _primary_key = "id"


    def __init__(self, id, media, owner, text, created_at):
        self.id = id
        self.media = media
        self.owner = owner
        self.text = text
        self.created_at = created_at
