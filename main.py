from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import AsyncGenerator, Any
import asyncio
import logging
import aiohttp

from src.config import settings

from webhook import router as webhook_router

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            '[%(asctime)s] %(levelname)s - %(filename)s'
            '[%(lineno)d]: %(message)s'
        )
    )


async def get_my_ip() -> str:
    url = 'https://httpbin.org/ip'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response = await response.json()
            return response.get('origin')


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    setup_logging()
    logger.info('Loggin setup')

    bot = settings.bot
    dp = settings.dp

    polling_task = asyncio.create_task(dp.start_polling(bot))
    app.state.polling_task = polling_task

    logger.info(f"IP {await get_my_ip()}")
    yield
    logger.info('Shutting down')
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
app.include_router(webhook_router)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True
    )
