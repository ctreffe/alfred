# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

_helper contains internal functions which are not to be called by framework users.

"""


def fontsize_converter(font_argument):
    '''
    FontsizeConverter checks any font arguments used in alfred and returns a fontsize variable compatible
    with any element or question in alfred.

    '''

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

    return alignment_argument
