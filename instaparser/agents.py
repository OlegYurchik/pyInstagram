import aiohttp
import asyncio
import hashlib
from instaparser.entities import (Account, Comment, Element, HasMediaElement,Media, Location, Story,
                                  Tag, UpdatableElement)
from instaparser.exceptions import (AuthException, ExceptionManager, InstagramException,
                                    InternetException, UnexpectedResponse, NotUpdatedElement)
import json
import re
import requests
from requests.exceptions import HTTPError
from time import sleep


exception_manager = ExceptionManager()


class Agent:
    def __init__(self, settings=None):
        self.rhx_gis = None
        self.csrf_token = None
        self.session = requests.Session()
        
        self.update(settings=settings)

    @exception_manager.decorator
    def update(self, obj=None, settings=None):
        if not isinstance(obj, UpdatableElement) and not obj is None:
            raise TypeError("obj must be UpdatableElement type or None")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()
        
        query = "https://www.instagram.com/"
        if not obj is None:
            query += obj.base_url + getattr(obj, obj.primary_key)
        
        response = self.get_request(query, **settings)

        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                response.text,
            )
            data = json.loads(match.group(1))
            self.rhx_gis = data["rhx_gis"]
            self.csrf_token = data["config"]["csrf_token"]
            
            if obj is None:
                return None
            
            data = data["entry_data"]
            for key in obj.entry_data_path:
                data=data[key]
            obj.set_data(data)
            
            return data
        except (AttributeError, KeyError, ValueError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_media(self, obj, pointer=None, count=12, limit=50, delay=0, settings=None):
        if not isinstance(obj, HasMediaElement):
            raise TypeError("'obj' must be HasMediaElement type")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        data = self.update(obj, settings=settings)
        
        variables_string = '{{"{name}":"{name_value}","first":{first},"after":"{after}"}}'
        medias = []

        if pointer is None:
            try:
                data = data[obj.media_path[-1]]
                
                page_info = data["page_info"]
                edges = data["edges"]
                
                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    m = Media(node["shortcode"])
                    m.set_data(node)
                    if isinstance(obj, Account):
                        m.likes_count = node["edge_media_preview_like"]["count"]
                        m.owner = obj
                    else:
                        m.likes_count = node["edge_liked_by"]
                    
                    obj.media.add(m)
                    medias.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                else:
                    return medias, pointer

            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(
                    exception,
                    "https://www.instagram.com/" + obj.base_url + getattr(obj, obj.primary_key),
                )

        while True:
            data = {"after": pointer, "first": min(limit, count)}
            if isinstance(obj, Tag):
                data["name"] = "tag_name"
                data["name_value"] = obj.name
            else:
                data["name"] = "id"
                data["name_value"] = obj.id

            response = self.graphql_request(
                query_hash=obj.media_query_hash,
                variables=variables_string.format(**data),
                settings=settings,
            )
            
            try:
                data = response.json()["data"]
                for key in obj.media_path:
                    data = data[key]
                page_info = data["page_info"]
                edges = data["edges"]
                
                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    m = Media(node["shortcode"])
                    m.set_data(node)
                    if isinstance(obj, Account):
                        m.likes_count = node["edge_media_preview_like"]["count"]
                        m.owner = obj
                    else:
                        m.likes_count = node["edge_liked_by"]
                    obj.media.add(m)
                    medias.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    sleep(delay)
                else:
                    return medias, pointer
                
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_likes(self, media, pointer=None, count=20, limit=50, delay=0, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.update(media, settings=settings)

        if pointer:
            variables_string = '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
        else:
            variables_string = '{{"shortcode":"{shortcode}","first":{first}}}'
        likes = []

        while True:
            data = {"shortcode": media.code, "first": min(limit, count)}
            if pointer:
                data["after"] = pointer

            response = self.graphql_request(
                query_hash="1cb6ec562846122743b61e492c85999f",
                variables=variables_string.format(**data),
                settings=settings,
            )

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

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count-len(edges)
                    variables_string = \
                        '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
                    sleep(delay)
                else:
                    return likes, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_comments(self, media, pointer=None, count=35, limit=32, delay=0, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        data = self.update(media, settings=settings)

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

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and not pointer is None:
                    count = count-len(edges)
                else:
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, media)

        variables_string =  '{{"shortcode":"{code}","first":{first},"after":"{after}"}}'
        while True:
            data = {"after": pointer, "code": media.code, "first": min(limit, count)}

            response = self.graphql_request(
                query_hash="f0986789a5c5d17c2400faebf16efd0d",
                variables=variables_string.format(**data),
                settings=settings,
            )

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
                
                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    sleep(delay)
                else:
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    def graphql_request(self, query_hash, variables, settings=None):
        if not isinstance(query_hash, str):
            raise TypeError("'query_hash' must be str type")
        if not isinstance(variables, str):
            raise TypeError("'variables' must be str type")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        if not "params" in settings:
            settings["params"] = dict() 
        settings["params"].update({"query_hash": query_hash})

        settings["params"]["variables"] = variables
        gis = "%s:%s" % (self.rhx_gis, variables)
        if not "headers" in settings:
            settings["headers"] = dict()
        settings["headers"].update({
            "X-IG-App-ID": "936619743392459",
            "X-Instagram-GIS": hashlib.md5(gis.encode("utf-8")).hexdigest(),
            "X-Requested-With": "XMLHttpRequest",
        })

        return self.get_request("https://www.instagram.com/graphql/query/", **settings)

    def action_request(self, referer, url, data=None, settings=None):
        if not isinstance(referer, str):
            raise TypeError("'referer' must be str type")
        if not isinstance(url, str):
            raise TypeError("'url' must be str type")
        if not isinstance(data, dict) and not data is None:
            raise TypeError("'data' must be dict type or None")
        data = dict() if data is None else data.copy()
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        headers = {
            "Referer": referer,
            "X-CSRFToken": self.csrf_token,
            "X-Instagram-Ajax": "1",
            "X-Requested-With": "XMLHttpRequest",
        }
        if "headers" in settings:
            settings["headers"].update(headers)
        else:
            settings["headers"] = headers
        if "data" in settings:
            settings["data"].update(data)
        else:
            settings["data"] = data

        response = self.post_request(url, **settings)
        return response

    def get_request(self, *args, **kwargs):
        try:
            response = self.session.get(*args, **kwargs)
            response.raise_for_status()
            return response
        except (requests.exceptions.RequestException, ConnectionResetError) as exception:
            raise InternetException(exception)

    def post_request(self, *args, **kwargs):
        try:
            response = self.session.post(*args, **kwargs)
            response.raise_for_status()
            return response
        except (requests.exceptions.RequestException, ConnectionResetError) as exception:
            raise InternetException(exception)


class AsyncAgent:
    @classmethod
    async def create(cls, settings=None):
        agent = cls()
        await agent.__ainit__(settings=settings)
        return agent

    async def delete(self):
        await self.session.close()

    async def __ainit__(self, settings=None):
        self.rhx_gix = None
        self.csrf_token = None
        self.session = aiohttp.ClientSession(raise_for_status=True)

        await self.update(settings=settings)

    @exception_manager.decorator
    async def update(self, obj=None, settings=None):
        if not isinstance(obj, UpdatableElement) and not obj is None:
            raise TypeError("obj must be UpdatableElement type or None")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()
        
        query = "https://www.instagram.com/"
        if not obj is None:
            query += obj.base_url + getattr(obj, obj.primary_key)
        
        response = await self.get_request(query, **settings)

        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                await response.text(),
            )
            data = json.loads(match.group(1))
            self.rhx_gis = data["rhx_gis"]
            self.csrf_token = data["config"]["csrf_token"]
            
            if obj is None:
                return None
            
            data = data["entry_data"]
            for key in obj.entry_data_path:
                data = data[key]
            obj.set_data(data)
            
            return data
        except (AttributeError, KeyError, ValueError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def get_media(self, obj, pointer=None, count=12, limit=50, delay=0, settings=None):
        if not isinstance(obj, HasMediaElement):
            raise TypeError("'obj' must be HasMediaElement type")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        data = await self.update(obj, settings=settings)
        
        variables_string = '{{"{name}":"{name_value}","first":{first},"after":"{after}"}}'
        medias = []

        if pointer is None:
            try:
                data = data[obj.media_path[-1]]
                
                page_info = data["page_info"]
                edges = data["edges"]
                
                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    m = Media(node["shortcode"])
                    m.set_data(node)
                    if isinstance(obj, Account):
                        m.likes_count = node["edge_media_preview_like"]["count"]
                        m.owner = obj
                    else:
                        m.likes_count = node["edge_liked_by"]
                    
                    obj.media.add(m)
                    medias.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                else:
                    return medias, pointer
                
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(
                    exception,
                    "https://www.instagram.com/" + obj.base_url + getattr(obj, obj.primary_key),
                )

        while True:
            data = {"after": pointer, "first": min(limit, count)}
            if isinstance(obj, Tag):
                data["name"] = "tag_name"
                data["name_value"] = obj.name
            else:
                data["name"] = "id"
                data["name_value"] = obj.id

            response = await self.graphql_request(
                query_hash=obj.media_query_hash,
                variables=variables_string.format(**data),
                settings=settings,
            )
            
            try:
                data = (await response.json())["data"]
                for key in obj.media_path:
                    data = data[key]
                page_info = data["page_info"]
                edges = data["edges"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    m = Media(node["shortcode"])
                    m.set_data(node)
                    if isinstance(obj, Account):
                        m.likes_count = node["edge_media_preview_like"]["count"]
                        m.owner = obj
                    else:
                        m.likes_count = node["edge_liked_by"]
                    obj.media.add(m)
                    medias.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    await asyncio.sleep(delay)
                else:
                    return medias, pointer
                
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def get_likes(self, media, pointer=None, count=20, limit=50, delay=0, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        await self.update(media, settings=settings)

        if pointer:
            variables_string = '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
        else:
            variables_string = '{{"shortcode":"{shortcode}","first":{first}}}'
        likes = []

        while True:
            data = {"shortcode": media.code, "first": min(limit, count)}
            if pointer:
                data["after"] = pointer

            response = await self.graphql_request(
                query_hash="1cb6ec562846122743b61e492c85999f",
                variables=variables_string.format(**data),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["shortcode_media"]["edge_liked_by"]
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

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count-len(edges)
                    variables_string = \
                        '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
                    await asyncio.sleep(delay)
                else:
                    return likes, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def get_comments(self, media, pointer=None, count=35, limit=32, delay=0, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        data = await self.update(media, settings=settings)

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

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and not pointer is None:
                    count = count - len(edges)
                else:
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, media)

        variables_string =  '{{"shortcode":"{code}","first":{first},"after":"{after}"}}'
        while True:
            data = {"after": pointer, "code": media.code, "first": min(limit, count)}

            response = await self.graphql_request(
                query_hash="f0986789a5c5d17c2400faebf16efd0d",
                variables=variables_string.format(**data),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["shortcode_media"]["edge_media_to_comment"]
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
                
                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    await asyncio.sleep(delay)
                else:
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    async def graphql_request(self, query_hash, variables, settings=None):
        if not isinstance(query_hash, str):
            raise TypeError("'query_hash' must be str type")
        if not isinstance(variables, str):
            raise TypeError("'variables' must be str type")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        if not "params" in settings:
            settings["params"] = dict() 
        settings["params"].update({"query_hash": query_hash})

        settings["params"]["variables"] = variables
        gis = "%s:%s" % (self.rhx_gis, variables)
        if not "headers" in settings:
            settings["headers"] = dict()
        settings["headers"].update({
            "X-IG-App-ID": "936619743392459",
            "X-Instagram-GIS": hashlib.md5(gis.encode("utf-8")).hexdigest(),
            "X-Requested-With": "XMLHttpRequest",
        })

        return await self.get_request("https://www.instagram.com/graphql/query/", **settings)

    async def action_request(self, referer, url, data=None, settings=None):
        if not isinstance(referer, str):
            raise TypeError("'referer' must be str type")
        if not isinstance(url, str):
            raise TypeError("'url' must be str type")
        if not isinstance(data, dict) and not data is None:
            raise TypeError("'data' must be dict type or None")
        data = dict() if data is None else data.copy()
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        headers = {
            "Referer": referer,
            "X-CSRFToken": self.csrf_token,
            "X-Instagram-AJAX": "1",
            "X-Requested-With": "XMLHttpRequest",
        }
        if "headers" in settings:
            settings["headers"].update(headers)
        else:
            settings["headers"] = headers
        if "data" in settings:
            settings["data"].update(data)
        else:
            settings["data"] = data

        response = await self.post_request(url, **settings)
        return response

    async def get_request(self, *args, **kwargs):
        try:
            response = await self.session.get(*args, **kwargs)
            return response
        except Exception as exception:
            raise InternetException(exception)

    async def post_request(self, *args, **kwargs):
        try:
            response = await self.session.post(*args, **kwargs)
            return response
        except Exception as exception:
            raise InternetException(exception)


class AgentAccount(Account, Agent):
    @exception_manager.decorator
    def __init__(self, login, password, settings=None):
        if not isinstance(login, str):
            raise TypeError("'login' must be str type")
        if not isinstance(password, str):
            raise TypeError("'password' must be str type")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        Account.__init__(self, login)
        Agent.__init__(self, settings=settings)
        
        if "headers" in settings:
            settings["headers"].update({
                # "X-IG-App-ID": "936619743392459",
                # "X_Instagram-AJAX": "ee72defd9231",
                "X-CSRFToken": self.csrf_token,
                "Referer": "https://www.instagram.com/",
            })
        else:
            settings["headers"] = {
                # "X-IG-App-ID": "936619743392459",
                # "X_Instagram-AJAX": "ee72defd9231",
                "X-CSRFToken": self.csrf_token,
                "Referer": "https://www.instagram.com/",
            }
        if "data" in settings:
            settings["data"].update({"username": self.login, "password": password})
        else:
            settings["data"] = {"username": self.login, "password": password}

        response = self.post_request("https://www.instagram.com/accounts/login/ajax/", **settings)

        try:
            data = response.json()
            if not data["authenticated"]:
                raise AuthException(self.login) 
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def update(self, obj=None, settings=None):
        if obj is None:
            obj = self
        return Agent.update(self, obj, settings=settings)

    @exception_manager.decorator
    def get_media(self, obj=None, pointer=None, count=12, limit=12, delay=0, settings=None):
        if obj is None:
            obj = self
        return Agent.get_media(self, obj, pointer=pointer, count=count, limit=limit, delay=delay,
                               settings=settings)

    @exception_manager.decorator
    def get_follows(self, account=None, pointer=None, count=20, limit=50, delay=0, settings=None):
        if account is None:
            account = self
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type or None")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(count, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        follows = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if not pointer is None:
                data["after"] = pointer

            response = self.graphql_request(
                query_hash="58712303d941c6855d4e888c5f0cd22f",
                variables=variables_string.format(**data),
                settings=settings,
            )

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
                
                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None
                
                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                    sleep(delay)
                else:
                    return follows, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_followers(self, account=None, pointer=None, count=20, limit=50, delay=0, settings=None):
        if account is None:
            account = self
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type or None")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        followers = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if not pointer is None:
                data["after"] = pointer

            response = self.graphql_request(
                query_hash="37479f2b8209594dde7facb0d904896a",
                variables=variables_string.format(**data),
                settings=settings,
            )

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

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                    sleep(delay)
                else:
                    return followers, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def stories(self, settings=None):
        response = self.graphql_request(
            query_hash="60b755363b5c230111347a7a4e242001",
            variables='{"only_stories":true}',
            settings=settings,
        )

        try:
            data = response.json()["data"]["user"]["feed_reels_tray"]["edge_reels_tray_to_reel"]
            return [Story(edge["node"]["id"]) for edge in data["edges"]]
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def feed(self, pointer=None, count=12, limit=50, delay=0, settings=None):
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        variables_string = '{{"fetch_media_item_count":{first},"fetch_media_item_cursor":"{after}",\
            "fetch_comment_count":4,"fetch_like":10,"has_stories":false}}'
        feed = []

        while True:
            response = self.graphql_request(
                query_hash="485c25657308f08317c1e4b967356828",
                variables=variables_string.format(
                    after=pointer,
                    first=min(limit, count),
                ) if pointer else "{}",
                settings=settings,
            )

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
                    m.set_data(node)
                    feed.append(m)
                
                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None
                
                if length < count and page_info["has_next_page"]:
                    count -= length
                    sleep(delay)
                else:
                    return feed, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def like(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        
        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/likes/%s/like/" % media.id,
            settings=settings,
        )

        try:
            return response.json()["status"] == "ok"
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def unlike(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/likes/%s/unlike/" % media.id,
            settings=settings,
        )

        try:
            return response.json()["status"] == "ok"
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def add_comment(self, media, text, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(text, str):
            raise TypeError("'text' must be str type")

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/comments/%s/add/" % media.id,
            data={"comment_text": text},
            settings=settings,
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
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def delete_comment(self, comment, settings=None):
        if not isinstance(comment, Comment):
            raise TypeError("'comment' must be Comment type")

        if comment.media.id is None:
            self.update(comment.media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % comment.media.code,
            url="https://www.instagram.com/web/comments/%s/delete/%s/" % (
                comment.media.id,
                comment.id,
            ),
            settings=settings,
        )

        try:
            if response.json()["status"] == "ok":
                del comment
                return True
            else:
                return False
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def follow(self, account, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        if account.id is None:
            self.update(account, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/%s" % account.login,
            url="https://www.instagram.com/web/friendships/%s/follow/" % account.id,
            settings=settings,
        )

        try:
            return response.json()["status"] == "ok"
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def unfollow(self, account, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        if account.id is None:
            self.update(account, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/%s" % account.login,
            url="https://www.instagram.com/web/friendships/%s/unfollow/" % account.id,
            settings=settings,
        )

        try:
            return response.json()["status"] == "ok"
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)


class AsyncAgentAccount(Account, AsyncAgent):
    @classmethod
    async def create(cls, login, password, settings=None):
        agent = cls(login, password, settings=settings)
        await agent.__ainit__(login, password, settings=settings)
        return agent

    def __init__(self, login, password, settings=None):
        pass

    def __del__(self):
        Account.__del__(self)
        self.session.close()

    @exception_manager.decorator
    async def __ainit__(self, login, password, settings=None):
        if not isinstance(login, str):
            raise TypeError("'login' must be str type")
        if not isinstance(password, str):
            raise TypeError("'password' must be str type")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        Account.__init__(self, login)
        await AsyncAgent.__ainit__(self, settings=settings)
        
        if "headers" in settings:
            settings["headers"].update({
                # "X-IG-App-ID": "936619743392459",
                # "X_Instagram-AJAX": "ee72defd9231",
                "X-CSRFToken": self.csrf_token,
                "Referer": "https://www.instagram.com/",
            })
        else:
            settings["headers"] = {
                # "X-IG-App-ID": "936619743392459",
                # "X_Instagram-AJAX": "ee72defd9231",
                "X-CSRFToken": self.csrf_token,
                "Referer": "https://www.instagram.com/",
            }
        if "data" in settings:
            settings["data"].update({"username": self.login, "password": password})
        else:
            settings["data"] = {"username": self.login, "password": password}

        response = await self.post_request(
            "https://www.instagram.com/accounts/login/ajax/",
            **settings,
        )

        try:
            data = await response.json()
            if not data["authenticated"]:
                raise AuthException(self.login) 
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def update(self, obj=None, settings=None):
        if obj is None:
            obj = self
        return await AsyncAgent.update(self, obj, settings=settings)

    @exception_manager.decorator
    async def get_media(self, obj=None, pointer=None, count=12, limit=12, delay=0, settings=None):
        if obj is None:
            obj = self
        return await AsyncAgent.get_media(self, obj, pointer=pointer, count=count, limit=limit,
                                          delay=delay, settings=settings)

    @exception_manager.decorator
    async def get_follows(self, account=None, pointer=None, count=20, limit=50, delay=0,
                          settings=None):
        if account is None:
            account = self
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type or None")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(count, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        await self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        follows = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if not pointer is None:
                data["after"] = pointer

            response = await self.graphql_request(
                query_hash="58712303d941c6855d4e888c5f0cd22f",
                variables=variables_string.format(**data),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["user"]["edge_follow"]
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

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                    await asyncio.sleep(delay)
                else:
                    return follows, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def get_followers(self, account=None, pointer=None, count=20, limit=50, delay=0,
                            settings=None):
        if account is None:
            account = self
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type or None")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        await self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        followers = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if not pointer is None:
                data["after"] = pointer

            response = await self.graphql_request(
                query_hash="37479f2b8209594dde7facb0d904896a",
                variables=variables_string.format(**data),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["user"]["edge_followed_by"]
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
                
                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None
                
                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                    await asyncio.sleep(delay)
                else:
                    return followers, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def stories(self, settings=None):
        response = await self.graphql_request(
            query_hash="60b755363b5c230111347a7a4e242001",
            variables='{"only_stories":true}',
            settings=settings,
        )

        try:
            data = (await response.json())["data"]["user"]["feed_reels_tray"]
            data = data["edge_reels_tray_to_reel"]
            return [Story(edge["node"]["id"]) for edge in data["edges"]]
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def feed(self, pointer=None, count=12, limit=50, delay=0, settings=None):
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        variables_string = '{{"fetch_media_item_count":{first},"fetch_media_item_cursor":"{after}",\
            "fetch_comment_count":4,"fetch_like":10,"has_stories":false}}'
        feed = []

        while True:
            response = await self.graphql_request(
                query_hash="485c25657308f08317c1e4b967356828",
                variables=variables_string.format(
                    after=pointer,
                    first=min(limit, count),
                ) if pointer else "{}",
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["user"]["edge_web_feed_timeline"]
                edges = data["edges"]
                page_info = data["page_info"]
                length = len(edges)

                for index in range(min(length, count)):
                    node = edges[index]["node"]
                    if not "shortcode" in node:
                        length -= 1
                        continue
                    m = Media(node["shortcode"])
                    m.set_data(node)
                    feed.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if length < count and page_info["has_next_page"]:
                    count -= length
                    await asyncio.sleep(delay)
                else:
                    return feed, pointer
            except (ValueError, KeyError) as exception:
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def like(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        
        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/likes/%s/like/" % media.id,
            settings=settings,
        )

        try:
            return (await response.json())["status"] == "ok"
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def unlike(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/likes/%s/unlike/" % media.id,
            settings=settings,
        )

        try:
            return (await response.json())["status"] == "ok"
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def add_comment(self, media, text, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(text, str):
            raise TypeError("'text' must be str type")

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/comments/%s/add/" % media.id,
            data={"comment_text": text},
            settings=settings,
        )

        try:
            data = await response.json()
            if data["status"] == "ok":
                comment = Comment(
                    data["id"],
                    media=media,
                    owner=self,
                    text=data["text"],
                    created_at=data["created_time"],
                )
                return comment
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def delete_comment(self, comment, settings=None):
        if not isinstance(comment, Comment):
            raise TypeError("'comment' must be Comment type")

        if comment.media.id is None:
            await self.update(comment.media, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/p/%s/" % comment.media.code,
            url="https://www.instagram.com/web/comments/%s/delete/%s/" % (
                comment.media.id,
                comment.id,
            ),
            settings=settings,
        )

        try:
            if (await response.json())["status"] == "ok":
                del comment
                return True
            return False
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def follow(self, account, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        if account.id is None:
            await self.update(account, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/%s" % account.login,
            url="https://www.instagram.com/web/friendships/%s/follow/" % account.id,
            settings=settings,
        )

        try:
            return (await response.json())["status"] == "ok"
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def unfollow(self, account, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        if account.id is None:
            await self.update(account, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/%s" % account.login,
            url="https://www.instagram.com/web/friendships/%s/unfollow/" % account.id,
            settings=settings,
        )

        try:
            return (await response.json())["status"] == "ok"
        except (ValueError, KeyError) as exception:
            raise UnexpectedResponse(exception, response.url)
