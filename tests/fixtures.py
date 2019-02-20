import asyncio
from instaparser.agents import Agent, AgentAccount, AsyncAgent, AsyncAgentAccount
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
def agent(settings):
    return Agent(settings=settings)


@pytest.fixture(scope="module")
async def async_agent(settings):
    return await AsyncAgent.create(settings=settings)


@pytest.fixture(scope="module")
def agent_account(settings):
    return AgentAccount(creds["login"], creds["password"], settings=settings)


@pytest.fixture(scope="module")
async def async_agent_account(settings):
    return await AsyncAgentAccount.create(creds["login"], creds["password"], settings=settings)


@pytest.fixture(scope="module")
def event_loop():
    return asyncio.new_event_loop()
