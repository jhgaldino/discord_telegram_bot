ReminderStr = str
UserID = int
ReminderDict = dict[ReminderStr, list[UserID]]

_reminderDict: ReminderDict = {}

# Retorna a lista de textos que o usuario está marcado
def list_by_user(user_id: UserID) -> list[ReminderStr]:
    reminders: list[ReminderStr] = []
    for reminder in _reminderDict:
        if user_id in _reminderDict[reminder]:
            reminders.append(reminder)
    return reminders

# Adiciona um usuario a um texto
def add_user_to_reminder(user_id: UserID, reminder: ReminderStr) -> None:
    reminder = reminder.lower()
    if reminder not in _reminderDict:
        _reminderDict[reminder] = []
    _reminderDict[reminder].append(user_id)

# Remove um usuario de um texto
def remove_user_from_reminder(user_id: UserID, reminder: ReminderStr) -> None:
    reminder = reminder.lower()
    if reminder not in _reminderDict:
        return
    _reminderDict[reminder].remove(user_id)
    if not _reminderDict[reminder]:
        del _reminderDict[reminder]

# Retorna uma lista com todos os textos marcados
def list_all() -> list[ReminderStr]:
    return list[ReminderStr](_reminderDict.keys())

# Retorna uma lista de usuarios que estão marcados para um texto
def users_by_reminder(reminder: ReminderStr) -> list[UserID]:
    reminder = reminder.lower()
    if reminder not in _reminderDict:
        return []
    return _reminderDict[reminder]

# Cria um dicionário de usuarios e lembretes que estão presentes no texto, evitando duplicação
def find_by_user_in_text(text: str) -> dict[UserID, list[ReminderStr]]:
    text = text.lower()
    reminder_by_user: dict[UserID, list[ReminderStr]] = {}
    for reminder in list_all():
        if reminder in text:
            for user_id in users_by_reminder(reminder):
                if user_id not in reminder_by_user:
                    reminder_by_user[user_id] = []
                reminder_by_user[user_id].append(reminder)
    return reminder_by_user
