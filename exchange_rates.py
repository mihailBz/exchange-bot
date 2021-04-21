import os
import requests
from datetime import date, timedelta

ACCESS_KEY = os.getenv('ACCESSKEY')


class ExchangeRatesApiError(Exception):
    pass


def get_latest_rates():
    response = requests.get('https://api.exchangeratesapi.io/latest', params={'base': 'USD', 'access_key': ACCESS_KEY})
    data = response.json()
    if data.get('success') is not True:
        raise ExchangeRatesApiError
    return data.get('rates')


def get_history_for_7_days(currency, base='USD'):
    today = date.today()
    delta = timedelta(days=9)

    params = {
        'start_at': str(today - delta),
        'end_at': str(today),
        'base': base,
        'symbols': currency,
        'access_key': ACCESS_KEY
    }
    response = requests.get('https://api.exchangeratesapi.io/history', params=params)
    data = response.json()
    if data.get('success') is not True:
        raise ExchangeRatesApiError
    return data.get('rates')
