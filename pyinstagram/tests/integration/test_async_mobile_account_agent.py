import pytest

from pyinstagram.agents import AsyncMobileAccountAgent
from pyinstagram.entities import Account

from .. import config


@pytest.mark.asyncio
async def test_login():
    agent = AsyncMobileAccountAgent(config.creds["username"])
    response = await agent.login(password=config.creds["password"])


@pytest.mark.parametrize("username", config.accounts)
@pytest.mark.asyncio
async def test_update_account(async_mobile_account_agent, username):
    account = Account(username)
    response = await async_mobile_account_agent.update(account)
