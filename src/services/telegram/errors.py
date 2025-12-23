import asyncio

from telethon import errors as telethon_errors

# Exception groups for cleaner error handling
AUTH_ERRORS = (
    telethon_errors.rpcerrorlist.AuthKeyUnregisteredError,
    telethon_errors.rpcerrorlist.AuthKeyInvalidError,
    telethon_errors.rpcerrorlist.AuthKeyDuplicatedError,
    telethon_errors.rpcerrorlist.AuthBytesInvalidError,
    telethon_errors.SecurityError,
)

# Password-related errors
PASSWORD_ERRORS = (
    telethon_errors.rpcerrorlist.PasswordHashInvalidError,
    telethon_errors.rpcerrorlist.PasswordEmptyError,
)

TIMEOUT_ERRORS = (
    asyncio.TimeoutError,
    asyncio.CancelledError,
)
