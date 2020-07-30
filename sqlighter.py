import sqlite3


class SQLighter:

    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def get_users(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM 'users'").fetchall()

    def user_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM 'users' WHERE user_id = ?", (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id):
        with self.connection:
            return self.cursor.execute("INSERT INTO 'users' ('user_id') VALUES (?)", (user_id,))

    def has_user_validator(self, user_id, validator_address):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM 'user_validators' WHERE user_id = ? AND validator = ?", (user_id, validator_address)).fetchall()
            return bool(len(result))

    def add_validator_to_user(self, user_id, validator_address):
        if not self.user_exists(user_id):
            self.add_user(user_id)
        if self.has_user_validator(user_id, validator_address):
            return False
        with self.connection:
            return self.cursor.execute("INSERT INTO 'user_validators' ('user_id', 'validator') VALUES (?, ?)", (user_id, validator_address))

    def get_validators_by_user(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT validator FROM 'user_validators' WHERE user_id = ?", (user_id,)).fetchall()

    def get_user_validators(self):
        with self.connection:
            return self.cursor.execute("SELECT user_id, validator FROM 'user_validators' ORDER BY validator").fetchall()

    def close(self):
        self.connection.close()
