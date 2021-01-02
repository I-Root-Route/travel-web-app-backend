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

