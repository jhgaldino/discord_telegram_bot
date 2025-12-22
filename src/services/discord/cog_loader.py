import asyncio
import logging
from pathlib import Path

from watchfiles import Change, awatch

from discord.ext import commands


class CogLoader:
    """Loads extensions and optionally watches for changes to reload them automatically."""

    _CHECK_INTERVAL: float = 1.0

    def __init__(
        self,
        bot: commands.Bot,
        hot_reload: bool = True,
    ) -> None:
        self.bot: commands.Bot = bot
        self.hot_reload: bool = hot_reload
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._task: asyncio.Task[None] | None = None
        self._running: bool = False
        self.ext_dir = Path.cwd() / Path("src/cogs")

    def _get_path_as_extension_name(self, file: Path) -> str:
        try:
            relative_path = file.relative_to(Path.cwd())
        except ValueError:
            relative_path = file
        return ".".join(relative_path.with_suffix("").parts)

    async def _load_extension(self, extension_name: str) -> None:
        try:
            await self.bot.load_extension(extension_name)
        except commands.ExtensionNotFound:
            self.logger.warning(f"Extension {extension_name} not found")
        except commands.ExtensionAlreadyLoaded:
            self.logger.debug(f"Extension {extension_name} already loaded")
        except commands.ExtensionFailed as e:
            self.logger.error(
                f"Extension {extension_name} failed to load: {e}", exc_info=e
            )

    async def load_all_extensions(self) -> None:
        dir_name = self._get_path_as_extension_name(self.ext_dir)
        if not self.ext_dir.is_dir():
            self.logger.warning(f"Extension directory {dir_name} does not exist")
            return

        self.logger.info("Loading extensions...")
        for file in self.ext_dir.rglob("*.py"):
            if file.stem.startswith("_"):
                continue
            extension_name = self._get_path_as_extension_name(file)
            await self._load_extension(extension_name)
            self.logger.info(f"Loaded {extension_name}")

    async def _watch(self) -> None:
        dir_name = self._get_path_as_extension_name(self.ext_dir)
        if not self.ext_dir.is_dir():
            self.logger.error(f"Extension directory {dir_name} does not exist")
            return
        self.logger.info(f"Watching for changes in {dir_name}/...")

        try:
            async for changes in awatch(self.ext_dir):
                for change in sorted(changes, reverse=True):
                    change_type = change[0]
                    change_path = change[1]

                    if not change_path.endswith(".py"):
                        continue

                    file_path = Path(change_path)
                    if file_path.stem.startswith("_"):
                        continue

                    extension_name = self._get_path_as_extension_name(file_path)
                    is_loaded = extension_name in self.bot.extensions

                    if change_type == Change.deleted:
                        if is_loaded:
                            try:
                                await self.bot.unload_extension(extension_name)
                                self.logger.info(f"Unloaded {extension_name}")
                            except Exception as e:
                                self.logger.error(
                                    f"Failed to unload {extension_name}: {e}",
                                    exc_info=e,
                                )
                    elif change_type == Change.added:
                        if not is_loaded:
                            await self._load_extension(extension_name)
                            self.logger.info(f"Loaded {extension_name}")
                    elif change_type == Change.modified:
                        if is_loaded:
                            try:
                                await self.bot.reload_extension(extension_name)
                                self.logger.info(f"Reloaded {extension_name}")
                            except Exception as e:
                                self.logger.error(
                                    f"Failed to reload {extension_name}: {e}",
                                    exc_info=e,
                                )
                        else:
                            await self._load_extension(extension_name)
                            self.logger.info(f"Loaded {extension_name}")
        except FileNotFoundError:
            self.logger.warning(f"Extension directory {dir_name} was deleted")
        except asyncio.CancelledError:
            pass

    async def start(self) -> None:
        """Start loading extensions and optionally watching for changes."""
        if self._running:
            self.logger.warning("Cog loader is already running")
            return

        await self.load_all_extensions()

        if self.hot_reload:
            self._running = True
            self._task = self.bot.loop.create_task(self._watch())
            self.logger.info("Cog loader started with hot-reload enabled")
        else:
            self.logger.info("Cog loader started (hot-reload disabled)")

    async def stop(self) -> None:
        """Stop watching for changes."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("Cog loader stopped")
