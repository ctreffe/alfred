# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

_helper contains internal functions which are not to be called by framework users.

"""

from urllib.parse import urlparse
from cryptography.fernet import Fernet
import os
import re
import socket

def fontsize_converter(font_argument) -> int:
    '''
    FontsizeConverter checks any font arguments used in alfred and 
    returns a fontsize variable compatible with any element or page in 
    alfred.

    '''
    if font_argument is None:
        return None

    if font_argument == 'normal':
        font_argument = 12

    if font_argument == 'big':
        font_argument = 16

    if font_argument == 'huge':
        font_argument = 22

    if not isinstance(font_argument, int):
        font_argument = 12

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


def check_name(name):
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