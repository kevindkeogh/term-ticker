import threading

import commands
import tools.rss_tools as rss_tools
import tools.twitter_tools as twitter_tools

### CALLABLE COMMANDS

def windowprint(termticker_dict, window_key, args):
    text_string = " ".join(args)
    commands.scroll_and_add_line(termticker_dict, window_key, text_string)

def clear_window(termticker_dict, window_key, args):
    window = termticker_dict['window_dict'][window_key]
    window.clear()
    window.border()
    window.addstr(0, 0, window_key)
    window.refresh()

def close_application(termticker_dict, window_key, args):
    curses.endwin()

def add_rss_feed(termticker_dict, window_key, args):
    connection = termticker_dict['connection']
    sql_insert_rss_feed = ''' INSERT OR IGNORE INTO
                              RSS_FEEDS(name, address)
                              VALUES (?, ?)
                          '''
    name    = args.split(' ')[0]
    address = (' '.join(args.split(' ')[1:])).replace(' ', '')
    connection.cursor().execute(sql_insert_rss_feed, (name, address))
    connection.commit()

def restart_twitter_thread(termticker_dict, window_key, args):
    if termticker_dict['threads']['twitter_thread'].is_alive():
        print_warning(termticker_dict['input_window'], 'Thread is alive')
    else:
        start_thread('twitter_thread',
                     twitter_tools.twitter_feed,
                     termticker_dict)

### UTILITY COMMANDS

def parse_input_text(input_string):
    window_key = input_string.split()[0].lower()
    command_key = input_string.split()[1:2]
    if command_key != []: command_key = command_key[0].lower()
    args = " ".join(input_string.split()[2:])
    return window_key, command_key, args


def scroll_and_add_line(termticker_dict, window_key, text_strings):
    window = termticker_dict['window_dict'][window_key.lower()]
    max_y_window, max_x_window = window.getmaxyx()
    line_length = max_x_window - 2
    if isinstance(text_strings, str): text_strings = [text_strings]
    for string in text_strings:
        window.scroll()
        window.move(max_y_window - 2, 0)
        window.deleteln()
        window.insertln()
        window.addstr(max_y_window - 2, 1, string)
        window.border()
        window.addstr(0, 0, window_key)
    window.refresh()

def print_warning(input_window, input_string):
    input_window.clear()
    input_window.addstr(0, 0, input_string)
    key_press = input_window.getch()

### SET COMMANDS

def set_commands_dict():

    twitter_commands = {
        'print'  : windowprint,
        'clear'  : clear_window,
        'restart': restart_twitter_thread
    }

    monitor_commands = {
        'print'  : windowprint,
        'clear'  : clear_window
    }

    rss_commands = {
        'print'  : windowprint,
        'clear'  : clear_window,
        'add'    : add_rss_feed,
        'update' : rss_tools.update_rss_window
    }

    all_commands = {
        'quit'   : close_application
    }

    commands_dict =  {
        'twitter': twitter_commands,
        'monitor': monitor_commands,
        'rss'    : rss_commands,
        'all'    : all_commands
    }

    return commands_dict