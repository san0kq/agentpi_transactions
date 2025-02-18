from logging import getLogger
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response
import httpx

from src.tg.utils import (
    send_message_to_group,
    validate_transaction,
)
from src.dto import TransactionDTO

logger = getLogger(__name__)

router = APIRouter()


async def build_url(tx_hash: str) -> str:
    return (
        f"https://tonapi.io/v2/events/{tx_hash}"
    )


async def process_response(response: dict) -> TransactionDTO:
    event_id = response.get("event_id")
    actions = response.get("actions")

    amount_in = None
    amount_out = None
    ton_in = None

    for action in actions:
        action_type = action.get("type")
        status = action.get("status")

        if status != "ok":
            continue

        if action_type == "JettonSwap":
            swap = action.get("JettonSwap")

            amount_in = int(swap.get("amount_in")) if swap.get("amount_in") else 0
            amount_out = int(swap.get("amount_out")) if swap.get("amount_out") else 0
            jetton_master_in = swap.get("jetton_master_in", {})
            jetton_master_out = swap.get("jetton_master_out", {})
            decimals_in = jetton_master_in.get("decimals", 0)
            decimals_out = jetton_master_out.get("decimals", 0)
            user_wallet = swap.get("user_wallet").get("address")
            ton_in = swap.get("ton_in", 0)

            break

        if action_type == "JettonTransfer":
            transfer = action.get("JettonTransfer")

            if transfer.get("senders_wallet") == transfer.get("recipients_wallet"):
                amount_out = int(transfer.get("amount"))
                decimals_in = transfer.get("jetton").get("decimals", 0)
            else:
                ton_in = int(transfer.get("amount"))
                decimals_out = transfer.get("jetton").get("decimals", 0)
                user_wallet = transfer.get("senders_wallet")

    created_at = datetime.fromtimestamp(
        response.get("timestamp"),
        timezone.utc
    )
    transaction = {
        "tx_hash": event_id,
        "user_wallet": user_wallet,
        "created_at": created_at,
    }

    if amount_in and amount_out:
        transaction["type"] = "sell"
        transaction["amount"] = amount_in / (10 ** decimals_in)
        transaction["price"] = amount_out / (10 ** decimals_out)

    elif amount_out and ton_in:
        transaction["type"] = "buy"
        transaction["amount"] = amount_out / (10 ** decimals_out)
        transaction["price"] = ton_in / (10 ** decimals_out)

    else:
        return None

    return TransactionDTO(**transaction)


@router.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"Get webhook: {data}")

        tx_hash = data.get("tx_hash")

        if tx_hash:

            url = await build_url(tx_hash)

            async with httpx.AsyncClient() as client:
                response = await client.get(url)

            if response.status_code == 200:
                response = response.json()
                logger.info("Request status success [200]")

                transaction = await process_response(response=response)

                is_valid = validate_transaction(transaction=transaction)

                if is_valid:
                    await send_message_to_group(
                        transaction=transaction
                    )

            else:
                logger.error(
                    f"Request error: "
                    f"{response.status_code} - {response.text}"
                )
        else:
            logger.warning("tx_hash not found")

        return Response(status_code=200)

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}
