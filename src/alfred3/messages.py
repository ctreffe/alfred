from builtins import object
import threading
import cmarkgfm
from emoji import emojize


class MessageManager(object):

    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    SUCCESS = 'success'

    def __init__(self):
        self._queue = []
        self._lock = threading.Lock()

    def post_message(self, msg: str, title: str = '', level: str = INFO):
        self._lock.acquire()
        self._queue.append(Message(msg, title, level))
        self._lock.release()

    def get_messages(self):
        self._lock.acquire()
        q = self._queue
        self._queue = []
        self._lock.release()
        return q


class Message(object):
    def __init__(self, msg, title='', level=''):
        self._msg = msg
        self._title = title
        self._level = level

    @property
    def msg(self):
        text = emojize(self._msg)
        return cmarkgfm.github_flavored_markdown_to_html(text) 

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level):
        self._level = level

    @property
    def title(self):
        text = emojize(self._title)
        return cmarkgfm.github_flavored_markdown_to_html(text) 

    def __unicode__(self):
        return self.msg
