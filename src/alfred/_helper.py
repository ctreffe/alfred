# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

_helper contains internal functions which are not to be called by framework users.

"""


def fontsizeConverter(fontArgument):
    '''
    FontsizeConverter checks any font arguments used in alfred and returns a fontsize variable compatible
    with any element or question in alfred.

    '''

    if fontArgument == 'normal':
        fontArgument = 12

    if fontArgument == 'big':
        fontArgument = 16

    if fontArgument == 'huge':
        fontArgument = 22

    if not isinstance(fontArgument, int):
        fontArgument = 12

    return fontArgument


def alignmentConverter(alignmentArgument, type='text'):
    '''
    AlignmentConverter checks any font arguments used in alfred and returns an alignment variable compatible
    for different element types in alfred.

    '''

    if type == 'text':
        if alignmentArgument == 'left':
            alignmentArgument = 'pagination-left'

        elif alignmentArgument == 'center':
            alignmentArgument = 'pagination-centered'

        elif alignmentArgument == 'right':
            alignmentArgument = 'pagination-right'

    elif type == 'container':
        if alignmentArgument == 'left':
            alignmentArgument = 'containerpagination-left'

        elif alignmentArgument == 'center':
            alignmentArgument = 'containerpagination-centered'

        elif alignmentArgument == 'right':
            alignmentArgument = 'containerpagination-right'

    elif type == 'both':
        if alignmentArgument == 'left':
            alignmentArgument = 'pagination-left containerpagination-left'

        elif alignmentArgument == 'center':
            alignmentArgument = 'pagination-centered containerpagination-centered'

        elif alignmentArgument == 'right':
            alignmentArgument = 'pagination-right containerpagination-right'

    return alignmentArgument
