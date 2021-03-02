from builtins import object
import threading
import cmarkgfm
import queue
from emoji import emojize
from cmarkgfm.cmark import Options as cmarkgfmOptions

class MessageManager:
    """
    Args:
        default_level: Sets the default message level for this message
            manager. Levels can be 'debug', 'info', 'warning', 'error',
            'success', 'primary', 'secondary', 'dark', and 'light'.
    """

    def __init__(self, default_level: str = "info"):
        self._default_level = default_level
        self._queue = queue.Queue()
        self._lock = threading.Lock()

    def post_message(self, msg: str, title: str = '', level: str = None):
        if level is None:
            level = self._default_level
        msg = Message(msg, title, level)
        self._queue.put(msg)

    def get_messages(self):
        while True:
            try:
                yield self._queue.get_nowait()
            except queue.Empty:
                break


class Message(object):
    def __init__(self, msg, title='', level=''):
        self._msg = msg
        self._title = title
        self._level = level

    @property
    def msg(self):
        text = emojize(self._msg)
        return cmarkgfm.github_flavored_markdown_to_html(text, options=cmarkgfmOptions.CMARK_OPT_UNSAFE) 

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level):
        self._level = level

    @property
    def title(self):
        text = emojize(self._title)
        return cmarkgfm.github_flavored_markdown_to_html(text, options=cmarkgfmOptions.CMARK_OPT_UNSAFE) 

    def __unicode__(self):
        return self.msg
