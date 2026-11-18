import telethon.errors

# Exception groups for cleaner error handling
AUTH_ERRORS = (
    telethon.errors.rpcerrorlist.AuthKeyUnregisteredError,
    telethon.errors.rpcerrorlist.AuthKeyInvalidError,
    telethon.errors.rpcerrorlist.AuthKeyDuplicatedError,
    telethon.errors.rpcerrorlist.AuthBytesInvalidError,
    telethon.errors.SecurityError,
)

# Password-related errors
PASSWORD_ERRORS = (
    telethon.errors.rpcerrorlist.PasswordHashInvalidError,
    telethon.errors.rpcerrorlist.PasswordEmptyError,
)
