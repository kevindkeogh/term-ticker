# standard library
import datetime
import feedparser
import hashlib
import sqlite3
import time

# term ticker
import commands

def setup_rss_tables(cursor):
    sql_create_table_rss_feeds = ''' CREATE TABLE if not EXISTS 
                                     RSS_FEEDS 
                                     (name TEXT,  address TEXT UNIQUE)
                                 '''    
    sql_create_table_rss_stories = ''' CREATE TABLE if not EXISTS
                                       RSS_STORIES
                                       (feed TEXT, title TEXT, time TEXT, 
                                        link TEXT, hash TEXT UNIQUE)
                                   '''
    sql_count_rss_feeds = '''SELECT COUNT(*) FROM RSS_FEEDS'''
    cursor.execute(sql_create_table_rss_feeds)
    cursor.execute(sql_create_table_rss_stories)
    num_feeds_obj = cursor.execute(sql_count_rss_feeds)
    num_feeds = num_feeds_obj.fetchone()[0]
    if num_feeds == 0:
        default_feeds = {
        'NYT'    : 'http://www.nytimes.com/services/xml/rss/nyt/HomePage.xml',
        'CNN'    : 'http://rss.cnn.com/rss/cnn_topstories.rss',
        'UPI'    : 'http://rss.upi.com/news/news.rss'
            }
        insert_new_rss_feeds(cursor, default_feeds)


def insert_new_rss_feeds(cursor, feeds_dict):
    for key, value in feeds_dict.items():
        cursor.execute(''' INSERT OR IGNORE INTO
                           RSS_FEEDS(name, address)
                           VALUES (?, ?)
                       '''
                       ,(key, value))

def get_rss_feeds(cursor):
    feeds_list = cursor.execute('''SELECT * FROM RSS_FEEDS''')
    return feeds_list

def rss_entry_exists(cursor, hashcode):
    sql_select_count_rss_stories_hash = ''' SELECT COUNT(*)
                                        FROM RSS_STORIES
                                        WHERE hash = ?
                                        '''
    query_list = cursor.execute(sql_select_count_rss_stories_hash, (hashcode, ))
    exists = query_list.fetchone()[0]
    if exists == 1:
        return True
    elif exists == 0:
        return False


def insert_new_rss_entries(cursor, feed_tuple):
    sql_insert_rss_stories = ''' INSERT OR IGNORE INTO
                             RSS_STORIES
                             VALUES (?, ?, ?, ?, ?)
                            '''
    db_entries = []
    feed_name = feed_tuple[0]
    parsed_feed = parse_feed(feed_tuple[1])
    for item in parsed_feed.entries:
        item_title = item['title']
        item_time = datetime.datetime(*item.published_parsed[:6]).isoformat()
        item_link = item['link']
        item_hashstring = (feed_name + ' ' + item_title).encode('utf-8')
        item_hashcode = hashlib.md5(item_hashstring).hexdigest()
        if not rss_entry_exists(cursor, item_hashcode):
            db_entry = (feed_name, item_title, item_time, item_link, item_hashcode)
            db_entries.append(db_entry)
    cursor.executemany(sql_insert_rss_stories, db_entries)

def parse_feed(feed_url):
    rss_feed = feedparser.parse(feed_url)
    return rss_feed

def poll_feeds(connection, rss_feeds, num_rows, poll=False):
    cursor = connection.cursor()
    if poll:
        for feed in rss_feeds:
            insert_new_rss_entries(cursor, feed)
        connection.commit()
    sql_select_rss_stories = ''' SELECT * FROM
                                (SELECT * FROM
                                 RSS_STORIES 
                                 ORDER BY time DESC
                                 LIMIT ?)
                                 ORDER BY time ASC
                            '''
    stories = cursor.execute(sql_select_rss_stories, (num_rows, ))
    return stories

def update_rss_window(termticker_dict, window_key, args, poll=False):
    window = termticker_dict['window_dict']['rss']
    num_rows, _ = window.getmaxyx()
    connection = termticker_dict['connection']
    cursor = connection.cursor()
    lock = termticker_dict['lock']
    rss_feeds = get_rss_feeds(cursor)
    stories = poll_feeds(connection, rss_feeds, num_rows, poll=poll)
    with lock:
        for story in stories:
            org, title, rss_time, line, _ = story
            commands.scroll_and_add_line(termticker_dict,
                                         'rss',
                                         org + ' ' + title)

def rss_feed(**termticker_dict):
    cursor = termticker_dict['connection'].cursor()
    setup_rss_tables(cursor)
    while True:
        update_rss_window(termticker_dict, 'rss', '', poll=True)
        time.sleep(600)