import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration from environment variables."""

    discord_token: str
    telegram_api_id: int
    telegram_api_hash: str
    environment: str

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables."""

        def get_required_env(var_name: str) -> str:
            value = os.getenv(var_name)
            if not value:
                raise ValueError(
                    f"{var_name} environment variable is not set. Please set it in your .env file."
                )
            return value

        def get_optional_env(var_name: str, default: str) -> str:
            return os.getenv(var_name, default)

        return cls(
            discord_token=get_required_env("DISCORD_TOKEN"),
            telegram_api_id=int(get_required_env("TELEGRAM_API_ID")),
            telegram_api_hash=get_required_env("TELEGRAM_API_HASH"),
            environment=get_optional_env("ENVIRONMENT", "production"),
        )

    @property
    def is_development(self) -> bool:
        return self.environment.lower() in ("development", "dev")


# Load config at module level
config = Config.from_env()
