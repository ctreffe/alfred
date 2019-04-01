from builtins import object
import threading


class MessageManager(object):

    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    SUCCESS = 'success'

    def __init__(self):
        self._queue = []
        self._lock = threading.Lock()

    def post_message(self, msg, title='', level=INFO):
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
        return self._msg

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level):
        self._level = level

    @property
    def title(self):
        return self._title

    def __unicode__(self):
        return self.msg
