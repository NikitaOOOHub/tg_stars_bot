import logging
from aiogram import Bot
from config import Config
from fragment_api import FragmentAPI

class FragmentSender:
    def init(self, config: Config, bot: Bot):
        self.config = config
        self.bot = bot
        self.api = FragmentAPI(
            seed=self.config.ton.wallet_seed,           # мнемоника (24 слова)
            api_key=self.config.ton.api_ton,            # API ключ TON
            cookies=self.config.fragment.cookies,       # куки с Fragment
            hash=self.config.fragment.hash              # хеш с Fragment
        )
        logging.info("FragmentSender initialized with fragment-api-py")

    async def send_stars(self, username: str, quantity: int) -> bool:
        logging.info(f"Sending {quantity} stars to @{username}")
        try:
            result = await self.api.buy_stars(username, quantity)
            logging.info(f"Stars purchase completed: {result}")
            await self._notify_admins(f"✅ Куплено {quantity} звёзд для @{username}")
            return True
        except Exception as e:
            logging.error(f"Stars purchase failed: {e}")
            await self._notify_admins(f"❌ Ошибка: {str(e)}")
            return False

    async def send_premium(self, username: str, months: int) -> bool:
        logging.info(f"Sending {months} months Premium to @{username}")
        try:
            result = await self.api.buy_premium(username, months)
            logging.info(f"Premium purchase completed: {result}")
            await self._notify_admins(f"✅ Куплен Premium ({months} мес.) для @{username}")
            return True
        except Exception as e:
            logging.error(f"Premium purchase failed: {e}")
            await self._notify_admins(f"❌ Ошибка: {str(e)}")
            return False

    async def _notify_admins(self, message: str):
        for admin_id in self.config.bot.admin_ids:
            try:
                await self.bot.send_message(admin_id, f"🔔 {message}")
            except Exception as e:
                logging.error(f"Failed to notify admin {admin_id}: {e}")
