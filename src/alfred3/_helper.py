# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

_helper contains internal functions which are not to be called by framework users.

"""

from urllib.parse import urlparse
from cryptography.fernet import Fernet
from dataclasses import dataclass
from typing import Union
import os
import re
import socket
import functools
import inspect

def fontsize_converter(font_argument: Union[int, str]) -> str:
    '''
    FontsizeConverter checks any font arguments used in alfred and 
    returns a fontsize variable compatible with any element or page in 
    alfred.

    '''
    if font_argument is None:
        return None

    elif font_argument == 'normal':
        return "1rem"

    elif font_argument == 'big':
        return "1.5rem"
    
    elif font_argument == "small":
        return "0.75rem"
    
    elif font_argument == "tiny":
        return "0.5rem"

    elif font_argument == 'huge':
        return "2rem"

    elif isinstance(font_argument, int):
        return f"{font_argument}pt"
    
    else:
        return font_argument


def alignment_converter(alignment_argument, type='text'):
    '''
    AlignmentConverter checks any font arguments used in alfred and returns an alignment variable compatible
    for different element types in alfred.

    '''

    if type == 'text':
        if alignment_argument == 'left':
            alignment_argument = 'pagination-left'

        elif alignment_argument == 'center':
            alignment_argument = 'pagination-centered'

        elif alignment_argument == 'right':
            alignment_argument = 'pagination-right'

    elif type == 'container':
        if alignment_argument == 'left':
            alignment_argument = 'containerpagination-left'

        elif alignment_argument == 'center':
            alignment_argument = 'containerpagination-centered'

        elif alignment_argument == 'right':
            alignment_argument = 'containerpagination-right'

    elif type == 'both':
        if alignment_argument == 'left':
            alignment_argument = 'pagination-left containerpagination-left'

        elif alignment_argument == 'center':
            alignment_argument = 'pagination-centered containerpagination-centered'

        elif alignment_argument == 'right':
            alignment_argument = 'pagination-right containerpagination-right'

    elif type == 'div':
        if alignment_argument == 'left':
            alignment_argument = 'text-align:left'

        elif alignment_argument == 'center':
            alignment_argument = 'text-align:center'

        elif alignment_argument == 'right':
            alignment_argument = 'text-align:right'

    return alignment_argument


class Decrypter(object):

    _decrypter = None

    def decrypt_login(self, username=None, password=None, from_env=False):

        if not self._decrypter:
            # Fernet instance for decryption of login data
            if os.path.isfile("alfred_secrect.key"):
                with open("alfred_secrect.key", "rb") as keyfile:
                    key = keyfile.read()
            else:
                key = os.environ.get("ALFRED_SECRET_KEY")
            try:
                self._decrypter = Fernet(key)
            except Exception:
                RuntimeError('Unable to initialize Fernet decrypter: Secret key not found!')

        if from_env:
            try:
                decrypted_username = self._decrypter.decrypt(os.environ.get("ALFRED_MONGODB_USER").encode()).decode()
                decrypted_password = self._decrypter.decrypt(os.environ.get("ALFRED_MONGODB_PASSWORD").encode()).decode()

                return (decrypted_username, decrypted_password)

            except (AttributeError, NameError):
                print("Incomplete DB login data in environment variables. Now trying to decrypt login data from config.conf...")

        decrypted_username = self._decrypter.decrypt(username.encode()).decode()
        decrypted_password = self._decrypter.decrypt(password.encode()).decode()

        return (decrypted_username, decrypted_password)

    
class _DictObj(dict):
    """
    This class allows dot notation to access dict elements

    Example:
    d = _DictObj()
    d.hello = "Hello World"
    print d.hello # Hello World
    """

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def is_url(url=None):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc, result.path])
    except:
        return False


def check_name(name: str):

    if name in ["exp", "experiment"]:
        raise ValueError(f"{name} cannot be chosen as a name.")

    if not re.match(pattern=r"^[a-zA-z](\d|_|[a-zA-Z])*$", string=name):

        raise ValueError(
            (
                "Name must start with a letter and can include only "
                "letters (a-z, A-Z), digits (0-9), and underscores ('_')."
                f"Name '{name}' does not match this pattern."
            )
        )


def socket_checker(port):
    try:
        s = socket.socket()
        s.bind(("127.0.0.1", port))
        s.listen(1)
        s.close()
        return True
    except Exception:
        s.close()
        return False


def sort_dict(d: dict) -> dict:
    """Returns a dict, sorted alphabetically by its keys."""
    return {key: d[key] for key in sorted(d)}


def add_indent(inp: str, spaces: int = 8) -> str:
        """
        Adds indentation to all lines of a single or multiline string.

        Args:
            inp: Input string
            spaces: Number of spaces to indent each line by
        """
        splitted = inp.split("\n")
        indented = f"\n{' '*spaces}".join(splitted)
        return " " * spaces + indented


def build_table(docs: dict, caption: str = "", widths: str = "20, 80") -> str:
        """
        Transforms a documentation dictionary into a string, representing
        the docutils csv-table directive.

        Args:
            docs: Documentation dictionary
            caption: String to use as table caption
            widths: String, indicating the relative widths of the table
                columns in percent.
        """
        directive = f".. csv-table:: {caption}"
        indent = " " * 3

        rows = []
        rows.append(f":widths: {widths}\n")

        for arg, explanation in docs.items():
            rows.append(f"\"{arg}\", \"{explanation}\"")

        built_rows = f"\n{indent}".join(rows)
        return directive + "\n" + indent + built_rows


def build_kwargs(docs: dict, text: str = "Inherited keyword arguments\n", **kwargs) -> str:
        """
        Builds a full keyword-arguments string, ready for use in a class
        docstring.

        Args:
            docs: Documentation dictionary
            text: A short heading for the keyword arguments
            **kwargs: Passed on to :meth:`.build_table`

        """
        heading = f"\*\*kwargs: {text}\n"
        body = build_table(docs=docs, **kwargs)
        body = add_indent(body, spaces=12)
        return heading + body

def extract_arguments(obj) -> dict:
    """
    Extracts function arguments from google style docstrings of the
    input object.

    Returns:
        dict: Dictionary of argument names and their descriptions.
    """
    args = {}
    beginning_found = False
    previous_arg = None
    p = re.compile(r"    (?P<arg>[\w*]+[\w ,]*?) ?(\((?P<type>.+?)?\))?:(?P<description>.*)")

    for line in inspect.getdoc(obj).split("\n"):
        if line in ["Args:", "Arguments:"]:
            beginning_found = True
            continue

        if beginning_found:
            m = p.match(line)
            if m is not None:
                name = m["arg"] if m["type"] is None else f"{m['arg']} ({m['type']})"
                args[name] = [m["description"]]
                previous_arg = name
            elif line.startswith(" "*8):
                args[previous_arg].append(line)
            
            elif beginning_found and line.replace(" ", "") != "":
                break
    
    def clean(lines: list) -> str:
        """
        All occurances of single and double quotes are removed, 
        because otherwise they would mess up the csv table.
            
        """
        joined = " ".join(lines)
        stripped = joined.strip()
        escaped1 = stripped.replace("'", "")
        escaped2 = escaped1.replace('"', '')
        return re.sub(r" +", " ", escaped2)


    return {arg: clean(desc) for arg, desc in args.items()}

def extract_arguments_from_tree(obj) -> dict:
    args = {}
    
    mro = list(inspect.getmro(obj))
    mro.reverse()
    
    for parent in mro:
        parent_args = extract_arguments(parent)
        parent_args.pop("**kwargs", None)
        args.update(parent_args)
    
    return args

def inherit_kwargs(
    _klass=None, *,
    from_: list = None,
    not_from_: list = None,
    include: list = None,
    exclude: list = None,
    sort_kwargs: bool = True,
    build_function: callable = build_kwargs,
    **kwargs,
):
    """
    Decorator for easier docstring sharing, used for displaying
    documentation of inherited keyword arguments.

    Args:
        ``from_`` : List of classes to inherit argument documentation from.
        ``not_from_`` : List of classes *not* to inherit argument 
            documentation from. Useful, if you want to include some
            specific parent or grandparent.
        include: List of keyword argument names to include
        exclude: List of keyword argument names to exclude
        sort_kwargs: If *True*, the keyword arguments will be arranged
            in alphabetical order. Defaults to True.
        build_function: A function that, as a minimmum, takes an argument
            of *docs*, which is the dictionary of arguments and their
            documentation. It must return a string. Its output is 
            inserted in the decorated class' docstring. The kwargs 
            will be passed on to the build_function.
        **kwargs: Further keyword arguments. These will be passed on to
            the *build_function*.
    
    Notes:
        Replaces the placeholder ``{kwargs}`` in the docstring of the 
        decorated object with argument documentation extracted from
        the parent classes.

        Further notes:
        
        1. The decorator can deal with classes that inherit from more 
           than one class.
        
        2. It is possible to use a different formatting by supplying
           a different build function.
        
        3. Arguments that are already part of the decorated class' 
           docstring will be filtered out.
        
        4. By using the *from_* argument, you can inherit from a 
           completely different class that is not part of the decorated
           class' hierarchy.
        
        5. If you are using curly braces (``{{}}``) anywhere in your 
           docstrings, you have to escape them to let *inherit_kwargs* 
           know that they are not a placeholder. Otherwise you will
           receive a somewhat cryptic error message
           ("IndexError: Replacement index 0 out of range for positional 
           args tuple").
    
    Examples:

        A simple example::
            
            from alfred3._helper import inherit_kwargs

            class Parent:
                '''
                Parent docstring.

                Args:
                    arg1: Description
                    arg2: Description
                '''

                def __init__(self, arg1, arg2):
                    pass
            
            
            @inherit_kwargs
            class Child(Parent):
                '''
                Child docstring.
                
                Args:
                    arg3: Description
                    {kwargs}
                '''
                
                def __init__(self, arg3, **kwargs):
                    super().__init__(**kwargs)


    """
    exclude = exclude if exclude is not None else []
    def build_kwargs(klass):
        @functools.wraps(klass)
        def wrapper():

            # collect arguments from parent classes
            inherited_docs = {}
            parents = from_ if from_ is not None else klass.__bases__
            for parent in parents:
                if not_from_ is not None and parent not in not_from_:
                    continue
                inherited_docs.update(extract_arguments_from_tree(parent))

            # remove arguments that are defined in klass directly
            klass_args = extract_arguments(klass)
            inherited_docs = {k: v for k, v in inherited_docs.items() if k not in klass_args}

            # apply inclusion and exclusion
            for arg in list(inherited_docs.keys()):
                if arg in exclude: del inherited_docs[arg]
                elif include is not None and arg not in include: del inherited_docs[arg]

            if sort_kwargs:
                inherited_docs = sort_dict(inherited_docs)
            
            doc_kwargs = build_function(docs=inherited_docs, **kwargs)
            
            # replace docstring
            klass_doc = klass.__doc__.format(kwargs=doc_kwargs)
            klass.__doc__ = klass_doc
            
            return klass

        return wrapper()
    
    if _klass is None:
        return build_kwargs
    else:
        return build_kwargs(_klass)


