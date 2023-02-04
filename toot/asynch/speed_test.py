from datetime import datetime
import asyncio
import httpx
import aiohttp


async def httpx_get(client, url):
    start = datetime.now()
    response = await client.get(url)
    response.raise_for_status()
    text = response.json()
    print("httpx  ", url, datetime.now() - start)


async def aiohttp_get(session, url):
    start = datetime.now()
    async with session.get(url) as response:
        text = await response.json()
        print("aiohttp", url, datetime.now() - start)


urls = [
    "https://chaos.social/api/v1/instance",
    "https://chaos.social/api/v1/instance/peers",
    "https://chaos.social/api/v1/timelines/public",
]


async def test_httpx():
    start = datetime.now()
    async with httpx.AsyncClient() as client:
        for url in urls:
            for _ in range(3):
                await httpx_get(client, url)
    print("TOTAL", datetime.now() - start)


async def test_aiohttp():
    start = datetime.now()
    async with aiohttp.ClientSession() as session:
        for url in urls:
            for _ in range(3):
                await aiohttp_get(session, url)
    print("TOTAL", datetime.now() - start)


def run():
    asyncio.run(test_httpx())
    print("")
    asyncio.run(test_aiohttp())
