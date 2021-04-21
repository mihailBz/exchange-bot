import telebot
import os
from datetime import datetime
import exchange_rates as ratesapi
from exchange_rates import ExchangeRatesApiError
import bot_db as db
from matplotlib import pyplot as plt
from io import BytesIO

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)


class WrongCommand(Exception):
    pass


def time_since_last_update(timestamp):
    now = datetime.now()
    last_update = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    delta = now - last_update
    seconds = delta.total_seconds()
    minutes = seconds // 60
    return minutes


def get_rates():
    last_updated = db.get_timestamp()
    if last_updated is not None and time_since_last_update(last_updated) < 360:
        rates = db.get_rates()
    else:
        rates = ratesapi.get_latest_rates()
        db.save_rates(rates=rates)
        rates = rates.items()
    return rates


@bot.message_handler(commands=['list'])
def list_message(message):
    text = ''

    try:
        rates = get_rates()
        for currency, rate in rates:
            text += f'{currency}: {rate}\n'
    except ExchangeRatesApiError:
        text = 'Exchange rates server is not available. Sorry'
    finally:
        bot.send_message(chat_id=message.chat.id, text=text)


def parse_text(text):
    try:
        words_list = text.split()[1:]
        amount = float(words_list[0])
        base_currency = words_list[1]
        convert_to = words_list[-1]
    except ValueError:
        raise WrongCommand
    except IndexError:
        raise WrongCommand

    return amount, base_currency, convert_to


def convert(value, base_currency, convert_to):
    try:
        rates = dict(get_rates())
        base_currency_rate = rates.get(base_currency) if base_currency != 'USD' else 1
        convert_to_rate = rates.get(convert_to)
        result = round((value * convert_to_rate) / base_currency_rate, 2)
    except TypeError:
        raise WrongCommand

    return result


@bot.message_handler(commands=['exchange'])
def exchange_message(message):
    amount, base_currency, convert_to = parse_text(message.text)
    try:
        result = convert(amount, base_currency, convert_to)
        bot.send_message(message.chat.id, text=f'{amount} USD = {result} {convert_to}')
    except ExchangeRatesApiError:
        bot.send_message(chat_id=message.chat.id, text='Exchange rates server is not available. Sorry')
    except WrongCommand:
        bot.send_message(message.chat.id, text=f'Wrong command :(')

@bot.message_handler(commands=['history'])
def history_message(message):
    try:
        text = message.text.split()[-1]
        base, currency = text.split('/')
        rates = ratesapi.get_history_for_7_days(currency=currency, base=base)
        if 'error' in rates:
            bot.send_message(message.chat.id, text='No exchange rate data is available for the selected currency.')
        else:
            values = [(day, rates[day][currency]) for day in rates]
            values.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))
            values = [value[1] for value in values]
            if None in values:
                bot.send_message(message.chat.id, text='No exchange rate data is available for the selected currency.')
            else:
                plt.plot(range(1, len(values) + 1), values)
                plt.title(f'{base} - {currency}')
                plt.ylabel(currency)
                plt.xlabel('last 7 days')
                with BytesIO() as output:
                    plt.savefig(output)
                    bot.send_photo(message.chat.id, photo=output.getvalue())
    except ExchangeRatesApiError:
        bot.send_message(chat_id=message.chat.id, text='Exchange rates server is not available. Sorry')
    except ValueError:
        bot.send_message(message.chat.id, text='No exchange rate data is available for the selected currency.')


@bot.message_handler(commands=['help'])
def help_message(message):
    text = """
    list - latest exchange rates in a listview.

exchange - exchange USD to another currency.Command example:'/exchange 10 USD to CAD'

history - return an image graph chart which shows the exchange rate graph of the selected currency for the last 7 days.
Command example:'/history USD/CAD'
    """
    bot.send_message(message.chat.id, text=text)

if __name__ == '__main__':
    db.init_db()
    bot.polling()
