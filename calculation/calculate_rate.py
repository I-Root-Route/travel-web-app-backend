import requests


def get_currency_rate(currency, start_date):
    if currency == "USD":
        return

    base_url = "https://api.exchangeratesapi.io/"
    url = base_url + start_date + "?base=USD" + f"&symbols={currency}"
    response = requests.get(url).json()

    if "error" in response.keys():
        return
    else:
        rate = response["rates"][currency]
        return rate


def get_average_cost(length_data, cost_data):
    averages = []
    for country, stay_length in length_data.items():
        spendings = cost_data[country]
        averages.append((country, int(spendings / stay_length)))

    return sorted(averages, key=lambda x: x[1], reverse=True)

