import sqlite3

connection = sqlite3.connect('reminders.db')
cursor = connection.cursor()

create_table_query = '''
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        reminder TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, reminder)
    )
'''

cursor.execute(create_table_query)
connection.commit()

def add_user_to_reminder(user_id: int, reminder: str) -> None:
    try:        
        insert_query = '''
            INSERT INTO reminders (user_id, reminder) VALUES (?, LOWER(?))
        '''

        cursor.execute(insert_query, (user_id, reminder))
        connection.commit()
    except sqlite3.IntegrityError:
        # Ignora o erro de duplicação de lembrete
        pass

def list_by_user(user_id: int) -> list[str]:
    select_query = '''
        SELECT reminder FROM reminders
        WHERE user_id = ?
        ORDER BY created_at DESC
    '''

    cursor.execute(select_query, (user_id,))
    results: list[tuple[str]] = cursor.fetchall()
    return [reminder for (reminder,) in results]

def remove_user_from_reminder(user_id: int, reminder: str) -> None:
    delete_query = '''
        DELETE FROM reminders
        WHERE user_id = ? AND reminder = LOWER(?)
    '''

    cursor.execute(delete_query, (user_id, reminder))
    connection.commit()

def list_all() -> list[str]:
    select_query = '''
        SELECT reminder FROM reminders
        GROUP BY reminder
    '''

    cursor.execute(select_query)
    results: list[tuple[str]] = cursor.fetchall()
    return [reminder for (reminder,) in results]

def find_by_user_in_text(text: str) -> dict[int, list[str]]:
    select_query = '''
        SELECT user_id, reminder FROM reminders
        WHERE INSTR(LOWER(?), LOWER(reminder)) > 0
    '''

    cursor.execute(select_query, (text,))
    results: list[tuple[int, str]] = cursor.fetchall()
    
    reminder_by_user: dict[int, list[str]] = {}
    for user_id, reminder in results:
        if user_id not in reminder_by_user:
            reminder_by_user[user_id] = []
        reminder_by_user[user_id].append(reminder)
    
    return reminder_by_user
