import requests
import datetime
import random
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from flask import Flask, request, jsonify
from flask_cors import CORS
from gevent.pywsgi import WSGIServer

# from database.open_database import OpenDatabase
from calculation.calculate_rate import get_currency_rate, get_average_cost
from backend_process.is_write_submission_valid import is_valid
from backend_process.sort_dict import sort_dict

import settings

app = Flask(__name__)
CORS(app)

es = Elasticsearch("https://3am93jkr5y:6obxztkcum@journey-list-8250541344.ap-southeast-2.bonsaisearch.net:443",
                   http_auth=('3am93jkr5y', '6obxztkcum'))


@app.route('/')
def hello():
    return "It's Working!"


@app.route('/api/login_process', methods=['GET', 'POST'])
def login_process():
    # database = OpenDatabase().database
    user_info = request.get_json()["data"]
    user_name = user_info["username"]
    user_name = user_name.replace(' ', '-')
    hashed_password = user_info["hashedPassword"]

    return {"message": "Success"}
    # try:
    #     with database.cursor() as cursor:
    #         sql = "SELECT EXISTS(SELECT * FROM users WHERE name=%s)"
    #         cursor.execute(sql, user_name)
    #         result = cursor.fetchone()
    #         user_count = result[f"EXISTS(SELECT * FROM users WHERE name='{user_name}')"]
    #         if user_count == 0:
    #             database.close()
    #             return {"message": "Incorrect username or password"}
    #         else:
    #             validate_password_sql = "SELECT password from travel_app.users WHERE name=%s"
    #             cursor.execute(validate_password_sql, user_name)
    #             password_in_database = cursor.fetchone()["password"]
    #             if password_in_database == hashed_password:
    #                 database.close()
    #                 return {"message": "Success", "username": user_name}
    #             else:
    #                 database.close()
    #                 return {"message": "Incorrect username or password"}
    # except Exception as e:
    #     database.close()
    #     return {"message": f"ERROR! {e}"}


@app.route('/api/register_process', methods=['GET', 'POST'])
def register_process():
    # database = OpenDatabase().database
    user_info = request.get_json()["data"]
    user_name = user_info["username"]
    user_name = user_name.replace(' ', '-')
    hashed_password = user_info["hashedPassword"]

    base_url = "https://3am93jkr5y:6obxztkcum@journey-list-8250541344.ap-southeast-2.bonsaisearch.net:443/"
    url = base_url + user_name
    requests.put(url)

    return {"message": "Success", "username": user_name}
#
# try:
#     with database.cursor() as cursor:
#         sql = "SELECT EXISTS(SELECT * FROM users WHERE name=%s)"
#         cursor.execute(sql, user_name)
#         result = cursor.fetchone()
#         user_count = result[f"EXISTS(SELECT * FROM users WHERE name='{user_name}')"]
#         if user_count == 0:
#             try:
#                 insert_sql = "INSERT INTO users (name, password) VALUES  (%s, %s)"
#                 cursor.execute(insert_sql, (user_name, hashed_password))
#                 database.commit()
#
#                 base_url = "https://3am93jkr5y:6obxztkcum@journey-list-8250541344.ap-southeast-2.bonsaisearch.net:443/"
#                 url = base_url + user_name
#                 requests.put(url)
#             except Exception as e:
#                 database.close()
#                 return {"message": f"ERROR {e}"}
#             finally:
#                 database.close()
#                 return {"message": "Success", "username": user_name}
#         elif user_count != 0:
#             database.close()
#             return {"message": "Failure. You can't use this username. Username must be unique"}
# except Exception as e:
#     database.close()
#     return {"message": f"ERROR! {e}"}


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
    username = username.replace(' ', '-')
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
        "data": {
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
    except helpers.BulkIndexError as e:
        print(e)
        return jsonify({"message": e})

    return jsonify(res)


@app.route('/api/search_personal_data', methods=['GET', 'POST'])
def get_personal_data():
    countries = []
    calendar_data = []
    length_pie_chart = {}
    spending_pie_chart = {}

    req = request.get_json()
    user_name = req["username"]
    user_name = user_name.replace(" ", "-")
    es_body = {
        "query": {"match_all": {}},
        "size": 10000
    }
    raw_data = es.search(body=es_body, index=user_name)
    hits = raw_data["hits"]["hits"]

    for hit in hits:
        data = hit["_source"]["data"]["data"]

        country = data["visited_country"]
        state = data["visited_state"]

        name = f"{country}: {state}"
        start = data["dates"][0]
        end = data["dates"][1]

        length = data["stay_length"]
        spendings = int(data["total_usd_cost"])

        calendar_data.append({
            "name": name,
            "start": start,
            "end": end,
            # "start": f"moment({start}).toDate()",
            # "end": f"moment({end}).toDate()",
            "color": settings.colors[random.randrange(len(settings.colors))],
            "timed": "true",
        })

        if country not in length_pie_chart.keys():
            countries.append(country)
            length_pie_chart[country] = length
            spending_pie_chart[country] = spendings
        else:
            length_pie_chart[country] += length
            spending_pie_chart[country] += spendings

    average_cost = get_average_cost(length_pie_chart, spending_pie_chart)

    return jsonify(
        {"calendar": calendar_data,
         "length": sort_dict(length_pie_chart),
         "spendings": sort_dict(spending_pie_chart),
         "countries": countries,
         "average": average_cost
         }
    )


if __name__ == '__main__':
    app.run()
