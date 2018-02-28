from __future__ import absolute_import

import time
import types

from getpass import getpass

from pwnlib import term
from pwnlib.log import getLogger

from pygments import highlight as hl
from pygments.lexers import guess_lexer, guess_lexer_for_filename
from pygments.formatters import TerminalFormatter, Terminal256Formatter
from pygments.util import ClassNotFound as pygmentsClassNotFound

log = getLogger(__name__)

def ask(prompt, default=None, required=False):
    """Presents the user with prompt which the user might answer.

    You can specify a default value or if the user answer must not be empty.

    Arguments:
      prompt   (string)          : The prompt to show
      default  (string, optional): The default option
      required (bool, optional)  : The answer must not be empty

    Returns:
      The user answer as a string (might be an empty string or default if provided)

    Raises:
      ValueError if `required` is not bool or None.

    Examples:
      >>> ask('Question:')
       [?] Question:
      ''

      >>> ask('Question:', default='Default answer')
       [?] Question: [Default answer]
      'Default answer'

      >>> ask('Question:', required=True)
       [?] Question:
       [?] Question:
       [?] Question:
       [?!] Question: answer
      'answer'
    """

    if not isinstance(required, (bool, types.NoneType)):
        raise ValueError('ask(): required must be a boolean or None')

    qm = term.text.bold_cyan('?')
    cprompt = ' [{qm}] {prompt} {default}'
    if default:
        cdef = '[{}] '.format(default)

    resp = raw_input(cprompt.format(qm=qm,
                                    prompt=prompt,
                                    default=cdef if default else '')).strip()
    if default and not resp:
        return default
    else:
        if required is True:
            i = 0
            while True:
                if not resp:
                    if i < 2:
                        qm = term.text.bold_yellow('?')
                        i += 1   # Don't need to continue incrementing after
                    else:
                        qm = term.text.bold_red('?!')
                    resp = raw_input(cprompt.format(qm=qm,
                                                    prompt=prompt,
                                                    default=cdef if default else '')).strip()
                else:
                    break
        return resp

def askpass(prompt, default=None, required=False):
    """Ask for sensitive data that won't be displayed.

    You can specify a default value or if the user answer must not be empty.
    This function works exactly the same as the function `ask()` above.

    Arguments:
      prompt   (string)          : The prompt to show
      default  (string, optional): The default option
      required (bool, optional)  : The answer must not be empty

    Returns:
      The user answer as a string (might be an empty string or default if provided)

    Raises:
      ValueError if `required` is not bool or None.
    """

    if not isinstance(required, (bool, types.NoneType)):
        raise ValueError('askpass(): required must be a boolean or None')

    cprompt = ' [{qm}] {prompt} {default}'

    if default:
        cdef = '[default] '
    resp = getpass(cprompt.format(qm=term.text.bold_magenta('?'),
                                    prompt=prompt,
                                    default=cdef if default else '')).strip()
    if default and not resp:
        return default
    else:
        if required is True:
            while True:
                if not resp:
                    resp = getpass(cprompt.format(qm=term.text.bold_magenta('?'),
                                                  prompt=prompt,
                                                  default='')).strip()
                else:
                    break
        return resp

def yesno(prompt, default = None):
    """Presents the user with prompt (typically in the form of question) which
    the user must answer yes or no.

    Arguments:
      prompt (str): The prompt to show
      default     : The default option;  `True` means "yes"

    Returns:
      `True` if the answer was "yes", `False` if "no"
"""

    if not isinstance(default, (bool, types.NoneType)):
        raise ValueError('yesno(): default must be a boolean or None')

    if term.term_mode:
        term.output(' [{qm}] {prompt} ['.format(qm = term.text.bold_cyan('?'),
                                                prompt = prompt))
        yesfocus, yes = term.text.bold('Yes'), 'yes'
        nofocus, no = term.text.bold('No'), 'no'
        hy = term.output(yesfocus if default == True else yes)
        term.output('/')
        hn = term.output(nofocus if default == False else no)
        term.output(']\n')
        cur = default
        while True:
            k = term.key.get()
            if   k in ('y', 'Y', '<left>') and cur != True:
                cur = True
                hy.update(yesfocus)
                hn.update(no)
            elif k in ('n', 'N', '<right>') and cur != False:
                cur = False
                hy.update(yes)
                hn.update(nofocus)
            elif k == '<enter>':
                if cur is not None:
                    return cur
    else:
        prompt = ' [{qm}] {prompt} [{yes}/{no}] '.format(qm = term.text.bold_cyan('?'),
                                                         prompt = prompt,
                                                         yes = 'Yes' if default == True else 'yes',
                                                         no = 'No' if default == False else 'no')
        while True:
            opt = raw_input(prompt).lower()
            if opt == '' and default != None:
                return default
            elif opt in ('y','yes'):
                return True
            elif opt in ('n', 'no'):
                return False
            print 'Please answer yes or no'

def options(prompt, opts, default = None):
    """Presents the user with a prompt (typically in the
    form of a question) and a number of options.

    Arguments:
      prompt (str): The prompt to show
      opts (list) : The options to show to the user
      default     : The default option to choose

    Returns:
      The users choice in the form of an integer.
"""

    if not isinstance(default, (int, long, types.NoneType)):
        raise ValueError('options(): default must be a number or None')

    if term.term_mode:
        numfmt = '%' + str(len(str(len(opts)))) + 'd) '
        print ' [{qm}] {prompt} ['.format(qm=term.text.bold_cyan('?'), prompt=prompt)
        hs = []
        space = '       '
        arrow = term.text.bold_green('    => ')
        cur = default
        for i, opt in enumerate(opts):
            h = term.output(arrow if i == cur else space, frozen = False)
            num = numfmt % (i + 1)
            term.output(num)
            term.output(opt + '\n', indent = len(num) + len(space))
            hs.append(h)
        ds = ''
        prev = 0
        while True:
            prev = cur
            was_digit = False
            k = term.key.get()
            if   k == '<up>':
                if cur is None:
                    cur = 0
                else:
                    cur = max(0, cur - 1)
            elif k == '<down>':
                if cur is None:
                    cur = 0
                else:
                    cur = min(len(opts) - 1, cur + 1)
            elif k == 'C-<up>':
                cur = 0
            elif k == 'C-<down>':
                cur = len(opts) - 1
            elif k in ('<enter>', '<right>'):
                if cur is not None:
                    return cur
            elif k in tuple('1234567890'):
                was_digit = True
                d = str(k)
                n = int(ds + d)
                if n > 0 and n <= len(opts):
                    ds += d
                elif d != '0':
                    ds = d
                n = int(ds)
                cur = n - 1

            if prev != cur:
                if prev is not None:
                    hs[prev].update(space)
                if was_digit:
                    hs[cur].update(term.text.bold_green('%5s> ' % ds))
                else:
                    hs[cur].update(arrow)
    else:
        linefmt =       '       %' + str(len(str(len(opts)))) + 'd) %s'
        while True:
            print ' [{qm}] {prompt} ['.format(qm=term.text.bold_cyan('?'), prompt=prompt)
            for i, opt in enumerate(opts):
                print linefmt % (i + 1, opt)
            s = '     Choice '
            if default:
                s += '[%s] ' % str(default)
            try:
                x = int(raw_input(s) or default)
            except (ValueError, TypeError):
                continue
            if x >= 1 and x <= len(opts):
                return x

def pause(n = None):
    """Waits for either user input or a specific number of seconds."""

    if n == None:
        if term.term_mode:
            log.info('Paused (press any to continue)')
            term.getkey()
        else:
            log.info('Paused (press enter to continue)')
            raw_input('')
    elif isinstance(n, (int, long)):
        with log.waitfor("Waiting") as l:
            for i in range(n, 0, -1):
                l.status('%d... ' % i)
                time.sleep(1)
            l.success()
    else:
        raise ValueError('pause(): n must be a number or None')

def more(text):
    """more(text)

    Shows text like the command line tool ``more``.

    If not in term_mode, just prints the data to the screen.

    Arguments:
      text(str): The text to show.

    Returns:
      :const:`None`
    """
    if term.term_mode:
        lines = text.split('\n')
        h = term.output(term.text.reverse('(more)'), float = True, frozen = False)
        step = term.height - 1
        for i in range(0, len(lines), step):
            for l in lines[i:i + step]:
                print l
            if i + step < len(lines):
                term.key.get()
        h.delete()
    else:
        print text


def less(text, filename=None):
    """Print text in less-like mode.

    Will display text that fit in terminal window and is scrollable.
    While exiting, terminal will be cleared from diplayed text.
    (Principally based on `more()`)

    It reacts to the following keys :
    `<down>`, `<enter>`, `<space>`, `<right>` : scroll down
    `<up>`, `<backspace>`, `<left>`           : scroll up
    'q', `<escape>`                           : exit

    If not in term_mode, just prints the data to the screen.

    Arguments:
        text     (string)          : The large text to display.
        filename (string, optional): The name of the file displayed.
                                     Prints ': `filename`' at the bottom of terminal

    Returns:
        Nothing.
    """
    def init(text):
        term.init()
        lines = text.split('\n')
        step = term.height - 1
        c = term.output(getprintable(lines, 0, step), float = True, frozen = False)
        f = term.output(term.text.reverse('(more)'), float = True, frozen = False)
        return (lines, step, c, f)

    def get_end_index(cursor, step, max):
        return cursor + step if cursor + step < max else -1

    def getprintable(lines, start, end):
        return '\n'.join(lines[start:end]) + '\n'

    def update_footer(footer, cursor, c_max, filename):
        if cursor >= c_max:
            footer.update(term.text.reverse('(END)'))
        elif cursor == 0:
            footer.update(term.text.reverse('(more)'))
        else:
            if filename:
                footer.update(term.text.reverse(': {fn}'.format(fn=filename)))
            else:
                footer.update(term.text.reverse(':'))

    if term.term_mode:
        lines, step, content, footer = init(text)
        cursor = 0
        cursor_max = len(lines) - step - 1

        while True:
            end = get_end_index(cursor, step, len(lines))

            content.update(getprintable(lines, cursor, end))
            update_footer(footer, cursor, cursor_max, filename)

            k = term.key.get()
            if k in ('<down>', '<enter>', '<space>', '<right>'):
                if cursor < cursor_max:
                    cursor += 1
            elif k in ('<up>', '<backspace>', '<left>'):
                if cursor > 0:
                    cursor -= 1
            elif k in ('q', '<escape>'):
                content.delete()
                footer.delete()
                break
    else:
        print text

def highlight(filepath, linenos=False, mode=None):
    """Simply highlight source files.

    Sometimes it might be useful to comfortably read source codes on targets.

    Arguments:
        filepath (string)          : The path to the file to be highlighted.
        linenos  (bool, optional)  : Whether to show line numbers or not.
        mode     (string, optional): The display mode ('more' | 'less').
                                     If mode is not set, it prints all the
                                     formatted content to the screen.

    Returns:
        Nothing.
    """
    from os import environ
    fname = filepath.split('/')[-1]
    with open(filepath, 'rb') as f:
        src = f.read()
        if src:
            try:
                lexer = guess_lexer(src)
            except pygmentsClassNotFound:
                print 'No lexer found... Print without formatting.'
                print src
            if 'xterm' in environ['TERM']:
                formatter = Terminal256Formatter(linenos=linenos)
            else:
                formatter = TerminalFormatter(linenos=linenos)
            highlighted = hl(src, lexer, formatter)
            if mode:
                if mode == 'more':
                    more(highlighted)
                elif mode == 'less':
                    less(highlighted, filename=fname)
                else:
                    print highlighted
            else:
                print highlighted
