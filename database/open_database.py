import pymysql


class OpenDatabase(object):
    def __init__(self):
        self.database = pymysql.connect(
            user='root',
            db='travel_app',
            cursorclass=pymysql.cursors.DictCursor
        )
