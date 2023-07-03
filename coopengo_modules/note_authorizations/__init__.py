# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from .note import *
from .res import *


def register():
    Pool.register(
        NoteType,
        NoteTypeGroup,
        Note,
        User,
        Group,
        module='note_authorizations', type_='model')
