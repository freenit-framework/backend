from playhouse.flask_utils import FlaskDB


class MyDB(FlaskDB):
    def connect_db(self):
        if self.database.is_closed():
            super(MyDB, self).connect_db()


db = MyDB()
