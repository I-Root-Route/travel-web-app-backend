import pymysql
import pyodbc


class OpenDatabase(object):
    def __init__(self):
        server = 'journey-list-sql.database.windows.net'
        database_id = 'journey-list-db'
        username = 'journey-list-admin'
        password = '!wnnbmscprdcr190821'
        driver = '{ODBC Driver 13 for SQL Server}'
        self.database = pyodbc.connect(
            'DRIVER=' + driver + ';PORT=1433;SERVER=' + server +
            ';PORT=1443;DATABASE=' + database_id + ';UID=' + username + ';PWD=' + password)

        # self.database = pymysql.connect(
        #     user='root',
        #     db='travel_app',
        #     cursorclass=pymysql.cursors.DictCursor
        # )
