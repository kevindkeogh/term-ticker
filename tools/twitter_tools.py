# standard library
from datetime import datetime, timedelta
import json
from html import unescape
import time

# external dependencies
import twitter
import twitter.api

# term ticker
import commands

class TermTickerTweet():
    """
    The TermTickerTweet object is a utility object, used for the purpose
    of organizing the information embedded in the tweet JSONs served by
    Twitter. The object takes 2 variables at initialization, the tweet JSON
    and the length of the window that will fit the tweet text.

    Methods:
    get_timestamp:
        args:
            tweet (dict)
        returns:
            string, time in ISO format

    parse_tweet_to_list:
        args:
            tweet (string), text of tweet
            line_length (int), length of space on window line
        returns:
            list, split of tweet such that each line should be visible in 
                  the window
    """

    def __init__(self, tweet, line_length):
        self.tweet     = tweet
        self.user      = [tweet['user']['name']]
        self.handle    = ['@' + tweet['user']['screen_name']]
        self.timestamp = [self.get_timestamp(tweet)]
        
        if self.tweet.get('retweeted_status'):
            self.text = 'RT @' + tweet['retweeted_status']['user']['screen_name']
            self.text = self.text + ': ' + tweet['retweeted_status']['text']
        elif self.tweet.get('text'):
            self.text = tweet['text']
        
        self.text   = unescape(self.text)    
        self.text   = self.parse_tweet_to_list(self.text, line_length)

    def get_timestamp(self, tweet):
        """
        Convert twitter timestamp to local time with ISO format
        """
        clean_timestamp = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        utc_offset      = time.localtime().tm_gmtoff / 3600
        local_timestamp = clean_timestamp + timedelta(hours=utc_offset)
        local_timestamp = datetime.strftime(local_timestamp, '%Y-%m-%d %H:%M:%S')
        return local_timestamp

    def get_full_urls(self, tweet):
        """
        DEPRECATED

        Twitter gives the t.co urls for everything. This replaces the link urls with their actual
        urls. The replacement for the media urls is commented out, links are just longer twitter 
        links.
        """
        full_text = tweet['text']
        if tweet['entities'].get('urls'):
            for url in tweet['entities']['urls']:
                full_text = full_text.replace(url['url'], url['expanded_url'])
        # Gets direct twitter link for image posts, unnecessary and ended up being longer than
        # t.co links
        # if tweet['entities'].get('media'):
        #    for url in tweet['entities']['media']:
        #        full_text = full_text.replace(url['url'], url['expanded_url'])
        return full_text

    def parse_tweet_to_list(self, text_string, line_length):
        """
        Return 1 string to list of strings, split into readable lengths in the window
        """
        lines = text_string.splitlines()
        text_strings = []
        current_line = ''
        for line in lines:
            line = line.split(' ')
            current_line = ''
            for num, word in enumerate(line):
                if len(current_line) + len(word) < line_length and num + 1 == len(line):
                    current_line = current_line + ' ' + word
                    text_strings.append(current_line.lstrip(' '))
                elif len(current_line) + len(word) < line_length:
                    current_line = current_line + ' ' + word
                elif len(word) > line_length:
                    text_strings.append(current_line.lstrip(' '))
                    text_strings.append(word.lstrip(' '))
                    current_line = ''
                elif num + 1 == len(line):
                    text_strings.append(current_line.lstrip(' '))
                    text_strings.append(word.lstrip(' '))
                else:
                    text_strings.append(current_line.lstrip(' '))
                    current_line = word
        return text_strings

def save_tweet(connection, tweet):
    """
    Saves tweets to the database in the 'TWITTER_TWEETS' table, for reference
    use.

    Args:
        connection (sqlite object), db connection
        tweet (TermTickerTweet object), tweet object

    """
    sql_insert_tweet = ''' INSERT INTO
                           TWITTER_TWEETS(username, time, json)
                           VALUES (?, ? ,?)
                       '''
    db_entry = (tweet.handle[0], tweet.timestamp[0], str(tweet.tweet))
    connection.cursor().execute(sql_insert_tweet, db_entry)
    connection.commit()

def auth_and_return_stream(input_window, keys):
    """
    Authenticates and returns twitter stream object (using the twitter library
    by sixohsix -- https://github.com/sixohsix/twitter).
    
    Args:
        keys (dict), dictionary of keys/token codes

    Returns:
        stream (twitter object), object that yields live tweets
    """
    try:
        auth   = twitter.OAuth(keys['TWITTER_ACCESS_TOKEN'],
                               keys['TWITTER_ACCESS_KEY'], 
                               keys['TWITTER_CONSUMER_KEY'],
                               keys['TWITTER_CONSUMER_SECRET'])
        stream = twitter.TwitterStream(auth=auth, domain='userstream.twitter.com')
        return stream
    except twitter.api.TwitterHTTPError:
        commands.print_warning(input_window, 'Could not connect to Twitter')

def twitter_feed(**termticker_dict):
    """
    Main twitter function, it sets up the twitter thread, accepts the
    stream object, and prints tweets as they are yielded by the object.
    In the event that the stream object yields a timeout, the loop 
    completes.

    Note that this function creates the 'TWITTER_TWEETS' table in the event
    that it has not already been created.
    """
    # get useful variables
    window                  = termticker_dict['window_dict']['twitter']
    input_window            = termticker_dict['input_window']
    lock                    = termticker_dict['lock']
    keys                    = termticker_dict['twitter_keys']
    connection              = termticker_dict['connection']
    
    # authenticate and create stream
    stream                  = auth_and_return_stream(input_window, keys)
    
    # get line length for printing tweets 
    _, line_length          = window.getmaxyx()
    line_length             = line_length - 2 # minus the border
    
    # create twitter table (if needed) to save tweets
    sql_create_table_tweets = ''' CREATE TABLE if not EXISTS
                                  TWITTER_TWEETS
                                  (username TEXT, time TEXT, json TEXT)
                              '''
    connection.cursor().execute(sql_create_table_tweets)
    
    # main twitter loop
    for tweet in stream.user():
        with lock:
            if tweet.get('text'):
                twt = TermTickerTweet(tweet, line_length)
                save_tweet(connection, twt)
                commands.scroll_and_add_line(termticker_dict, 
                                              'twitter',
                                              '￣')
                commands.scroll_and_add_line(termticker_dict,
                                              'twitter',
                                              twt.user)
                commands.scroll_and_add_line(termticker_dict,
                                              'twitter',
                                              twt.handle)
                commands.scroll_and_add_line(termticker_dict, 
                                              'twitter',
                                              twt.timestamp)
                commands.scroll_and_add_line(termticker_dict,
                                              'twitter',
                                              twt.text)
            elif tweet.get('heartbeat_timeout'):
                commands.scroll_and_add_line(termticker_dict, 
                                              'twitter',
                                              ' ')
                commands.scroll_and_add_line(termticker_dict, 
                                              'twitter',
                                              'Twitter timed out.')

def read_keys():
    """
    The read keys function reads the keys from the tools/twitter keys.json
    file, and returns them to the reader. This needs to be done before the
    curses windows are created, because in the event that no access key/token
    is available, the twitter oauth_dance function uses the terminal to verify
    and accept the token.

    This function should work normally (and return consumer and access keys/tokens)
    after the first time the function is run.

    Returns:
        keys (dict), dictionary of twitter keys/tokens used for authentication
    """
    with open('tools/twitter keys.json', 'r') as keyfile:
        keys = json.load(keyfile)
    if 'TWITTER_ACCESS_TOKEN' not in keys:
        access_token, access_key = twitter.oauth_dance('Term Ticker',
                                                       keys['TWITTER_CONSUMER_KEY'],
                                                       keys['TWITTER_CONSUMER_SECRET'])
        keys['TWITTER_ACCESS_TOKEN'] = access_token
        keys['TWITTER_ACCESS_KEY']   = access_key
        with open('tools/twitter keys.json', 'w') as keyfile:
            keyfile.write(json.dumps(keys))
    return keys
