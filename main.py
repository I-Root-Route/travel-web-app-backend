import requests
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from flask import Flask, request, jsonify
from flask_cors import CORS

from database.open_database import OpenDatabase

app = Flask(__name__)
CORS(app)


@app.route('/api/login_process', methods=['GET', 'POST'])
def login_process():
    database = OpenDatabase().database
    user_info = request.get_json()["data"]
    user_name = user_info["username"]
    hashed_password = user_info["hashedPassword"]

    try:
        with database.cursor() as cursor:
            sql = "SELECT EXISTS(SELECT * FROM users WHERE name=%s)"
            cursor.execute(sql, user_name)
            result = cursor.fetchone()
            user_count = result[f"EXISTS(SELECT * FROM users WHERE name='{user_name}')"]
            if user_count == 0:
                database.close()
                return {"message": "Incorrect username or password"}
            else:
                validate_password_sql = "SELECT password from travel_app.users WHERE name=%s"
                cursor.execute(validate_password_sql, user_name)
                password_in_database = cursor.fetchone()["password"]
                if password_in_database == hashed_password:
                    database.close()
                    return {"message": "Success", "username": user_name}
                else:
                    database.close()
                    return {"message": "Incorrect username or password"}
    except Exception as e:
        database.close()
        return {"message": f"ERROR! {e}"}


@app.route('/api/register_process', methods=['GET', 'POST'])
def register_process():
    database = OpenDatabase().database
    user_info = request.get_json()["data"]
    user_name = user_info["username"]
    hashed_password = user_info["hashedPassword"]

    try:
        with database.cursor() as cursor:
            sql = "SELECT EXISTS(SELECT * FROM users WHERE name=%s)"
            cursor.execute(sql, user_name)
            result = cursor.fetchone()
            user_count = result[f"EXISTS(SELECT * FROM users WHERE name='{user_name}')"]
            if user_count == 0:
                try:
                    insert_sql = "INSERT INTO users (name, password) VALUES  (%s, %s)"
                    cursor.execute(insert_sql, (user_name, hashed_password))
                    database.commit()
                except Exception as e:
                    database.close()
                    return {"message": f"ERROR {e}"}
                finally:
                    database.close()
                    return {"message": "Success", "username": user_name}
            elif user_count != 0:
                database.close()
                return {"message": "Failure. You can't use this username. Username must be unique"}
    except Exception as e:
        database.close()
        return {"message": f"ERROR! {e}"}


@app.route('/api/country_data', methods=['GET', 'POST'])
def get_country_data():
    return jsonify("hflsaklflkal")


if __name__ == '__main__':
    es = Elasticsearch("http://localhost:9200")
    app.run()
