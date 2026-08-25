from typing import TYPE_CHECKING

from src.database.database import Database
from src.shared.exceptions import ServiceNotInitializedError

if TYPE_CHECKING:
    from src.services.discord.bot import Bot
    from src.services.notifications import ReminderNotifier
    from src.services.telegram.client import TelegramClient


class ServiceRegistry:
    """
    Centralized registry for all application services.

    Services are initialized once and accessed via properties,
    ensuring they're never None when accessed.
    """

    __slots__ = ("_bot", "_client", "_notifier", "_database")

    _instance: ServiceRegistry | None = None

    def __new__(cls) -> ServiceRegistry:
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._bot = None
            cls._instance._client = None
            cls._instance._notifier = None
            cls._instance._database = None
        return cls._instance

    @property
    def bot(self) -> Bot:
        """Get the Discord bot instance. Raises ServiceNotInitializedError if not initialized."""
        if self._bot is None:
            raise ServiceNotInitializedError("Bot has not been initialized yet")
        return self._bot

    @bot.setter
    def bot(self, value: Bot) -> None:
        """Set the Discord bot instance."""
        if self._bot is not None:
            raise RuntimeError("Bot has already been initialized")
        self._bot = value

    @property
    def client(self) -> TelegramClient:
        """Get the Telegram client instance. Raises ServiceNotInitializedError if not initialized."""
        if self._client is None:
            raise ServiceNotInitializedError(
                "Telegram client has not been initialized yet"
            )
        return self._client

    @client.setter
    def client(self, value: TelegramClient) -> None:
        """Set the Telegram client instance."""
        if self._client is not None:
            raise RuntimeError("Telegram client has already been initialized")
        self._client = value

    @property
    def notifier(self) -> ReminderNotifier:
        """Get the reminder notifier or raise if it has not been initialized."""
        if self._notifier is None:
            raise ServiceNotInitializedError(
                "Reminder notifier has not been initialized yet"
            )
        return self._notifier

    @notifier.setter
    def notifier(self, value: ReminderNotifier) -> None:
        """Set the reminder notifier instance."""
        if self._notifier is not None:
            raise RuntimeError("Reminder notifier has already been initialized")
        self._notifier = value

    @property
    def database(self) -> Database:
        """Get the database instance. Creates it lazily if not initialized."""
        if self._database is None:
            self._database = Database()
        return self._database

    @database.setter
    def database(self, value: Database) -> None:
        """Set the database instance."""
        if self._database is not None:
            raise RuntimeError("Database has already been initialized")
        self._database = value


# Global registry instance - access services via this
services = ServiceRegistry()
