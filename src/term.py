import os
os.system("") # allows terminal to receive control sequences

BELL = "\x07"
BACKSPACE = "\x08"
ESCAPE = "\x1b"

def nav_up(amount: int) -> str:
    '''Yield code to navigate `amount` lines up'''
    return ESCAPE + "[{}A".format(amount)

def nav_down(amount: int) -> str:
    '''Yield code to navigate `amount` lines down'''
    return ESCAPE + "[{}B".format(amount)

def nav_right(amount: int) -> str:
    '''Yield code to navigate `amount` columns right'''
    return ESCAPE + "[{}C".format(amount)

def nav_left(amount: int) -> str:
    '''Yield code to navigate `amount` columns left'''
    return ESCAPE + "[{}D".format(amount)

def nav_up_col_0(amount: int) -> str:
    '''Yield could to navigate to the beginning of the line `amount` up'''
    return ESCAPE + "[{}E".format(amount)

def nav_down_col_0(amount: int) -> str:
    '''Yield could to navigate to the beginning of the line `amount` down'''
    return ESCAPE + "[{}F".format(amount)

def nav_cursor(position: int) -> str:
    '''Yield code to navigate to column `position`'''
    return ESCAPE + "[{}G".format(position)

ERASE_TILL_LINE_END = ESCAPE + "[0K"
ERASE_FROM_LINE_START = ESCAPE + "[1K"
ERASE_LINE = ESCAPE + "[2K"

TERM_RESET = ESCAPE + "[0m"

COLORS = {
        'fg': {
            'black': 30, 'red': 31, 'green': 32, 'yellow': 33, 'blue': 34,
            'magenta': 35, 'cyan': 36, 'white': 37, 'default': 39},
        'bg': {
            'black': 40, 'red': 41, 'green': 42, 'yellow': 43, 'blue': 44,
            'magenta': 45, 'cyan': 46, 'white': 47, 'default': 49}
        }

def term_color_fg(color: str) -> str:
    '''Yield code to set terminal foreground color'''
    code = COLORS['fg'].get(color)
    return ESCAPE + "[{}m".format(code) if code is not None else ''

def term_color_bg(color: str) -> str:
    '''Yield code to set terminal background color'''
    code = COLORS['bg'].get(color)
    return ESCAPE + "[{}m".format(code) if code is not None else ''

def term_color(fg_color: str, bg_color: str) -> str:
    '''Yield code to set terminal color'''
    fg_code = COLORS['fg'].get(fg_color)
    bg_code = COLORS['bg'].get(bg_color)
    if fg_code is None or bg_code is None:
        return ''

    return ESCAPE + "[{};{}m".format(fg_code, bg_code)
