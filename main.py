import telebot
import os
from datetime import datetime
import exchange_rates as ratesio
import bot_db as db
from matplotlib import pyplot as plt
from io import BytesIO

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
db.init_db()


class WrongCommand(Exception):
    pass


def time_since_last_update(timestamp):
    now = datetime.now()
    last_update = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    delta = now - last_update
    seconds = delta.total_seconds()
    minutes = (seconds % 3600) // 60
    return minutes


def handle_text(text):
    word_list = text.split()[1:]
    try:
        value = float(word_list[0].strip('$'))
    except ValueError:
        raise WrongCommand
    except IndexError:
        raise WrongCommand
    convert_to = word_list[-1]
    return value, convert_to


def convert(value, currency):
    rate = db.get_currency_rate(currency=currency)
    if rate is not None:
        return value * rate
    else:
        try:
            rate = float(ratesio.get_latest_rates()[currency])
            return value * rate
        except KeyError:
            raise WrongCommand


@bot.message_handler(commands=['list', 'lst'])
def list_message(message):
    text = ''
    timestamp = db.get_timestamp()
    if timestamp is not None and time_since_last_update(timestamp) < 10:
        rates = db.get_rates()
        for currency in rates:
            text += f'{currency[0]}: {currency[1]}\n'
    else:
        rates = ratesio.get_latest_rates()
        db.save_rates(rates=rates)
        for currency in rates:
            text += f'{currency}: {round(rates[currency], 2)}\n'

    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(commands=['exchange'])
def exchange_message(message):
    try:
        value, convert_to = handle_text(message.text)
        res = convert(value, convert_to)
        bot.send_message(message.chat.id, text=f'{value} USD = {round(res, 2)} {convert_to}')
    except WrongCommand:
        bot.send_message(message.chat.id, text=f'Wrong command :(')


@bot.message_handler(commands=['history'])
def history_message(message):
    try:
        text = message.text.split()[-1]
        base, currency = text.split('/')
        data = ratesio.get_history_for_7_days(currency=currency, base=base)
        if 'error' in data:
            bot.send_message(message.chat.id, text='No exchange rate data is available for the selected currency.')
        else:
            values = []
            for day in data['rates']:
                values.append((day, data['rates'][day][currency]))
            values.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))
            values = [value[1] for value in values]

            plt.plot(range(1, len(values) + 1), values)
            plt.ylabel(currency)
            plt.xlabel('last 7 days')
            with BytesIO() as output:
                plt.savefig(output)
                bot.send_photo(message.chat.id, photo=output.getvalue())
    except ValueError:
        bot.send_message(message.chat.id, text=f'Wrong command :(')
    except KeyError:
        bot.send_message(message.chat.id, text=f'Wrong command :(')


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
    bot.polling()
