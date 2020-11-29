import datetime
import hashlib
import hmac
import json
import random
from typing import Optional
from urllib.parse import (
    urljoin,
    urlparse,
)
import uuid

import aiohttp

from .utils import sync
from ..entities import (
    Account,
    UpdatableEntity,
)


# https://github.com/ping/instagram_private_api
class AsyncMobileAccountAgent(Account):
    API_URL = "https://i.instagram.com/api/"
    API_VERSION = "v1"
    FB_HTTP_ENGINE = "Liger"

    APP_VERSION = "76.0.0.15.395"
    APPLICATION_ID = "567067343352427"
    IG_CAPABILITIES = "3brTvw=="
    SIG_KEY = "19ce5f445dbfd9d29c59dc2a78c616a7fc090a8e018b9267bc4240a30244c53b"
    SIG_KEY_VERSION = "4"
    VERSION_CODE = "138226743"

    ANDROID_RELEASE = "7.0"
    ANDROID_VERSION = 24
    PHONE_CHIPSET = "samsungexynos8890"
    PHONE_DEVICE = "SM-G930F"
    PHONE_DPI = "640dpi"
    PHONE_MANUFACTURER = "samsung"
    PHONE_MODEL = "herolte"
    PHONE_RESOLUTION = "1440x2560"

    USER_AGENT_FORMAT = (
        "Instagram {app_version} Android ({android_version:d}/{android_release}; "
        "{dpi}; {resolution}; {manufacturer}; {device}; {model}; {chipset}; en_US; {version_code})"
    )

    def __init__(
            self,
            username: str,
            api_url: Optional[str] = None,
            api_version: Optional[str] = None,
            fb_engine_http: Optional[str] = None,
            app_version: Optional[str] = None,
            application_id: Optional[str] = None,
            ig_capabilities: Optional[str] = None,
            sig_key: Optional[str] = None,
            sig_key_version: Optional[str] = None,
            version_code: Optional[str] = None,
            android_release: Optional[str] = None,
            android_version: Optional[int] = None,
            phone_chipset: Optional[str] = None,
            phone_device: Optional[str] = None,
            phone_dpi: Optional[str] = None,
            phone_manufacturer: Optional[str] = None,
            phone_model: Optional[str] = None,
            phone_resoulution: Optional[str] = None,
    ):
        self._session = aiohttp.ClientSession()

        self.username = username
        self._api_url = self.API_URL if api_url is None else api_url
        self._api_version = self.API_VERSION if api_version is None else api_version
        self._fb_engine_http = self.FB_HTTP_ENGINE if fb_engine_http is None else fb_engine_http
        self._app_version = self.APP_VERSION if app_version is None else app_version
        self._ig_capabilities = self.IG_CAPABILITIES if ig_capabilities is None else ig_capabilities
        self._application_id = self.APPLICATION_ID if application_id is None else application_id
        self._sig_key = self.SIG_KEY if sig_key is None else sig_key
        self._sig_key_version = self.SIG_KEY_VERSION if sig_key_version is None else sig_key_version
        self._version_code = self.VERSION_CODE if version_code is None else version_code
        self._android_release = self.ANDROID_RELEASE if android_release is None else android_release
        self._android_version = self.ANDROID_VERSION if android_version is None else android_version
        self._phone_chipset = self.PHONE_CHIPSET if phone_chipset is None else phone_chipset
        self._phone_device = self.PHONE_DEVICE if phone_device is None else phone_device
        self._phone_dpi = self.PHONE_DPI if phone_dpi is None else phone_dpi
        if phone_manufacturer is None:
            self._phone_manufacturer = self.PHONE_MANUFACTURER
        else:
            self._phone_manufacturer = phone_manufacturer
        self._phone_model = self.PHONE_MODEL if phone_model is None else phone_model
        if phone_resoulution is None:
            self._phone_resolution = self.PHONE_RESOLUTION
        else:
            self._phone_resolution = phone_resoulution

    def get_user_agent(self):
        return self.USER_AGENT_FORMAT.format(
            app_version=self._app_version,
            android_version=self._android_version,
            android_release=self._android_release,
            manufacturer=self._phone_manufacturer,
            device=self._phone_device,
            model=self._phone_model,
            dpi=self._phone_dpi,
            resolution=self._phone_resolution,
            chipset=self._phone_chipset,
            version_code=self._version_code,
        )

    def get_default_headers(self):
        return {
            "User-Agent": self.get_user_agent(),
            "Connection": "close",
            "Accept": "*/*",
            "Accept-Language": "en-US",
            "Accept-Encoding": "gzip, deflate",
            "X-IG-Capabilities": self._ig_capabilities,
            "X-IG-Connection-Type": "WIFI",
            "X-IG-Connection-Speed": "{0:d}kbps".format(random.randint(1000, 5000)),
            "X-IG-App-ID": self._application_id,
            "X-IG-Bandwidth-Speed-KBPS": "-1.000",
            "X-IG-Bandwidth-TotalBytes-B": "0",
            "X-IG-Bandwidth-TotalTime-MS": "0",
            "X-FB-HTTP-Engine": self._fb_engine_http,
        }

    def get_cookie_value(self, key: str):
        now = int(datetime.datetime.now().timestamp())
        url = urlparse(self._api_url)
        url = f"{url.scheme}://{url.netloc}"

        for name, cookie in self._session.cookie_jar.filter_cookies(url).items():
            # if cookie.expires and cookie.expires < now:
            #     continue
            if name.lower() == key.lower():
                return cookie.value

    def generate_signature(self, data: str):
        return hmac.new(
            self._sig_key.encode("ascii"),
            data.encode("ascii"),
            digestmod=hashlib.sha256,
        ).hexdigest()

    def generate_adid(self, seed: Optional[str] = None):
        # modified_seed = seed or self.authenticated_user_name or self.username
        modified_seed = seed or self.username
        if modified_seed:
            hash = hashlib.sha256()
            hash.update(modified_seed.encode("utf-8"))
            modified_seed = hash.hexdigest()
        return self.generate_uuid(modified_seed)

    @staticmethod
    def generate_uuid(seed: Optional[str] = None):
        if seed is not None:
            hash = hashlib.md5()
            hash.update(seed.encode("utf-8"))
            return uuid.UUID(hash.hexdigest())
        return uuid.uuid1()

    @classmethod
    def generate_deviceid(cls, seed: Optional[str] = None):
        return "android-{0!s}".format(cls.generate_uuid(seed).hex[:16])

    async def _request(self, path: str, data: Optional[dict] = None, params: Optional[dict] = None,
                       headers: Optional[dict] = None, *args, **kwargs):
        url = urljoin(self._api_url, self._api_version)
        if not url.endswith("/"):
            url += "/"
        url = urljoin(url, path)

        data = json.dumps(data, separators=(",", ":"))
        hash_sig_key = self.generate_signature(data)
        data = {
            "ig_sig_key_version": self._sig_key_version,
            "signed_body": hash_sig_key + "." + data,
        }

        tmp = {} if headers is None else headers
        headers = self.get_default_headers()
        headers.update(tmp)

        response = await self._session.post(url=url, data=data, params=params, headers=headers,
                                            *args, **kwargs)
        return await response.json()

    async def login(self, password: str):
        await self._request(
            "si/fetch_headers/",
            data="",
            params={
                "challenge_type": "signup",
                "guid": self.generate_uuid().hex,
            },
        )

        device_id = self.generate_deviceid()
        data = {
            "device_id": device_id,
            "guid": str(self.generate_uuid()),
            "adid": str(self.generate_adid()),
            "phone_id": str(self.generate_uuid(device_id)),
            "_csrftoken": self.get_cookie_value("csrftoken"),
            "username": self.username,
            "password": password,
            "login_attempt_count": "0",
        }
        response = await self._request("accounts/login/", data=data)

        return response

    async def update(self, entity: Optional[UpdatableEntity] = None):
        if entity is None:
            entity = self

        response = await self._request(f"users/{entity.username}/usernameinfo/")
        print(response)
        response = await self._request(f"users/{response['user']['pk']}/full_detail_info/")

        print(response["user_detail"]["user"].keys())

        return response
