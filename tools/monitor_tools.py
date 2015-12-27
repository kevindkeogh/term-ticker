import sqlite3

def setup_monitor_tables(cursor):
    sql_create_table_monitor_feeds   =  ''' CREATE TABLE if not EXISTS 
                                        MONITOR_FEEDS
                                        (display_name TEXT, ticker_code TEXT UNIQUE)
                                        '''
    sql_create_table_monitor_prices  =  ''' CREATE TABLE if not EXISTS
                                        MONITOR_PRICES
                                        (date INT)
                                        '''
    cursor.execute(sql_create_table_monitor_feeds)
    cursor.execute(sql_create_table_monitor_prices)
    add_monitor_prices_columns(cursor)
    


def add_sql_column(cursor, table_name, column_name):
    command = '''ALTER TABLE {0} ADD COLUMN '{1}' REAL'''.format(table_name, column_name)
    cursor.execute(command)

def add_monitor_prices_columns(cursor):
    tickers_columns = cursor.execute(   '''SELECT ticker_code
                                        FROM MONITOR_FEEDS
                                        ''' 
                                    )
    prices_columns  = [info[1] for info in cursor.execute('PRAGMA table_info(MONITOR_PRICES)')]
    prices_columns.remove('date')
    # If empty, add SPX
    if prices_columns == []:
        cursor.execute('''INSERT INTO MONITOR_FEEDS
                          VALUES ('SPX', '^GSPC')
                       '''
                       )
        prices_columns  = [info[1] for info in cursor.execute('PRAGMA table_info(MONITOR_PRICES)')]
        tickers_columns = cursor.execute(   '''SELECT ticker_code
                                            FROM MONITOR_FEEDS
                                            '''
                                        )
    # Add column to the table if it doesn't exist
    for ticker in tickers_columns:
        if ticker not in prices_columns:
            add_sql_column(cursor, 'MONITOR_PRICES', ticker[0])

connection = sqlite3.connect('sample.db')
cursor = connection.cursor()
setup_monitor_tables(cursor)