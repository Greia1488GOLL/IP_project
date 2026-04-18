from aiogram import Dispatcher

from .alerts import router as alerts_router
from .common import router as common_router
from .tickers import router as tickers_router


def register_routers(dp: Dispatcher) -> None:
    dp.include_router(common_router)
    dp.include_router(tickers_router)
    dp.include_router(alerts_router)
