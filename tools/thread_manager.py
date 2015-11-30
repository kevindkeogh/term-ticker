# standard libary
import threading

# term ticker
import commands
import tools.rss_tools as rss_tools
import tools.twitter_tools as twitter_tools

class TermTickerThreadManager():
    """
    """
    def __init__(self, termticker_dict):
        self.window_dict = {
        'monitor' : 'monitor_thread',
        'rss'     : 'rss_thread',
        'twitter' : 'twitter_thread'
        }
        
        self.functions_dict = {
        'monitor_thread': '',
        'rss_thread'    : rss_tools.rss_feed,
        'twitter_thread': twitter_tools.twitter_feed
        }

        self.commands_dict = {
        'alive' : self.call_check_thread,
        'exit'  : self.call_exit_thread
        }

        self.threads = {}
        self.termticker_dict = termticker_dict

    ### Utility commands

    def add_thread(self, name):
        thread = threading.Thread(name   = name,
                                  target = self.functions_dict[name],
                                  kwargs = self.termticker_dict)
        thread.daemon = True
        thread.start()
        self.threads[name] = thread

    def check_thread(self, window_name):
        return self.threads[self.window_dict[window_name]].is_alive()

    def exit_thread(self, window_name):
        if not self.check_thread(window_name):
            self.threads[window_dict[window_name]].exit()

    ### Callable Commands

    def call_check_thread(self, window_key, command_key, args):
        if self.check_thread(window_key):
            is_alive = 'alive'
        else:
            is_alive = 'not alive'
        commands.print_warning(self.termticker_dict['input_window'],
                               'Thread is ' + is_alive + '. Press ' + \
                               'any key to continue.')

    def call_exit_thread(self, window_key, command_key, args):
        self.exit_thread(window_key) 
        commands.print_warning(self.termticker_dict['input_window'],
                               window_key + ' thread has been killed. ' + \
                               'Press any key to continue.')




