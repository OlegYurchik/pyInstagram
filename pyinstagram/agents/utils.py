import asyncio


def sync(coroutine):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        future = coroutine(*args, **kwargs)
        if not loop.is_running():
            return loop.run_until_complete(future)
        return future
    return wrapper
