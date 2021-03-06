import requests
import datetime
import random
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

from calculation.calculate_rate import get_currency_rate, get_average_cost
from backend_process.is_write_submission_valid import is_valid
from backend_process.sort_dict import sort_dict

import settings

app = Flask(__name__)
CORS(app)

es = Elasticsearch(settings.elastic_url, http_auth=(settings.elastic_user, settings.elastic_pass))


def user_hits(user_name):
    is_user_exist_query = {
        "query": {
            "match": {"user_name": user_name}
        }
    }

    user = es.search(index=settings.users_index, body=is_user_exist_query)["hits"]["hits"]

    return user


@app.route('/')
def hello():
    return "It's Working!"


@app.route('/api/login_process', methods=['GET', 'POST'])
def login_process():
    user_info = request.get_json()["data"]
    user_name = user_info["username"]
    user_name = user_name.replace(' ', '-')
    hashed_password = user_info["hashedPassword"]

    user = user_hits(user_name)

    if not user:
        return {"message": "ERROR Incorrect username or password"}
    else:
        pass_in_db = user[0]["_source"]["hashed_password"]
        if hashed_password != pass_in_db:
            return {"message": "ERROR Incorrect username or password"}
        else:
            return {"message": "Success"}


@app.route('/api/register_process', methods=['GET', 'POST'])
def register_process():
    user_info = request.get_json()["data"]
    user_name = user_info["username"]
    user_name = user_name.replace(' ', '-')
    hashed_password = user_info["hashedPassword"]

    user = user_hits(user_name)

    if not user:
        try:
            body = {
                "user_name": user_name,
                "hashed_password": hashed_password,
            }
            es.index(index=settings.users_index, body=body)
            requests.put(settings.elastic_url + "/" + user_name)
        except Exception as e:
            logging.error(e)
            return {"message": f"ERROR {e}"}
    else:
        return {"message": f"ERROR This user name already exists in our database. Try to use different user name"}

    return {"message": "Success", "username": user_name}


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
