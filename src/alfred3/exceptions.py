# -*- coding: utf-8 -*-

"""
Das Modul definiert alle Exceptions des Frameworks
"""

class AlfredError(Exception):
    u"""
    Jede Exception des Frameworks ist von dieser Klasse abgeleitet.
    """
    pass


class MoveError(AlfredError):
    pass


class SavingAgentRunException(AlfredError):
    pass


class SavingAgentException(AlfredError):
    pass
