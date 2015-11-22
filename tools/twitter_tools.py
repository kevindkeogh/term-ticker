from datetime import datetime, timedelta
from html import unescape
import json
import twitter
import time
import commands

class TermTickerTweet:
    """
    Hold the json return for each tweet and format for printing
    """
    user = ''
    handle = ''
    timestamp = ''
    text = ''

    def __init__(self, tweet, line_length):
        self.tweet = tweet
        self.user = [tweet['user']['name']]
        self.handle = ['@' + tweet['user']['screen_name']]
        self.timestamp = [self.get_timestamp(tweet)]
        if self.tweet.get('retweeted_status'):
            self.text = 'RT @' + tweet['retweeted_status']['user']['screen_name']
            self.text = self.text + ': ' + tweet['retweeted_status']['text']
        elif self.tweet.get('text'):
            self.text = tweet['text']
        self.text = unescape(self.text)    
        self.text = self.parse_tweet_to_list(self.text, line_length)

    def get_timestamp(self, tweet):
        """
        Convert twitter timestamp to local time with ISO format
        """
        clean_timestamp = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        utc_offset = time.localtime().tm_gmtoff / 3600
        local_timestamp = clean_timestamp + timedelta(hours=utc_offset)
        local_timestamp = datetime.strftime(local_timestamp, '%Y-%m-%d %H:%M:%S')
        return local_timestamp

    def get_full_urls(self, tweet):
        """
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

    def save_tweet(self, tweet, filepath):
        """
        Saves tweet to json file.
        TODO: update so that these are saved to a db. Probably need to consider multi-threading if
        I do this.
        """
        jsonfile = open(filepath, 'a')
        jsonfile.write("{}\n".format(json.dumps(tweet)))
        jsonfile.close()

    def parse_tweet_to_list(self, text_string, line_length):
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

def auth_and_return_stream(keys):
    auth = twitter.OAuth(keys['TWITTER_ACCESS_TOKEN'],
                         keys['TWITTER_ACCESS_KEY'], 
                         keys['TWITTER_CONSUMER_KEY'],
                         keys['TWITTER_CONSUMER_SECRET'])
    stream = twitter.TwitterStream(auth=auth, domain='userstream.twitter.com')
    return stream

def twitter_feed(**termticker_dict):
    window = termticker_dict['window_dict']['twitter']
    lock = termticker_dict['lock']
    keys = termticker_dict['twitter_keys']
    stream = auth_and_return_stream(keys)
    _, line_length = window.getmaxyx()
    line_length = line_length - 2 # minus the border
    for tweet in stream.user():
        if tweet.get('text'):
            with lock:
                twt = TermTickerTweet(tweet, line_length)
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
        if tweet.get('heartbeat_timeout'):
            commands.scroll_and_add_line(termticker_dict, 
                                              'twitter',
                                              'Twitter timed out.')


def read_keys():
    with open('tools/twitter keys.json', 'r') as keyfile:
        keys = json.load(keyfile)
    if 'TWITTER_ACCESS_TOKEN' not in keys:
        access_token, access_key = twitter.oauth_dance('messingaround1',
                                                       keys['TWITTER_CONSUMER_KEY'],
                                                       keys['TWITTER_CONSUMER_SECRET'])
        keys['TWITTER_ACCESS_TOKEN'] = access_token
        keys['TWITTER_ACCESS_KEY']   = access_key
        with open('tools/twitter keys.json', 'w') as keyfile:
            keyfile.write(json.dumps(keys))
    return keys