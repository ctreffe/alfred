# -*- coding: utf-8 -*-

'''
Das Modul definiert alle Exceptions des Frameworks
'''
from __future__ import absolute_import

import sys
from . import alfredlog
import traceback

from . import settings


logger = alfredlog.getLogger(__name__)

if settings.experiment.type == 'qt':
    def excepthook(type, value, tb):
        s = 'Unhandled exception: %s (%s)\n' % (type, value)
        s = s + 'Traceback:\n' + ''.join(traceback.format_tb(tb))
        # logging.critical(s)
        logger.critical(s)

    sys.excepthook = excepthook


class AlfredError(Exception):
    u'''
    Jede Exception des Frameworks ist von dieser Klasse abgeleitet.
    '''
    pass


class MoveError(AlfredError):
    pass


class SavingAgentRunException(AlfredError):
    pass


class SavingAgentException(AlfredError):
    pass
