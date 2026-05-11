# Este módulo implementa um armazenamento simples de eventos para o NEXUS

import sqlite3
from datetime import datetime

class EventStorage:
    def __init__(self, db_path='nexus_memory.db'):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self._setup_database()

    def _setup_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                event_type TEXT,
                event_data TEXT
            )
        ''')
        self.connection.commit()

    def store_event(self, event_type, event_data):
        timestamp = datetime.now().isoformat()
        self.cursor.execute(
            'INSERT INTO events (timestamp, event_type, event_data) VALUES (?, ?, ?)',
            (timestamp, event_type, event_data)
        )
        self.connection.commit()

    def get_events(self, event_type=None):
        query = 'SELECT * FROM events'
        params = ()
        if event_type:
            query += ' WHERE event_type = ?'
            params = (event_type,)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        self.connection.close()
