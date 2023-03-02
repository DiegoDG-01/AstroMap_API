from peewee import *


database = MySQLDatabase(
    'AstroMap',
    user='root',
    password='root',
    host='localhost',
    port=3306,
)

class Map(Model):
    user_uuid = CharField()
    map_uuid = CharField()
    url = CharField()
    status = CharField(default='in_progress')

    def __str__(self):
        return self.map_uuid

    class Meta:
        database = database
        table_name = 'maps'