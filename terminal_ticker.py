# standard library
import curses
import sqlite3
import threading

# term ticker
import commands
import tools.twitter_tools as twitter_tools
import tools.rss_tools as rss_tools
import ui

def start_terminal_ticker(stdscr, twitter_keys):

    # Set up windows
    window_dict = ui.set_window_parameters()
    input_window = window_dict['input']
    
    for name, window in window_dict.items():
        if name is not 'input':
            window.border()
            window.addstr(0, 0, name)
            window.refresh()
            window.scrollok(True)   

    # Get commands dict
    commands_dict = commands.set_commands_dict()

    # Set up threads
    lock = threading.Lock()
    threads = set()
    connection = sqlite3.connect('term_ticker.db',
                                 check_same_thread=False)

    # Create a global dict to pass stuff around the threads
    # and to pass the lock/queues when completing commands
    termticker_dict = {
        'connection'         : connection,
        'input_window'       : input_window,
        'lock'               : lock,
        'twitter_keys'       : twitter_keys,
        'window_dict'        : window_dict
    }

    # Create threads
    twitter_thread = threading.Thread(name   = 'twitter_thread',
                                      target = twitter_tools.twitter_feed,
                                      kwargs = termticker_dict)

    rss_thread     = threading.Thread(name   = 'rss_thread',
                                      target = rss_tools.rss_feed,
                                      kwargs = termticker_dict)

    threads.add(twitter_thread)
    threads.add(rss_thread)

    for thread in threads:
        thread.daemon = True
        thread.start()

    application_running = True

    while application_running:
        try:
            curses.noecho()
            input_window.keypad(1)
            input_edit = curses.textpad.Textbox(input_window)
            input_edit.edit()
            message = input_edit.gather().strip()
            window_key, command_key, args = commands.parse_input_text(message)
            if window_key in window_dict:
                if command_key in commands_dict[window_key]:
                    commands_dict[window_key][command_key](termticker_dict, window_key, args)
                else:
                    commands.print_warning(input_window, 
                                   'Command does not exist. Press any key to continue')
            elif window_key == 'all' and command_key == 'quit':
                application_running = False
            else:
                commands.print_warning(input_window, 
                               'Window does not exist. Press any key to continue')
            # elif window_key == 'all':
            #     all_commands[command_key](args)
            input_window.clear()
        except KeyboardInterrupt:
            return
        finally:
            curses.endwin()
            connection.close()

def main(stdscr, twitter_keys):
    curses.curs_set(0)
    start_terminal_ticker(curses.initscr(), twitter_keys)

if __name__ == '__main__':
    # this needs to run first in case this is the first use,
    # and user needs to use browser to get access keys
    twitter_keys = twitter_tools.read_keys()
    curses.wrapper(main, twitter_keys)
