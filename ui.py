import curses
import curses.textpad

def set_window_parameters():
    """
    Function to set all the window sizes and placements on the screen.
    Returns a dictionary of all curses windows where key is a string
    that is the title of the window (eg 'twitter'), and the value is the
    curses window object.

    """

    max_y, max_x = curses.initscr().getmaxyx()
    VERTICAL_SPLIT = 0.6
    HORIZONTAL_SPLIT = 0.5
    INPUT_WINDOW_LINES = 2
    INPUT_INDENT = 1
    
    window_width = {
        'twitter': int(max_x * (1 - VERTICAL_SPLIT)),
        'monitor': int(max_x * VERTICAL_SPLIT),
        'rss'    : int(max_x * VERTICAL_SPLIT),
        'input'  : int(max_x * VERTICAL_SPLIT) - INPUT_INDENT
    }

    window_height = {
        'twitter': int(max_y),
        'monitor': int(max_y * HORIZONTAL_SPLIT) - INPUT_WINDOW_LINES,
        'rss'    : int(max_y * HORIZONTAL_SPLIT),
        'input'  : INPUT_WINDOW_LINES
    }

    window_row_begin = {
        'twitter': 0,
        'monitor': int(max_y * HORIZONTAL_SPLIT),
        'rss'    : 0,
        'input'  : max_y - INPUT_WINDOW_LINES
    }

    window_column_begin = {
        'twitter': int(max_x * VERTICAL_SPLIT),
        'monitor': 0,
        'rss'    : 0,
        'input'  : INPUT_INDENT
    }

    twitter_window = curses.newwin(
                                    window_height['twitter'], 
                                    window_width['twitter'],
                                    window_row_begin['twitter'],
                                    window_column_begin['twitter'])

    rss_window = curses.newwin(
                                    window_height['rss'], 
                                    window_width['rss'],
                                    window_row_begin['rss'],
                                    window_column_begin['rss'])

    monitor_window = curses.newwin(
                                    window_height['monitor'], 
                                    window_width['monitor'],
                                    window_row_begin['monitor'],
                                    window_column_begin['monitor'])

    input_window = curses.newwin(
                                    window_height['input'], 
                                    window_width['input'],
                                    window_row_begin['input'],
                                    window_column_begin['input'])

    window_dict =  {
        'twitter': twitter_window,
        'monitor': monitor_window,
        'rss'    : rss_window,
        'input'  : input_window
    }

    return window_dict