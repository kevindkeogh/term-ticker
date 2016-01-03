# standard library
import curses
import sqlite3
import threading

# term ticker
import commands
import tools.thread_manager as thread_manager
import tools.twitter_tools as twitter_tools
import ui

def start_terminal_ticker(stdscr):

    # Set up windows
    window_dict  = ui.set_window_parameters()
    input_window = window_dict['input']
    
    for name, window in window_dict.items():
        if name is not 'input':
            window.border()
            window.addstr(0, 0, name)
            window.refresh()
            window.scrollok(True)

    # Get dict stuff
    commands_dict = commands.set_commands_dict()
    connection = sqlite3.connect('term_ticker.db',
                                 check_same_thread=False)
    twitter_keys = twitter_tools.read_keys()

    # Create a global dict to pass stuff around the threads
    # and to pass the lock/queues when completing commands
    termticker_dict = {
        'connection'         : connection,
        'input_window'       : input_window,
        'lock'               : threading.Lock(),
        'twitter_keys'       : twitter_keys,
        'window_dict'        : window_dict
    }

    # Create threads
    term_threads = thread_manager.TermTickerThreadManager(termticker_dict)
    threads = ['twitter_thread', 'rss_thread']
    for thread in threads:
        term_threads.add_thread(thread)

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
                    commands_dict[window_key][command_key](termticker_dict,
                                                           window_key,
                                                           args)
                elif command_key in term_threads.commands_dict:
                    term_threads.commands_dict[command_key](window_key,
                                                            command_key,
                                                            args)
                else:
                    commands.print_warning(input_window, 
                                           'Command does not exist. \
                                           Press any key to continue')
            elif window_key == 'all' and command_key == 'quit':
                application_running = False
            else:
                commands.print_warning(input_window, 
                                       'Window does not exist. \
                                       Press any key to continue')
            # elif window_key == 'all':
            #     all_commands[command_key](args)
            input_window.clear()
        except KeyboardInterrupt:
            return
    
    curses.endwin()
    connection.close()

def main(stdscr):
    curses.curs_set(0)
    start_terminal_ticker(curses.initscr())

if __name__ == '__main__':
    # this needs to run first in case this is the first use,
    # and user needs to use browser to get access keys
    twitter_tools.read_keys()
    curses.wrapper(main)
