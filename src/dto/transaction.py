from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TransactionTypeEnum(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class TransactionDTO:
    tx_hash: str
    user_wallet: str
    created_at: datetime
    type: TransactionTypeEnum
    amount: float
    price: float
