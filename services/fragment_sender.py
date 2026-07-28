import base64
import re
import json
import logging
import httpx
from aiogram import Bot
from config import Config
from pytonlib import TonlibClient

def fix_base64_padding(b64_string: str) -> str:
    missing_padding = len(b64_string) % 4
    if missing_padding:
        b64_string += '=' * (4 - missing_padding)
    return b64_string

class FragmentSender:
    def __init__(self, config: Config, bot: Bot):
        self.config = config
        self.bot = bot
        self.url = "https://fragment.com/api"
        self.base_headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://fragment.com",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "X-Requested-With": "XMLHttpRequest",
        }
        logging.info(f"FRAGMENT_HASH: {self.config.fragment.hash}")
logging.info(f"STEL_SSID: {self.config.ton.stel_ssid}")
logging.info(f"STEL_TON_TOKEN: {self.config.ton.stel_ton_token}")

        self.ton_client = None
        logging.info("FragmentSender initialized (pytonlib)")

    async def _init_ton_client(self):
        if self.ton_client is None:
            self.ton_client = TonlibClient(
                ls_index=0,
                config='https://ton.org/global.config.json',
                keystore='./keystore'
            )
            await self.ton_client.init()
        return self.ton_client

    async def _safe_parse_response(self, response: httpx.Response):
        content = response.content
        try:
            return response.json()
        except (UnicodeDecodeError, json.JSONDecodeError):
            for encoding in ['utf-8', 'windows-1251', 'latin-1', 'cp1252']:
                try:
                    text = content.decode(encoding)
                    return json.loads(text)
                except:
                    continue
            logging.error(f"Failed to parse response. Raw: {content[:200]}")
            return None

    async def _send_ton_transaction(self, recipient_addr, amount, payload, comment_template):
        logging.info(f"[TON] Sending to {recipient_addr} amount={amount}")
        try:
            client = await self._init_ton_client()
            mnemonic = self.config.ton.wallet_seed.split()
            wallet = await client.import_wallet(mnemonic, wallet_id=698983191)
            address = wallet['address']
            logging.info(f"[TON] Wallet address: {address}")

            balance = await client.get_balance(address)
            amount_decimal = float(amount) / 1_000_000_000
            if balance < amount_decimal:
                logging.critical(f"Insufficient funds. Required: {amount_decimal:.4f} TON")
                return False

            decoded_bytes = base64.b64decode(fix_base64_padding(payload))
            decoded_text = ''.join(chr(b) if 32 <= b < 127 else ' ' for b in decoded_bytes)
            clean_text = re.sub(r'\s+', ' ', decoded_text).strip()
            match = re.search(comment_template, clean_text)
            final_text = match.group(0) if match else clean_text

            result = await client.transfer(
                destination=recipient_addr,
                amount=amount_decimal,
                comment=final_text,
                wallet=wallet
            )
            logging.info(f"Transaction sent: {result}")
            return True
        except Exception as e:
            logging.error(f"TON transaction failed: {e}")
            await self._notify_admins(f"❌ Ошибка TON: {str(e)}")
            return False

    async def send_stars(self, username: str, quantity: int) -> bool:
        logging.info(f"Starting stars purchase: {quantity} stars for @{username}")
        try:
            async with httpx.AsyncClient(cookies=self.config.fragment.cookies, headers=self.base_headers, timeout=30.0) as client:
                # Шаг 1
                headers_step1 = self.base_headers.copy()
                headers_step1["Referer"] = "https://fragment.com/stars"
                data_step1 = {"query": username, "method": "searchStarsRecipient"}
                response_step1 = await client.post(self.url, data=data_step1, headers=headers_step1)
                response_step1.raise_for_status()
                json_step1 = await self._safe_parse_response(response_step1)
                logging.info(f"Step1: {json_step1}")
                if json_step1 is None or not json_step1.get("ok", True):
                    logging.error("Step1 failed")
                    return False
                recipient = json_step1.get("found", {}).get("recipient")
                if not recipient:
                    logging.error("Step1: no recipient")
                    return False

                # Шаг 2
                headers_step2 = self.base_headers.copy()
                headers_step2["Referer"] = f"https://fragment.com/stars/buy?query={username}"
                data_step2 = {"recipient": recipient, "quantity": quantity, "method": "initBuyStarsRequest"}
                response_step2 = await client.post(self.url, data=data_step2, headers=headers_step2)
                response_step2.raise_for_status()
                json_step2 = await self._safe_parse_response(response_step2)
                logging.info(f"Step2: {json_step2}")
                if json_step2 is None or not json_step2.get("ok", True):
                    logging.error("Step2 failed")
                    return False
                req_id = json_step2.get("req_id")
                if not req_id:
                    logging.error("Step2: no req_id")
                    return False

                # Шаг 3
                headers_step3 = self.base_headers.copy()
                headers_step3["Referer"] = f"https://fragment.com/stars/buy?recipient={recipient}&quantity={quantity}"
                data_step3 = {
                    "address": self.config.fragment.address,
                    "chain": "-239",
                    "walletStateInit": self.config.fragment.wallets,
                    "publicKey": self.config.fragment.public_key,
                    "features": ["SendTransaction", {"name": "SendTransaction", "maxMessages": 255}],
                    "maxProtocolVersion": 2,
                    "platform": "iphone",
                    "appName": "Tonkeeper",
                    "appVersion": "5.0.14",
                    "transaction": "1",
                    "id": req_id,
                    "show_sender": "0",
                    "method": "getBuyStarsLink"
                }
                response_step3 = await client.post(self.url, data=data_step3, headers=headers_step3)
                response_step3.raise_for_status()
                json_step3 = await self._safe_parse_response(response_step3)
                logging.info(f"Step3: {json_step3}")
                if json_step3 is None or not (json_step3.get("ok") and "transaction" in json_step3):
                    logging.error("Step3: no transaction")
                    return False

                tx = json_step3["transaction"]["messages"][0]
                addr, amount, payload = tx["address"], tx["amount"], tx["payload"]
                comment_template = rf"{quantity} Telegram Stars.*"
                return await self._send_ton_transaction(addr, amount, payload, comment_template)
        except Exception as e:
            logging.error(f"Stars purchase failed: {e}")
            await self._notify_admins(f"❌ Ошибка: {str(e)}")
            return False

    async def _notify_admins(self, message: str):
        for admin_id in self.config.bot.admin_ids:
            try:
                await self.bot.send_message(admin_id, f"🔗 <b>Fragment уведомление</b>\n\n{message}")
            except Exception as e:
                logging.error(f"Failed to notify admin {admin_id}: {e}")

    async def send_premium(self, username: str, months: int) -> bool:
        logging.info(f"Premium purchase not implemented yet for @{username}")
        return False
