"""Custom exception classes for the application."""


class BotError(Exception):
    """Base exception for all bot-related errors."""

    pass


class ServiceError(BotError):
    """Base exception for service-related errors."""

    pass


class ChannelError(BotError):
    """Base exception for channel-related errors."""

    pass


class ReminderError(BotError):
    """Base exception for reminder-related errors."""

    pass


class ServiceNotInitializedError(ServiceError):
    """Raised when accessing a service that hasn't been initialized."""

    pass


class ChannelNotFoundError(ChannelError):
    """Raised when a channel is not found."""

    pass


class ChannelAlreadyExistsError(ChannelError):
    """Raised when trying to add a channel that already exists."""

    pass


class ReminderGroupNotFoundError(ReminderError):
    """Raised when a reminder group is not found."""

    pass


class ReminderGroupAlreadyExistsError(ReminderError):
    """Raised when trying to create a reminder group that already exists."""

    pass


class ReminderTextExistsError(ReminderError):
    """Raised when trying to add a reminder text that already exists."""

    pass


class ReminderLimitReachedError(ReminderError):
    """Raised when trying to exceed reminder limits."""

    pass
