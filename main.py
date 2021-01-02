import requests
import datetime
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from flask import Flask, request, jsonify
from flask_cors import CORS

from database.open_database import OpenDatabase
from calculation.calculate_rate import get_currency_rate
from backend_process.is_write_submission_valid import is_valid

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


@app.route('/api/country_states', methods=['GET', 'POST'])
def get_country_states():
    states = []
    country = request.get_json()["data"]["country"]
    url = "https://countriesnow.space/api/v0.1/countries/states"
    body = {"country": country}
    response = requests.post(url, data=body).json()["data"]["states"]

    for state in response:
        states.append(state["name"])

    return jsonify(states)


@app.route('/api/country_currency', methods=['GET', 'POST'])
def get_country_currency():
    country = request.get_json()["data"]["country"]
    url = "https://countriesnow.space/api/v0.1/countries/currency"
    body = {"country": country}
    response = requests.post(url, data=body).json()["data"]["currency"]

    return jsonify(response)


@app.route('/api/insert_visit_data', methods=['GET', 'POST'])
def insert_visit_data():
    req = request.get_json()["data"]
    if is_valid(req) is True:
        pass
    else:
        return jsonify(is_valid(req))

    username = req["userName"]
    visited_country = req["visitedCountry"]
    visited_state = req["visitedState"]
    total_cost = req["totalCost"]
    selected_currency = req["selectedCurrency"]

    dates = req["dates"]
    start_year = int(dates[0][:4])
    start_month = int(dates[0][5:7])
    start_day = int(dates[0][8:])
    start_date = datetime.date(year=start_year, month=start_month, day=start_day)

    end_year = int(dates[1][:4])
    end_month = int(dates[1][5:7])
    end_day = int(dates[1][8:])
    end_date = datetime.date(year=end_year, month=end_month, day=end_day)

    stay_length = abs(end_date - start_date).days

    rate = get_currency_rate(currency=selected_currency, start_date=dates[0])
    if rate is None:
        total_usd_cost = total_cost
    else:
        total_usd_cost = float(total_cost) / rate

    reformatted_data = [{
        "_index": username,
        "_source": {
            "username": username,
            "data": {
                "visited_country": visited_country,
                "visited_state": visited_state,
                "dates": dates,
                "stay_length": stay_length,
                "total_cost": int(total_cost),
                "selected_currency": selected_currency,
                "total_usd_cost": int(total_usd_cost)
            }
        }
    }]

    try:
        helpers.bulk(es, reformatted_data)
        res = {
            "message": "Insert Success"
        }
    except Exception as e:
        return jsonify({"message": e})

    return jsonify(res)


if __name__ == '__main__':
    es = Elasticsearch("http://localhost:9200")
    app.run()
