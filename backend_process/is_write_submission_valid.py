import settings


def is_valid(data):
    if data["visitedCountry"] not in settings.countries:
        return {"message": "Error! You should select a country"}
    if not data["visitedState"]:
        return {"message": "Error! You should select a state"}
    if not data["dates"]:
        return {"message": "Error! You should pick up period of the trip"}
    elif len(data["dates"]) == 1:
        return {"message": "Error! You should pick up 2 dates (start and end of the trip)"}
    if int(data["totalCost"]) == 0:
        return {"message": "Error! You must have spent money in your trip."}
    if not data["selectedCurrency"]:
        return {"message": "Error! You should select a currency. If multiple choices are available, either is fine"}
    elif data["selectedCurrency"] not in settings.valid_currencies:
        return {
            "message": "Error! You should select a valid currency. If multiple choices are available, either is fine"}

    return True
