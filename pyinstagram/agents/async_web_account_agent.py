import json
from typing import Optional

from .async_web_agent import AsyncWebAgent
from ..entities import (
    Account,
    HasMediaEntity,
)


class AsyncWebAccountAgent(Account, AsyncWebAgent):
    def __init__(self, username: str, cookies=None):
        if not isinstance(username, str):
            raise TypeError("'username' must be str type")

        Account.__init__(self, username)
        AsyncWebAgent.__init__(self, cookies=cookies)

    async def login(self, password: str, settings: Optional[dict] = None):
        if not isinstance(password, str):
            raise TypeError("'password' must be str type")
        if not isinstance(settings, dict) and settings is not None:
            raise TypeError("'settings' must be dict type or None")
        settings = {} if settings is None else settings.copy()

        self.logger.debug("Auth started")

        await self.update(settings=settings)

        if "headers" not in settings:
            settings["headers"] = {}
        settings["headers"].update({
            "X-IG-App-ID": "936619743392459",
            # "X_Instagram-AJAX": "ee72defd9231",
            "X-CSRFToken": self.csrf_token,
            "Referer": self.API_URL,
        })
        if "data" not in settings:
            settings["data"] = {}
        settings["data"].update({"username": self.username, "password": password})

        response = await self._post_request(
            path="/accounts/login/ajax/",
            **settings,
        )

        try:
            data = await response.json()
            if data.get("authenticated") is False:
                raise AuthException(self.username)
            elif data.get("message") == "checkpoint_required":
                data = await self.checkpoint_handle(
                    path=data.get("checkpoint_url"),
                    settings=settings,
                )
                raise CheckpointException(
                    username=self.username,
                    checkpoint_url=urljoin(self.API_URL, data.get("checkpoint_url")),
                    navigation=data["navigation"],
                    types=data["types"],
                )
        except (ValueError, KeyError) as exception:
            self.logger.exception("Auth was unsuccessfully")
            raise UnexpectedResponse(exception, response.url)
        self.logger.debug("Auth was successfully")

    async def checkpoint_handle(self, path, settings=None):
        self.logger.debug("Handle checkpoint page for '%s' started", self)

        response = await self.get_request(path=path, **settings)
        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                await response.text(),
            )
            data = json.loads(match.group(1))
            data = data["entry_data"]["Challenge"][0]

            navigation = {
                key: urljoin(self.API_URL, value) for key, value in data["navigation"].items()
            }

            data = data["extraData"]["content"]
            data = list(filter(lambda item: item["__typename"] == "GraphChallengePageForm", data))
            data = data[0]["fields"][0]["values"]
            types = []
            for d in data:
                types.append({"label": d["label"].lower().split(":")[0], "value": d["value"]})
            self.logger.debug("Handle checkpoint page for '%s' was successfull")
            return {"navigation": navigation, "types": types}
        except (AttributeError, KeyError, ValueError) as exception:
            self.logger.exception("Handle checkpoint page for '%s' was unsuccessfull", self)
            raise UnexpectedResponse(exception, response.url)

    async def checkpoint_send(self, checkpoint_path, forward_path, choice, settings=None):
        self.logger.debug("Send verify code for '%s' started", self)

        response = await self.action_request(
            path=forward_path,
            referer_path=checkpoint_path,
            data={"choice": choice},
            settings=settings,
        )

        try:
            navigation = (await response.json())["navigation"]
            self.logger.debug("Send verify code for '%s' was successfully", self)
            return {
                key: urljoin(self.API_URL, value) for key, value in navigation.items()
            }
        except (ValueError, KeyError) as exception:
            self.logger.exception("Send verify code by %s to '%s' was unsuccessfully", type, self)
            raise UnexpectedResponse(exception, response.url)

    async def checkpoint_replay(self, forward_path, replay_path, settings=None):
        self.logger.debug("Resend verify code for '%s' started", self)

        response = await self.action_request(
            path=replay_path,
            referer_path=forward_path,
            settings=settings,
        )
        try:
            navigation = (await response.json())["navigation"]
            self.logger.debug("Resend verify code for '%s' was successfull", self)
            return {
                key: urljoin(self.API_URL, value) for key, value in navigation.items()
            }
        except (AttributeError, KeyError, ValueError) as exception:
            self.logger.exception("Resend verify code for '%s' was unsuccessfull", self)
            raise UnexpectedResponse(exception, response.url)

    async def checkpoint(self, path, code, settings=None):
        self.logger.debug("Verify account '%s' started", self)

        response = await self.action_request(
            path=path,
            referer_path=path,
            data={"security_code": code},
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Verify account '%s' was successfull", self)
            return result
        except (AttributeError, KeyError, ValueError) as exception:
            self.logger.exception("Verify account '%s' was unsuccessfull", self)
            raise UnexpectedResponse(exception, response.url)

    async def update(self, entity=None, settings=None):
        if entity is None:
            entity = self
        return await AsyncWebAgent.update(self, entity=entity, settings=settings)

    async def get_media(self, entity=None, pointer=None, count=12, limit=12, delay=0,
                        settings=None):
        if entity is None:
            entity = self
        return await AsyncWebAgent.get_media(self, entity=entity, pointer=pointer, count=count,
                                             limit=limit, delay=delay, settings=settings)

    async def get_follows(self, account=None, pointer=None, count=20, limit=50, delay=0,
                          settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type or None")
        if not isinstance(pointer, str) and pointer is not None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(count, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.debug("Get '%s' follows started", account)

        if account is None:
            account = self
        if account.id is None:
            await self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        follows = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if pointer is not None:
                data["after"] = pointer

            response = await self.graphql_request(
                query_hash="58712303d941c6855d4e888c5f0cd22f",
                variables=variables_string.format(**data),
                referer_path=urljoin(account.web_base_path, getattr(account, account.primary_key)),
                settings=settings,
            )

            try:
                data = json.loads(response)["data"]["user"]["edge_follow"]
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
                    self.logger.debug("Get '%s' follows was successfully", account)
                    return follows, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get '%s' follows was unsuccessfully", account)
                raise UnexpectedResponse(exception, response.url)

    async def get_followers(self, account=None, pointer=None, count=20, limit=50, delay=0,
                            settings=None):
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

        self.logger.debug("Get '%s' followers started", account)

        if account is None:
            account = self
        if account.id is None:
            await self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        followers = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if pointer is not None:
                data["after"] = pointer

            response = await self.graphql_request(
                query_hash="37479f2b8209594dde7facb0d904896a",
                variables=variables_string.format(**data),
                referer_path=urljoin(account.web_base_path, getattr(account, account.primary_key)),
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
                    self.logger.debug("Get '%s' followers was successfully", account)
                    return followers, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get '%s' followers was unsuccessfully", account)
                raise UnexpectedResponse(exception, response.url)

    async def stories(self, settings=None):
        response = await self.graphql_request(
            query_hash="60b755363b5c230111347a7a4e242001",
            variables='{"only_stories":true}',
            referer_path=urljoin(self.web_base_path, getattr(self, self.primary_key)),
            settings=settings,
        )

        self.logger.debug("Get stories started")

        try:
            data = (await response.json())["data"]["user"]["feed_reels_tray"]
            data = data["edge_reels_tray_to_reel"]
            result = [Story(edge["node"]["id"]) for edge in data["edges"]]
            self.logger.debug("Get stories was successfully")
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Get stories was unsuccessfully")
            raise UnexpectedResponse(exception, response.url)

    async def feed(self, pointer=None, count=12, limit=50, delay=0, settings=None):
        if not isinstance(pointer, str) and pointer is not None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.debug("Get feed started")

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
                referer_path=urljoin(self.web_base_path, getattr(self, self.post_request)),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["user"]["edge_web_feed_timeline"]
                edges = data["edges"]
                page_info = data["page_info"]
                length = len(edges)

                for index in range(min(length, count)):
                    node = edges[index]["node"]
                    if "shortcode" not in node:
                        length -= 1
                        continue
                    m = Media(node["shortcode"])
                    m.set_web_data(node)
                    feed.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if length < count and page_info["has_next_page"]:
                    count -= length
                    await asyncio.sleep(delay)
                else:
                    self.logger.debug("Get feed was successfully")
                    return feed, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get feed was unsuccessfully")
                raise UnexpectedResponse(exception, response.url)

    async def like(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Like '%s' started", media)

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            path=f"/web/likes/{media.id}/like/",
            referer_path=urljoin(media.web_base_path, media.code),
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Like '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Like '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    async def unlike(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Unlike '%s' started", media)

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            path=f"/web/likes/{media.id}/unlike/",
            referer_path=urljoin(media.web_base_path, media.code),
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Like '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Like '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    async def save(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Save '%s' started", media)

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            path=f"/web/save/{media.id}/save/",
            referer_path=urljoin(media.web_base_path, media.code),
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Save '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Save '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    async def unsave(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Unsave '%s' started", media)

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer_path=urljoin(media.web_base_path, media.code),
            path=f"/web/save/{media.id}/unsave/",
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Unsave '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Unsave '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    async def add_comment(self, media, text, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(text, str):
            raise TypeError("'text' must be str type")

        self.logger.debug("Comment '%s' started", media)

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer_path=urljoin(media.web_base_path, media.code),
            path=f"/web/comments/{media.id}/add/",
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
            else:
                comment = None
            self.logger.debug("Comment '%s' was successfully", media)
            return comment
        except (ValueError, KeyError) as exception:
            self.logger.exception("Comment '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    async def delete_comment(self, comment, settings=None):
        if not isinstance(comment, Comment):
            raise TypeError("'comment' must be Comment type")

        self.logger.debug("Delete comment '%s' started", comment)

        if comment.media.id is None:
            await self.update(comment.media, settings=settings)

        response = await self.action_request(
            referer_path=urljoin(comment.media.web_base_path, comment.media.code),
            path=f"/web/comments/{comment.media.id}/delete/{comment.id}/",
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            if result:
                del comment
            self.logger.debug("Delete comment '%s' was successfully", comment)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Delete comment '%s' was unsuccessfully", comment)
            raise UnexpectedResponse(exception, response.url)

    async def follow(self, account, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        self.logger.debug("Follow to '%s' started", account)

        if account.id is None:
            await self.update(account, settings=settings)

        response = await self.action_request(
            path=f"/web/friendships/{account.id}/follow/",
            referer_path=urljoin(account.web_base_path, account.username),
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Follow to '%s' was successfully", account)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Follow to '%s' was unsuccessfully", account)
            raise UnexpectedResponse(exception, response.url)

    async def unfollow(self, account, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        self.logger.debug("Unfollow to '%s' started", account)

        if account.id is None:
            await self.update(account, settings=settings)

        response = await self.action_request(
            path=f"/web/friendships/{account.id}/unfollow/",
            referer_path=urljoin(account.web_base_path, account.username),
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Unfollow to '%s' was successfully", account)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Unfollow to '%s' was unsuccessfully", account)
            raise UnexpectedResponse(exception, response.url)
