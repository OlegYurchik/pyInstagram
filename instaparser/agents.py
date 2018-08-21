import hashlib
import json
import re
import requests
from requests.exceptions import HTTPError

from instaparser.entities import (Account, Comment, Element, HasMediaElement, Media, Location, Tag, \
    UpdatableElement)
from instaparser.exceptions import (AuthException, ExceptionManager, http_response_handler, \
    InstagramException, InternetException, UnexpectedResponse, NotUpdatedElement)



exception_manager = ExceptionManager()
exception_manager[InternetException] = http_response_handler



class Agent:
    def __init__(self, settings={}):
        self._session = requests.Session()
        
        self.update(settings=settings)


    @exception_manager.decorator
    def update(self, obj=None, settings={}):
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(obj, UpdatableElement) and not obj is None:
            raise TypeError("obj must be UpdatableElement type or None")
        
        query = "https://www.instagram.com/"
        if not obj is None:
            query += obj._base_url+getattr(obj, obj._primary_key)
        
        response = self._get_request(query, **settings)

        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                response.text,
            )
            data = json.loads(match.group(1))
            self._rhx_gis = data["rhx_gis"]
            self._csrf_token = data["config"]["csrf_token"]
            
            if obj is None:
                return None
            
            data = data["entry_data"]
            for key in obj._entry_data_path:
                data=data[key]
            obj._set_data(data)
            
            return data
        except (AttributeError, KeyError, ValueError):
            raise UnexpectedResponse(response.url, response.text)


    @exception_manager.decorator
    def get_media(self, obj, pointer=None, count=12, settings={}, limit=50):
        if not isinstance(obj, HasMediaElement):
            raise TypeError("'obj' must be HasMediaElement type")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        
        data = self.update(obj, settings)
        
        variables_string = '{{"{name}":"{name_value}","first":{first},"after":"{after}"}}'
        medias = []

        if pointer is None:
            try:
                data = data[obj._media_path[-1]]
                
                page_info = data["page_info"]
                edges = data["edges"]
                
                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    m = Media(node["shortcode"])
                    m._set_data(node)
                    if isinstance(obj, Account):
                        m.likes_count = node["edge_media_preview_like"]["count"]
                        m.owner = obj
                    else:
                        m.likes_count = node["edge_liked_by"]
                    
                    obj.media.add(m)
                    medias.append(m)
                
                if page_info["has_next_page"]:
                    pointer = page_info["end_cursor"]
                
                if len(edges) < count and page_info["has_next_page"]:
                    count = count-len(edges)
                else:
                    return medias, pointer
                
            except (ValueError, KeyError):
                raise UnexpectedResponse()

        if not "params" in settings:
            settings["params"] = {"query_hash": obj._media_query_hash}
        else:
            settings['params']['query_hash'] = obj._media_query_hash

        while True:
            data = {"after": pointer, "first": min(limit, count)}
            if isinstance(obj, Tag):
                data["name"] = "tag_name"
                data["name_value"] = obj.name
            else:
                data["name"] = "id"
                data["name_value"] = obj.id

            settings["params"]["variables"] = variables_string.format(**data)
            if not "headers" in settings:
                settings["headers"] = {
                    "X-Instagram-GIS": "%s:%s" % (self._rhx_gis, settings["params"]["variables"]),
                }
            else:
                settings["headers"]["X-Instagram-GIS"] = \
                    "%s:%s" % (self._rhx_gis, settings["params"]["variables"])
            settings["headers"]["X-Instagram-GIS"] = \
                hashlib.md5(settings["headers"]["X-Instagram-GIS"].encode("utf-8")).hexdigest()
            settings["headers"]["X-Requested-With"] = "XMLHttpRequest"
            
            response = self._get_request("https://www.instagram.com/graphql/query/", **settings)
            
            try:
                data = response.json()["data"]
                for key in obj._media_path:
                    data = data[key]
                page_info = data["page_info"]
                edges = data["edges"]
                
                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    m = Media(node["shortcode"])
                    m._set_data(node)
                    if isinstance(obj, Account):
                        m.likes_count = node["edge_media_preview_like"]["count"]
                        m.owner = obj
                    else:
                        m.likes_count = node["edge_liked_by"]
                    obj.media.add(m)
                    medias.append(m)
                
                if page_info["has_next_page"]:
                    pointer = page_info["end_cursor"]
                else:
                    pointer = None
                
                if len(edges) < count and page_info["has_next_page"]:
                    count = count-len(edges)
                else:
                    return medias, pointer
                
            except (ValueError, KeyError):
                raise UnexpectedResponse(response.url, response.text)


    @exception_manager.decorator
    def get_likes(self, media, settings={}):
        # Check data
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        data = self.update(media, settings)
        likes = []
        
        try:
            data = data["edge_media_preview_like"]
            edges = data["edges"]
            
            for edge in edges:
                node = edge["node"]
                account = Account(node["username"])
                account.id = node["id"]
                account.profile_pic_url = node["profile_pic_url"]
                if "is_verified" in node:
                    account.is_verified = node["is_verified"]
                if "full_name" in node:
                    account.full_name = node["full_name"]
                
                media.likes.add(account)
                likes.append(account)
        except (ValueError, KeyError):
            raise UnexpectedResponse()
        return likes, None


    @exception_manager.decorator
    def get_comments(self, media, pointer=None, count=35, settings={}, limit=50):
        # Check data
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")

        data = self.update(media, settings)

        query_hash = "33ba35852cb50da46f5b5e889df7d159"
        variables_string =  '{{"shortcode":"{code}","first":{first},"after":"{after}"}}'
        comments = []

        if pointer is None:
            try:
                data = data["edge_media_to_comment"]
                edges = data["edges"]
                page_info = data["page_info"]
                
                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    c = Comment(node["id"], media=media,
                                owner=Account(node["owner"]["username"]),
                                text=node["text"],
                                created_at=node["created_at"])
                    media.comments.add(c)
                    comments.append(c)
                
                if page_info["has_next_page"]:
                    pointer = page_info["end_cursor"]
                
                if len(edges) < count and not pointer is None:
                    count = count-len(edges)
                else:
                    return comments, pointer
            except (ValueError, KeyError):
                raise UnexpectedResponse(media)

        if not "params" in settings:
            settings["params"] = {"query_hash": query_hash}
        else:
            settings["params"]["query_hash"] = query_hash

        while True:
            data = {"after": pointer, "code": media.code, "first": min(limit, count)}
            
            settings["params"]["variables"] = variables_string.format(**data)
            if not "headers" in settings:
                settings["headers"] = {
                    "X-Instagram-GIS": "%s:%s" % (self._rhx_gis, settings["params"]["variables"]),
                }
            else:
                settings["headers"]["X-Instagram-GIS"] = \
                    "%s:%s" % (self._rhx_gis, settings["params"]["variables"])
            settings["headers"]["X-Instagram-GIS"] = \
                hashlib.md5(settings["headers"]["X-Instagram-GIS"].encode("utf-8")).hexdigest()
            settings["headers"]["X-Requested-With"] = "XMLHttpRequest"

            response = self._get_request("https://www.instagram.com/graphql/query/", **settings)

            try:
                data = response.json()["data"]["shortcode_media"]["edge_media_to_comment"]
                media.comments_count = data["count"]
                edges = data["edges"]
                page_info = data["page_info"]
                
                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    c = Comment(node["id"],
                                media=media,
                                owner=Account(node["owner"]["username"]),
                                text=node["text"],
                                created_at=node["created_at"])
                    media.comments.add(c)
                    comments.append(c)
                
                if page_info["has_next_page"]:
                    pointer = page_info["end_cursor"]
                else:
                    pointer = None
                    
                if len(edges) < count and page_info["has_next_page"]:
                    count = count-len(edges)
                else:
                    return comments, pointer
            except (ValueError, KeyError):
                raise UnexpectedResponse(response.url, response.text)


    def _get_request(self, *args, **kwargs):
        try:
            response = self._session.get(*args, **kwargs)
            response.raise_for_status()
            return response
        except HTTPError as e:
            raise InternetException(e)


    def _post_request(self, *args, **kwargs):
        try:
            response = self._session.post(*args, **kwargs)
            response.raise_for_status()
            return response
        except HTTPError as e:
            raise InternetException(e)


class AgentAccount(Account, Agent):
    @exception_manager.decorator
    def __init__(self, login, password, settings={}):
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")

        Account.__init__(self, login)
        Agent.__init__(self, settings=settings)

        data = {"username": self.login, "password": password}
        
        if "headers" in settings:
            settings["headers"]["X-CSRFToken"] = self._csrf_token
            settings["headers"]["referer"] = "https://www.instagram.com/"
        else:
            settings["headers"] = {
                "X-CSRFToken": self._csrf_token,
                "referer": "https://www.instagram.com/",
            }

        response = self._post_request("https://www.instagram.com/accounts/login/ajax/",
                                      data=data, **settings)

        try:
            data = response.json()
            if not data["authenticated"]:
                raise AuthException(self.login) 
        except (ValueError, KeyError):
            raise UnexpectedResponse(response.url, response.text)

    @exception_manager.decorator
    def update(self, obj=None, settings={}):
        if obj is None:
            obj = self
        return super().update(obj, settings)

    @exception_manager.decorator
    def get_media(self, obj, pointer=None, count=12, settings={}, limit=12):
        return super().get_media(obj, pointer, count, settings, limit)

    @exception_manager.decorator
    def get_likes(self, media, pointer=None, count=20, settings={}, limit=50):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")

        self.update(media, settings)
        
        query_hash = "1cb6ec562846122743b61e492c85999f"
        if pointer:
            variables_string = '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
        else:
            variables_string = '{{"shortcode":"{shortcode}","first":{first}}}'
        likes = []

        if "params" in settings:
            settings["params"]["query_hash"] = query_hash
                
        else:
            settings["params"] = {"query_hash": query_hash}

        while True:
            data = {"shortcode": media.code, "first": min(limit, count)}
            if pointer:
                data["after"] = pointer

            settings["params"]["variables"] = variables_string.format(**data)
            if not "headers" in settings:
                settings["headers"] = {
                    "X-Instagram-GIS": "%s:%s" % (self._rhx_gis, settings["params"]["variables"]),
                }
            else:
                settings["headers"]["X-Instagram-GIS"] = \
                    "%s:%s" % (self._rhx_gis, settings["params"]["variables"])
            settings["headers"]["X-Instagram-GIS"] = \
                hashlib.md5(settings["headers"]["X-Instagram-GIS"].encode("utf-8")).hexdigest()
            settings["headers"]["X-Requested-With"] = "XMLHttpRequest"

            response = self._get_request("https://www.instagram.com/graphql/query/", **settings)

            try:
                data = response.json()["data"]["shortcode_media"]["edge_liked_by"]
                edges = data["edges"]
                page_info = data["page_info"]
                media.likes_count = data["count"]
                
                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    account = Account(node["username"])
                    account.id = node["id"]
                    account.profile_pic_url = node["profile_pic_url"]
                    account.is_verified = node["is_verified"]
                    account.full_name = node["full_name"]
                    media.likes.add(account)
                    likes.append(account)
                
                if page_info["has_next_page"]:
                    pointer = page_info["end_cursor"]
                else:
                    pointer = None
                
                if len(edges) < count and page_info["has_next_page"]:
                    count = count-len(edges)
                    variables_string = \
                        '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
                else:
                    return likes, pointer
            except (ValueError, KeyError):
                raise UnexpectedResponse(response.url, response.text)


    @exception_manager.decorator
    def get_follows(self, account=None, pointer=None, count=20, settings={}, limit=50):
        if account is None:
            account = self
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")
        if not isinstance(count, int):
            raise TypeError("'limit' must be int type")

        self.update(account, settings)

        query_hash = "58712303d941c6855d4e888c5f0cd22f"
        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        follows = []

        if not "params" in settings:
            settings["params"] = {"query_hash": query_hash}
        else:
            settings["params"]["query_hash"] = query_hash

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if not pointer is None:
                data["after"] = pointer
            
            settings["params"]["variables"] = variables_string.format(**data)
            if not "headers" in settings:
                settings["headers"] = {
                    "X-Instagram-GIS": "%s:%s" % (self._rhx_gis, settings["params"]["variables"]),
                }
            else:
                settings["headers"]["X-Instagram-GIS"] = \
                    "%s:%s" % (self._rhx_gis, settings["params"]["variables"])
            settings["headers"]["X-Instagram-GIS"] = \
                hashlib.md5(settings["headers"]["X-Instagram-GIS"].encode("utf-8")).hexdigest()
            settings["headers"]["X-Requested-With"] = "XMLHttpRequest"

            response = self._get_request("https://www.instagram.com/graphql/query/", **settings)

            try:
                data = response.json()["data"]["user"]["edge_follow"]
                edges = data["edges"]
                page_info = data["page_info"]
                account.follows_count = data["count"]
                
                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    a = Account(node["username"])
                    a.id = node["id"]
                    a.profile_pic_url = node["profile_pic_url"]
                    a.is_verified = node["is_verified"]
                    a.full_name = node["full_name"]
                    account.follows.add(a)
                    follows.append(a)
                
                if page_info["has_next_page"]:
                    pointer = page_info["end_cursor"]
                else:
                    pointer = None
                
                if len(edges) < count and page_info["has_next_page"]:
                    count = count-len(edges)
                    variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                else:
                    return follows, pointer
            except (ValueError, KeyError):
                raise UnexpectedResponse(response.url, response.text)


    @exception_manager.decorator
    def get_followers(self, account=None, pointer=None, count=20, settings={}, limit=50):
        if account is None:
            account = self
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")

        self.update(account, settings)
        
        query_hash = "37479f2b8209594dde7facb0d904896a"
        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        followers = []

        if "params" in settings:
            settings["params"]["query_hash"] = query_hash
        else:
            settings["params"] = {"query_hash": query_hash}

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if not pointer is None:
                data["after"] = pointer
            
            settings["params"]["variables"] = variables_string.format(**data)
            if not "headers" in settings:
                settings["headers"] = {
                    "X-Instagram-GIS": "%s:%s" % (self._rhx_gis, settings["params"]["variables"]),
                }
            else:
                settings["headers"]["X-Instagram-GIS"] = \
                    "%s:%s" % (self._rhx_gis, settings["params"]["variables"])
            settings["headers"]["X-Instagram-GIS"] = \
                hashlib.md5(settings["headers"]["X-Instagram-GIS"].encode("utf-8")).hexdigest()
            settings["headers"]["X-Requested-With"] = "XMLHttpRequest"

            response = self._get_request("https://www.instagram.com/graphql/query/", **settings)

            try:
                data = response.json()["data"]["user"]["edge_followed_by"]
                edges = data["edges"]
                page_info = data["page_info"]
                account.followers_count = data["count"]
                
                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    a = Account(node["username"])
                    a.id = node["id"]
                    a.profile_pic_url = node["profile_pic_url"]
                    a.is_verified = node["is_verified"]
                    a.full_name = node["full_name"]
                    account.followers.add(a)
                    followers.append(a)
                
                if page_info["has_next_page"]:
                    pointer = page_info["end_cursor"]
                else:
                    pointer = None
                
                if len(edges) < count and page_info["has_next_page"]:
                    count = count-len(edges)
                    variables_query = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                else:
                    return followers, pointer
            except (ValueError, KeyError):
                raise UnexpectedResponse(response.url, response.text)


    @exception_manager.decorator
    def feed(self, pointer=None, count=12, settings={}, limit=50):
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")

        query_hash = "485c25657308f08317c1e4b967356828"
        variables_string = '{{"fetch_media_item_count":{first},"fetch_media_item_cursor":"{after}",\
            "fetch_comment_count":4,"fetch_like":10,"has_stories":false}}'
        feed = []

        if "params" in settings:
            settings["params"]["query_hash"] = query_hash 
        else:
            settings["params"] = {"query_hash": query_hash}

        while True:
            if pointer:
                settings["params"]["variables"] = variables_string.format(after=pointer,
                                                                          first=min(limit, count))
            else:
                settings["params"]["variables"]="{}"
            
            if not "headers" in settings:
                settings["headers"] = {
                    "X-Instagram-GIS": "%s:%s" % (self._rhx_gis, settings["params"]["variables"]),
                }
            else:
                settings["headers"]["X-Instagram-GIS"] = \
                    "%s:%s" % (self._rhx_gis, settings["params"]["variables"])
            settings["headers"]["X-Instagram-GIS"] = \
                hashlib.md5(settings["headers"]["X-Instagram-GIS"].encode("utf-8")).hexdigest()
            settings["headers"]["X-Requested-With"] = "XMLHttpRequest"

            response = self._get_request("https://www.instagram.com/graphql/query/", **settings)

            try:
                data = response.json()["data"]["user"]["edge_web_feed_timeline"]
                edges = data["edges"]
                page_info = data["page_info"]
                length = len(edges)
                
                for index in range(min(length, count)):
                    node = edges[index]["node"]
                    if not "shortcode" in node:
                        length -= 1
                        continue
                    m = Media(node["shortcode"])
                    m._set_data(node)
                    feed.append(m)
                
                if page_info["has_next_page"]:
                    pointer = page_info["end_cursor"]
                else:
                    pointer = None
                
                if length < count and page_info["has_next_page"]:
                    count = count-length
                else:
                    return feed, pointer
            except (ValueError, KeyError):
                raise UnexpectedResponse(response.url, response.text)


    @exception_manager.decorator
    def like(self, media, settings={}):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if media.id is None:
            self.update(media)

        response = \
            self._action_request(referer="https://www.instagram.com/p/%s/" % media.code,
                                 url="https://www.instagram.com/web/likes/%s/like/" % media.id,
                                 )

        try:
            return response.json()["status"] == "ok"
        except (ValueError, KeyError):
            raise UnexpectedResponse(response.url, response.text)


    @exception_manager.decorator
    def unlike(self, media, settings={}):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if media.id is None:
            self.update(media)

        response = \
            self._action_request(referer="https://www.instagram.com/p/%s/" % media.code,
                                 url="https://www.instagram.com/web/likes/%s/unlike/" % media.id,
                                 )

        try:
            return response.json()["status"] == "ok"
        except (ValueError, KeyError):
            raise UnexpectedResponse(response.url, response.text)


    @exception_manager.decorator
    def add_comment(self, media, text, settings={}):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(text, str):
            raise TypeError("'text' must be str type")
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if media.id is None:
            self.update(media)

        response = \
            self._action_request(referer="https://www.instagram.com/p/%s/" % media.code,
                                 url="https://www.instagram.com/web/comments/%s/add/" % media.id,
                                 data={"comment_text": text}
                                 )

        try:
            data = response.json()
            if data["status"] == "ok":
                comment = Comment(
                    data["id"],
                    media=media,
                    owner=self,
                    text=data["text"],
                    created_at=data["created_time"],
                )
                return comment
            return None
        except (ValueError, KeyError):
            raise UnexpectedResponse(response.url, response.text)


    @exception_manager.decorator
    def delete_comment(self, comment, settings={}):
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(comment, Comment):
            raise TypeError("'comment' must be Comment type")
        if comment.media.id is None:
            self.update(comment.media)

        response = \
            self._action_request(referer="https://www.instagram.com/p/%s/" % comment.media.code,
                                 url="https://www.instagram.com/web/comments/%s/delete/%s/" % \
                                    (comment.media.id, comment.id)
                                )

        try:
            if response.json()["status"] == "ok":
                del comment
                return True
            else:
                return False
        except (ValueError, KeyError):
            raise UnexpectedResponse(response.url, response.text)


    @exception_manager.decorator
    def follow(self, account, settings={}):
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")
        if account.id is None:
            self.update(account)

        response = \
            self._action_request(referer="https://www.instagram.com/%s" % account.login,
                                 url="https://www.instagram.com/web/friendships/%s/follow/" % \
                                    account.id
                                )

        try:
            return response.json()["status"] == "ok"
        except (ValueError, KeyError):
            raise UnexpectedResponse(response.url, response.text)

    @exception_manager.decorator
    def unfollow(self, account, settings={}):
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")
        if account.id is None:
            self.update(account)

        response = \
            self._action_request(referer="https://www.instagram.com/%s" % account.login,
                                 url="https://www.instagram.com/web/friendships/%s/unfollow/" % \
                                    account.id
                                )

        try:
            return response.json()["status"] == "ok"
        except (ValueError, KeyError):
            raise UnexpectedResponse(response.url, response.text)

    def _action_request(self, referer, url, data={}, settings={}):
        if not isinstance(settings, dict):
            raise TypeError("'settings' must be dict type")
        if not isinstance(data, dict):
            raise TypeError("'data' must be dict type")
        if not isinstance(referer, str):
            raise TypeError("'referer' must be str type")
        if not isinstance(url, str):
            raise TypeError("'url' must be str type")

        headers = {
            "referer": referer,
            "x-csrftoken": self._session.cookies["csrftoken"],
            "x-instagram-ajax": "1",
            "x-requested-with": "XMLHttpRequest",
        }
        if "headers" in settings:
            settings["headers"].update(headers)
        else:
            settings["headers"] = headers
        if "data" in settings:
            settings["data"].update(data)
        else:
            settings["data"] = data

        response = self._post_request(url, **settings)
        return response
