import requests
from datetime import date, timedelta


def get_latest_rates():
    response = requests.get('https://api.exchangeratesapi.io/latest', params={'base': 'USD'})
    data = response.json()['rates']
    return data


def get_history_for_7_days(currency, base='USD'):
    today = date.today()
    delta = timedelta(days=9)

    params = {
        'start_at': str(today - delta),
        'end_at': str(today),
        'base': base,
        'symbols': currency,
    }
    response = requests.get('https://api.exchangeratesapi.io/history', params=params)
    return response.json()
