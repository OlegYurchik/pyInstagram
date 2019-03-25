import asyncio
from instagram.agents import WebAgent, WebAgentAccount, AsyncWebAgent, AsyncWebAgentAccount
import pytest
from random import random
from tests.settings import creds


@pytest.fixture(scope="module")
def settings():
    return {"headers": {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 " + \
                      "Firefox/61.0",
    }}


@pytest.fixture(scope="module")
def agent():
    return WebAgent()


@pytest.fixture(scope="module")
async def async_agent():
    return AsyncWebAgent()


@pytest.fixture(scope="module")
def agent_account(settings):
    agent =  WebAgentAccount(creds["username"])
    agent.auth(password=creds["password"], settings=settings)
    return agent


@pytest.fixture(scope="module")
async def async_agent_account(settings):
    agent = AsyncWebAgentAccount(creds["username"])
    await agent.auth(password=creds["password"], settings=settings)
    return agent


@pytest.fixture(scope="module")
def event_loop():
    return asyncio.new_event_loop()
