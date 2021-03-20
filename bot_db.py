import sqlite3


def ensure_connection(func):
    def inner(*args, **kwargs):
        with sqlite3.connect('bot.db') as conn:
            kwargs['conn'] = conn
            res = func(*args, **kwargs)
        return res

    return inner


@ensure_connection
def init_db(conn, force=False):
    cursor = conn.cursor()
    if force:
        cursor.execute('DROP TABLE IF EXISTS exchange_rates')

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exchange_rates (
        currency VARCHAR(30),
        rate REAL,
        added DATE DEFAULT (datetime('now', 'localtime'))
    )
    """)
    conn.commit()


@ensure_connection
def save_rates(conn, rates):
    cursor = conn.cursor()
    cursor.execute('DELETE FROM exchange_rates')
    for currency in rates:
        cursor.execute(
            'INSERT INTO exchange_rates (currency, rate) VALUES (?, ?)',
            (currency, round(float(rates[currency]), 2))
        )


@ensure_connection
def get_timestamp(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT added FROM exchange_rates')
    res = cursor.fetchone()
    if res is not None:
        return res[0]


@ensure_connection
def get_rates(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT currency, rate FROM exchange_rates')
    return cursor.fetchall()


@ensure_connection
def get_currency_rate(conn, currency):
    cursor = conn.cursor()
    cursor.execute('SELECT rate FROM exchange_rates WHERE currency = ?', (currency,))
    res = cursor.fetchone()
    if res is not None:
        return res[0]
