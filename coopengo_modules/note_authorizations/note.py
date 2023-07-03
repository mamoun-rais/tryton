# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from collections import defaultdict

from trytond.pyson import Bool, Eval
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.model import fields, ModelSQL, ModelView

__all__ = [
    'NoteType',
    'NoteTypeGroup',
    'Note',
    ]


class NoteType(ModelSQL, ModelView):
    'Note Type'

    __name__ = 'ir.note.type'

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', required=True)
    groups = fields.Many2Many('ir.note.type-res.group', 'type_', 'group',
        'Groups')

    @classmethod
    def search(cls, domain, *args, **kwargs):
        # Filter out everything the user is not allowed to view
        user = Pool().get('res.user')(Transaction().user)
        if Transaction().user != 0:
            domain = ['AND', domain,
                ['OR',
                    ('groups', 'in', [x.id for x in user.groups]),
                    ('groups', '=', None)]]
        res = super(NoteType, cls).search(domain, *args, **kwargs)
        if Transaction().user == 0:
            return res
        return [r for r in res if not r.groups or
            all(x in user.groups for x in r.groups)]


class NoteTypeGroup(ModelSQL):
    'Note Type Group relation'

    __name__ = 'ir.note.type-res.group'

    type_ = fields.Many2One('ir.note.type', 'Type', ondelete='CASCADE',
        required=True, select=True)
    group = fields.Many2One('res.group', 'Group', ondelete='CASCADE',
        required=True, select=True)

    @classmethod
    def delete(cls, records):
        Rule = Pool().get('ir.rule')
        super(NoteTypeGroup, cls).delete(records)
        # Restart the cache on the domain_get method of ir.rule
        Rule._domain_get_cache.clear()

    @classmethod
    def create(cls, vlist):
        Rule = Pool().get('ir.rule')
        res = super(NoteTypeGroup, cls).create(vlist)
        # Restart the cache on the domain_get method of ir.rule
        Rule._domain_get_cache.clear()
        return res

    @classmethod
    def write(cls, records, values, *args):
        Rule = Pool().get('ir.rule')
        super(NoteTypeGroup, cls).write(records, values, *args)
        # Restart the cache on the domain_get method
        Rule._domain_get_cache.clear()


class Note(metaclass=PoolMeta):
    __name__ = 'ir.note'

    type_ = fields.Selection('get_type_code', 'Type',
        states={'readonly':
            Bool(Eval('type_') & Bool(Eval('id', 0) > 0))},)
    groups = fields.Function(
        fields.Many2Many('res.group', None, None, 'User Groups'),
        'get_groups', searcher='search_groups')

    @classmethod
    def search(cls, domain, *args, **kwargs):
        # Never search any note for which the user is not allowed to view the
        # type
        types = Pool().get('ir.note.type').search([])
        domain = ['AND', domain,
            [('type_', 'in', list({x.code for x in types}) + ['', None])]]
        return super(Note, cls).search(domain, *args, **kwargs)

    @classmethod
    def default_groups(cls):
        user = Pool().get('res.user')(Transaction().user)
        return [x.id for x in user.groups]

    @classmethod
    def get_type_code(cls):
        pool = Pool()
        NoteType = pool.get('ir.note.type')
        note_types = NoteType.search([])
        return [(x.code, x.name) for x in note_types] + [('', '')]

    @classmethod
    def get_groups(cls, notes, name):
        pool = Pool()
        NoteType = pool.get('ir.note.type')
        Group = pool.get('res.group')
        code2note = defaultdict(list)
        for note in notes:
            code2note[note.type_].append(note.id)

        note_types = NoteType.search([
                ('code', 'in', list(code2note.keys())),
                ])

        groups = defaultdict(list)
        for note_type in note_types:
            for note_id in code2note[note_type.code]:
                groups[note_id] += [x.id for x in note_type.groups]

        if None in code2note:
            all_groups = Group.search([])
            for note_id in code2note[None]:
                groups[note_id] = [x.id for x in all_groups]

        return groups

    @staticmethod
    def search_groups(name, clause):
        NoteType = Pool().get('ir.note.type')
        note_types = NoteType.search([clause], order=[])
        codes = {note_type.code for note_type in note_types}
        return [('type_', 'in', list(codes))]
