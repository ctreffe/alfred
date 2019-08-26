# -*- coding:utf-8 -*-

from builtins import object
import logging
import sys
import os


def init_logging(name='alfred'):
    from . import settings
    logger = logging.getLogger(name)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # configure handlers
    if settings.log.syslog:
        raise ValueError("syslog logger not implemented. please set syslog = false")

    if settings.log.stderrlog:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if settings.log.path:
        path = os.path.abspath(settings.log.path)
        if not os.path.exists(path):
            os.makedirs(path)
        if not os.path.isdir(path):
            raise RuntimeError("log.path '%s' must be an directory" % path)
        if not os.access(path, os.W_OK):
            raise RuntimeError("log.path '%s' must be writable" % path)
        logname = 'alfred_debug.log' if settings.debugmode else 'alfred.log'
        path = os.path.join(path, logname)
        if os.path.exists(path):
            if not os.access(path, os.W_OK) or not os.access(path, os.R_OK):
                raise RuntimeError("'%s' must be readable and writable" % path)
        handler = logging.FileHandler(path)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # set log level
    if settings.log.level == 'debug':
        logger.setLevel(logging.DEBUG)
    elif settings.log.level == 'info':
        logger.setLevel(logging.INFO)
    elif settings.log.level == 'warning':
        logger.setLevel(logging.WARNING)
    elif settings.log.level == 'error':
        logger.setLevel(logging.ERROR)
    elif settings.log.level == 'critical':
        logger.setLevel(logging.CRITICAL)
    else:
        raise ValueError("log level must be debug, info, warning, error or critical")

    if settings.experiment.type == 'web':
        alfred_init('web')
    elif settings.experiment.type == 'qt':
        alfred_init('qt')


def getLogger(module_name=None):
    return NewLogger(module_name)


def alfred_init(exp_type):
    logger = getLogger(__name__)

    if exp_type == 'web':
        logger.info("Alfred framework web startup! Logging system initialized.")
    elif exp_type == 'qt':
        logger.info("##################################### Starting new alfred qt experiment session #####################################")


class NewLogger(object):
    def __init__(self, module_name=None):
        self.logger = logging.getLogger(module_name)

    def debug(self, msg, experiment=None, *args, **kwargs):
        if experiment:
            try:
                msg = 'session id={session}'.format(session=experiment.session_id[:6]) + ' - ' + msg
            except Exception:
                pass
        return self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, experiment=None, *args, **kwargs):
        if experiment:
            try:
                msg = 'session id={session}'.format(session=experiment.session_id[:6]) + ' - ' + msg
            except Exception:
                pass
        return self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, experiment=None, *args, **kwargs):
        if experiment:
            try:
                msg = 'session id={session}'.format(session=experiment.session_id[:6]) + ' - ' + msg
            except Exception:
                pass
        return self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, experiment=None, *args, **kwargs):
        if experiment:
            try:
                msg = 'session id={session}'.format(session=experiment.session_id[:6]) + ' - ' + msg
            except Exception:
                pass
        return self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, experiment=None, *args, **kwargs):
        if experiment:
            try:
                msg = 'session id={session}'.format(session=experiment.session_id[:6]) + ' - ' + msg
            except Exception:
                pass
        return self.logger.critical(msg, *args, **kwargs)

    def log(self, lvl, msg, experiment=None, *args, **kwargs):
        if experiment:
            try:
                msg = 'session id={session}'.format(session=experiment.session_id[:6]) + ' - ' + msg
            except Exception:
                pass
        return self.logger.log(lvl, msg, *args, **kwargs)

    def exception(self, msg, experiment=None, *args):
        if experiment:
            try:
                msg = 'session id={session}'.format(session=experiment.session_id[:6]) + ' - ' + msg
            except Exception:
                pass
        return self.logger.exception(msg, *args)
