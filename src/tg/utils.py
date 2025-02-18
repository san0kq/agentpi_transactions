from __future__ import annotations

from typing import TYPE_CHECKING
from logging import getLogger

from aiogram.enums.parse_mode import ParseMode
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config import settings
from src.dto import TransactionTypeEnum


if TYPE_CHECKING:
    from src.dto import TransactionDTO

bot = settings.bot
chat_ids = settings.chat_ids.split(',')

logger = getLogger(__name__)


async def send_message_to_group(transaction: TransactionDTO) -> None:
    url = f"https://tonscan.org/tx/{transaction.tx_hash}"

    message = (
        f"Новая покупка <b>AGENTPI</b> от {settings.min_price} TON\n\n"
        f"🔒 Хэш: <code>{transaction.tx_hash}</code>\n"
        f"💰 Получено: {transaction.amount} AGENTPI\n"
        f"💵 Цена: {transaction.price} TON\n"
        f"👤 Покупатель: <code>{transaction.user_wallet}</code>\n"
        f"📎 Ссылка: {url}"
    )

    buttons = [
        [InlineKeyboardButton(
            text="🌍 Канал",
            url="https://t.me/AgentPi_Official"
        )],
        [InlineKeyboardButton(
            text="📎 Сделка",
            url=url
        )],
        [InlineKeyboardButton(
            text="👨‍💻 Creator",
            url="https://t.me/sut_adm1"
        )]
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    keyboard.adjust(1, 1)

    for chat_id in chat_ids:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard.as_markup()
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
