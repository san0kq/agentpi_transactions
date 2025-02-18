from __future__ import annotations

from typing import TYPE_CHECKING
from logging import getLogger

from aiogram.enums.parse_mode import ParseMode

from src.config import settings
from src.dto import TransactionTypeEnum


if TYPE_CHECKING:
    from src.dto import TransactionDTO

bot = settings.bot
chat_id = settings.chat_id

logger = getLogger(__name__)


async def send_message_to_group(transaction: TransactionDTO) -> None:
    url = f"https://tonscan.org/tx/{transaction.tx_hash}"

    message = (
        f"Новая покупка <b>AGENTPI</b> от {settings.min_price} TON\n\n"
        f"🔗 Хэш: {transaction.tx_hash}\n"
        f"💰 Получено: {transaction.amount} AGENTPI\n"
        f"💵 Цена: {transaction.price} TON"
        f"👤 Покупатель: {transaction.user_wallet}\n"
        f"🌎 Ссылка: {url}"
    )

    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML
    )


def validate_transaction(transaction: TransactionDTO | None) -> bool:
    if not transaction:
        logger.info("No transaction.")
        return False

    if transaction.type != TransactionTypeEnum.BUY.value:
        logger.info(transaction.type)
        logger.info("Transaction TYPE is not BUY!")
        return False

    if transaction.price < settings.min_price:
        return False

    return True
