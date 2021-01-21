"""
Provides miscellaneous utilities for alfred experiments.

.. versionadded:: 1.5

.. moduleauthor:: Johannes Brachem <jbrachem@posteo.de>

"""

import csv
import random
from pathlib import Path

from emoji import emojize
from typing import Any
from typing import Union
from typing import Iterator
from .page import Page
from .section import Section
from .element.core import Element
from .element.core import InputElement
from .element.display import Label

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

def is_section(obj: Any) -> bool: return isinstance(obj, Section)

def is_page(obj: Any) -> bool: return isinstance(obj, Page)

def is_element(obj: Any) -> bool: return isinstance(obj, Element)

def is_input_element(obj: Any) -> bool: return isinstance(obj, InputElement)

def is_label(obj: Any) -> bool: return isinstance(obj, Label)

def read_csv_todict(path: Union[str, Path], encoding: str = "utf-8", **kwargs) -> Iterator[dict]:
    with open(path, "r", encoding=encoding) as csvfile:
        reader = csv.DictReader(csvfile, **kwargs)
        for row in reader:
            yield row

def read_csv_tolist(path: Union[str, Path], encoding: str = "utf-8", **kwargs) -> Iterator[list]:
    with open(path, "r", encoding=encoding) as csvfile:
        reader = csv.reader(csvfile, **kwargs)
        for row in reader:
            yield row    

def random_condition(*conditions) -> str:
    """
    Returns a random condition based on the supplied arguments with 
    equal probability of all conditions.

    Args:
        *conditions: A variable number of condition identifiers
    
    Returns:
        str: One of the input arguments, chosen at random.
    
    Examples:
        
            >>> import alfred3 as al
            >>> al.random_condition("A", "B")

        The example returns either "A" or "B".
    """
    return str(random.choice(conditions))