# -*- coding: utf-8 -*-

"""
Das Modul definiert alle Exceptions des Frameworks
"""

class AlfredError(Exception):
    u"""
    Jede Exception des Frameworks ist von dieser Klasse abgeleitet.
    """
    pass

class ValidationError(AlfredError): pass

class AbortMove(AlfredError): pass

class MoveError(AlfredError):
    pass


class SavingAgentRunException(AlfredError):
    pass


class SavingAgentException(AlfredError):
    pass

class SessionTimeout(AlfredError): 
    pass