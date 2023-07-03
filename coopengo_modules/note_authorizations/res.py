# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import fields


__all__ = [
    'Group',
    'User',
    ]


class Group(metaclass=PoolMeta):
    __name__ = 'res.group'

    note_types = fields.Many2Many('ir.note.type-res.group', 'group', 'type_',
        'Note Types')


class User(metaclass=PoolMeta):
    __name__ = 'res.user'

    note_types = fields.Function(
        fields.Many2Many('ir.note.type', None, None, 'Note Types'),
        'on_change_with_note_types')

    @fields.depends('groups')
    def on_change_with_note_types(self, name=None):
        return list({x.id for group in self.groups for x in group.note_types})
