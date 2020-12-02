"""Provides miscellaneous utilities for alfred experiments.

.. versionadded:: 1.5

.. moduleauthor:: Johannes Brachem <jbrachem@posteo.de>

"""

from emoji import emojize

def icon(name: str, ml: int = 0, mr: int = 0) -> str:
    """Returns HTML code for displaying font-awesome icons.
    
    These icons can be used in all places where HTML code is rendered,
    i.e. TextElements, and all labels of elements.
    
    Args:
        name: The icon name, as shown on https://fontawesome.com/icons?d=gallery&m=free
        ml: Margin to the left, can be an integer from 0 to 5.
        mr: Margin to the right, can be an integer from 0 to 5.

    """
    return f"<i class='fas fa-{name} ml-{ml} mr-{mr}'></i>"


def emoji(text: str) -> str:
    """Returns a new string in which emoji shortcodes in the input 
    string are replaced with their unicode representation.
    
    Emoji printing can be used in all TextElements and Element labels.
    An overview of shortcodes can be found here: 
    https://www.webfx.com/tools/emoji-cheat-sheet/

    Args:
        text: Text, containing emoji shortcodes.
    
    """
    return emojize(text, use_aliases=True)