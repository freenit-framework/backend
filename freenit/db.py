from playhouse.flask_utils import FlaskDB


class SQL(FlaskDB):
    def connect_db(self):
        if self.database.is_closed():
            super(SQL, self).connect_db()


db = SQL()
