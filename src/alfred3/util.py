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

def icon(name: str, ml: int = 0, mr: int = 0, size: str = "1rem", spin: bool = False) -> str:
    """Returns HTML code for displaying font-awesome icons.
    
    These icons can be used in all places where HTML code is rendered,
    i.e. TextElements, and all labels of elements.
    
    Args:
        name: The icon name, as shown on https://fontawesome.com/icons?d=gallery&m=free
        ml: Margin to the left, can be an integer from 0 to 5.
        mr: Margin to the right, can be an integer from 0 to 5.

    """
    spin = "fa-spin" if spin else ""
    return f"<i class='fas fa-{name} {spin} ml-{ml} mr-{mr}' style='font-size: {size};'></i>"


def emoji(text: str, size: str = "1rem") -> str:
    """Returns a new string in which emoji shortcodes in the input 
    string are replaced with their unicode representation.
    
    Emoji printing can be used in all TextElements and Element labels.
    An overview of shortcodes can be found here: 
    https://www.webfx.com/tools/emoji-cheat-sheet/

    Args:
        text: Text, containing emoji shortcodes.
    
    """
    return f"<span style='font-size: {size};'>{emojize(text, use_aliases=True)}</span>"

def is_section(obj: Any) -> bool: 
    """
    Returns True, if the given object is a :class:`.Section`, or a
    subclass of Section.
    """
    return isinstance(obj, Section)

def is_page(obj: Any) -> bool: 
    """
    Returns True, if the given object is a :class:`.Page`, or a
    subclass of Page.
    """
    return isinstance(obj, Page)

def is_element(obj: Any) -> bool: 
    """
    Returns True, if the given object is an :class:`.Element`, or a
    subclass of Element.
    """
    return isinstance(obj, Element)

def is_input_element(obj: Any) -> bool:
    """
    Returns True, if the given object is an :class:`.InputElement`, or a
    subclass of InputElement.
    """
    return isinstance(obj, InputElement)

def is_label(obj: Any) -> bool: 
    """
    Returns True, if the given object is an :class:`.Label`, or a
    subclass of Label.
    """
    return isinstance(obj, Label)

def _read_csv_todict(path: Union[str, Path], encoding: str = "utf-8", **kwargs) -> Iterator[dict]:
    with open(path, "r", encoding=encoding) as csvfile:
        reader = csv.DictReader(csvfile, **kwargs)
        for row in reader:
            yield row

def _read_csv_tolist(path: Union[str, Path], encoding: str = "utf-8", **kwargs) -> Iterator[list]:
    with open(path, "r", encoding=encoding) as csvfile:
        reader = csv.reader(csvfile, **kwargs)
        for row in reader:
            yield row    


def prefix_keys(d: dict, prefix: str, sep: str = "_") -> dict:
    """
    dict: Returns the input dictionary with prefixed keys.

    Examples:
        >>> a = {"k": "val"}
        >>> prefix_keys(d=a, prefix="demo")
        {"demo_k": "val"}
    """
    keys = [prefix + sep + str(k) for k in d.keys()]
    return {key: val for key, val in zip(keys, d.values())}

def flatten_dict(d: dict, prefix_sep: str = "_", sequences_to_dict: bool = True) -> dict:
    """
    dict: Turns a nested dictionary into a flat one. 
    
    Keys of subdictionaries are concatenated, e.g. ``{"k1": {"s1": "value"}}``
    would result in ``{"k1_s1": "value"}``. The sperator can be defined
    in the argument *prefix_sep*.

    If *sequences_to_dict* is true, values that are iterable sequences
    like lists, tuples or generators (but not strings), will be turned 
    into dictionaries and identified with unique keys aswell. In this 
    case, the resulting output will be a dictionary where each entry is 
    a pair of a single key with a single value.
    """
    out = {}
    for key, val in d.items():
        
        if isinstance(val, dict):
            renamed = prefix_keys(d=val, prefix=key, sep=prefix_sep)
            flattened = flatten_dict(renamed)
            
            if any([k in out for k in flattened.keys()]):
                raise ValueError
            
            out.update(flattened)
        elif isinstance(val, str):
            out[key] = val
        elif sequences_to_dict:
            try:
                dictified_iterable = to_dict(val, prefix=key, sep=prefix_sep)
                if any([k in out for k in dictified_iterable.keys()]):
                    raise ValueError
                out.update(dictified_iterable)
            except TypeError:
                out[key] = val
        else:
            out[key] = val

    return out

def to_dict(data, prefix: str = "", sep: str = "_") -> dict:
    """
    dict: Turns an iterable into a flat dictionary. 
    
    The keys are procuded by counting through the elements of the iterable
    and concatenating them with the *prefix* and *sep*: 
    ``key = prefix + sep + str(i)``, where ``i`` is the count.
    """
    out = {}
    
    for i, val in enumerate(data, 1):
        name = prefix + sep + str(i)

        if isinstance(val, str):
            out[name] = val
        elif isinstance(val, dict):
            renamed = prefix_keys(d=val, prefix=name)
            out.update(flatten_dict(renamed, prefix_sep=sep))
        else:
            try:
                subsequence_dict = to_dict(data=val, prefix=name, sep=sep)
                out.update(subsequence_dict)
            except TypeError:
                out[name] = val

    return out

def prefix_keys_safely(data: dict, base: dict, prefix: str ="", sep: str = "_") -> dict:
    """
    Takes the *data* dict and prefixes its keys in a way that makes sure
    that there are no keys that are present in both the resulting prefixed
    dictionary and the *base* dictionary.

    If the planned prefixing of any key in *data* would result in a 
    conflict with a key in *base*, the separator *sep* will be continually
    repeated until there is no conflict anymore.
    
    For example, a single underscore would be turned into a double 
    underscore on first try. Then into a triple underscore, and so on.

    This can be useful, if you want to update the *base* dictionary with
    the *data* dictionary without the danger of losing data.

    Returns:
        dict: A version of the *data* dictionary, in which all keys received
        the prefix in a way that does not cause conflicts with the *base*
        dictionary.
    
    Notes:
        Actually, prefixes of the output dictionary are checked very 
        conservatively, which makes the process more safe and more efficient. The
        function does not check every single key of the output dictionary,
        but it checks if any key in the *base* dictionary has the same
        prefix. If so, this counts as a key collision and the separator
        will be repeated.

    Examples:
        
        In this example, prefixing works without any conflict resolution
        being necessary:

        >>> a = {"k": "val1"}
        >>> b = {"k": "val2"}
        >>> prefixed = prefix_keys_safely(data=b, base=a, prefix="demo")
        >>> prefixed
        {"demo_k": "val2"}

        >>> a.update(prefixed)
        >>> a
        {"k": "val1", "demo_k": "val2"}

        Second example, demonstrating how conflicts are resolved:
        
        >>> a = {"demo_k": "val1"}
        >>> b = {"k": "val2"}
        >>> prefixed = prefix_keys_safely(data=b, base=a, prefix="demo")
        >>> prefixed
        {"demo__k": "val2"}

        >>> a.update(prefixed)
        >>> a
        {"demo_k": "val1", "demo__k": "val2"}

        Third example, demonstrating how convervative the approach is.
        Even though there is no direct collision, the prefix collides
        with the start of a key in ``a``, which causes the function
        to repeat the separator:

        >>> a = {"demo_key1": "val1"}
        >>> b = {"k": "val2"}
        >>> prefixed = prefix_keys_safely(data=b, base=a, prefix="demo")
        >>> prefixed
        {"demo__k": "val2"}

        >>> a.update(prefixed)
        >>> a
        {"demo_key1": "val1", "demo__k": "val2"}
    """
    if not sep:
        raise ValueError("Separator must not be empty.")
    
    while any([str(k).startswith(prefix) for k in base.keys()]):
        prefix += sep
    
    return prefix_keys(d=data, prefix=prefix, sep=sep)
