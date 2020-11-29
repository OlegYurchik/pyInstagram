import random
import time

import pytest

from pyinstagram.agents import (
    AsyncMobileAccountAgent,
    AsyncWebAccountAgent,
    AsyncWebAgent,
    MobileAccountAgent,
    WebAccountAgent,
    WebAgent,
)
from pyinstagram.entities import (
    Account,
    Location,
    Media,
    Tag,
)
from pyinstagram.tests import config


def setup_function():
    if config.anon["global_delay"] is None:
        return
    max_delay = config.anon["global_delay"].get("max", 120)
    min_delay = config.anon["global_delay"].get("min", 0)
    time.sleep(random.random() * (max_delay - min_delay) + min_delay)


def teardown_function():
    Account.clear_cache()
    Media.clear_cache()
    Location.clear_cache()
    Tag.clear_cache()


@pytest.fixture(scope="function")
def delay():
    if not config.anon["local_delay"] is None:
        min_delay = config.anon["local_delay"].get("min", 0)
        max_delay = config.anon["local_delay"].get("max", 10)
        return random.random() * (max_delay - min_delay) + min_delay
    return 0


@pytest.fixture(scope="module")
def web_agent():
    return WebAgent()


@pytest.fixture(scope="function")
async def async_web_agent():
    return AsyncWebAgent()


@pytest.fixture(scope="module")
def web_account_agent():
    agent = WebAccountAgent(config.creds["username"])
    agent.login(password=config.creds["password"])
    return agent


@pytest.fixture(scope="function")
async def async_web_account_agent():
    agent = AsyncWebAccountAgent(config.creds["username"])
    await agent.login(password=config.creds["password"])
    return agent


@pytest.fixture(scope="module")
def mobile_account_agent():
    agent = MobileAccountAgent(config.creds["username"])
    agent.login(password=config.creds["password"])
    return agent


@pytest.fixture(scope="function")
async def async_mobile_account_agent():
    agent = AsyncMobileAccountAgent(config.creds["username"])
    await agent.login(password=config.creds["password"])
    return agent
