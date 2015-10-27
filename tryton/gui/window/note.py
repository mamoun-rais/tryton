# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from tryton.gui.window.view_form.screen import Screen
from tryton.gui.window.win_form import WinForm


class Note(WinForm):
    "Note window"

    def __init__(self, record, callback=None):
        self.resource = '%s,%s' % (record.model_name, record.id)
        self.note_callback = callback
        context = record.context_get()
        context['resource'] = self.resource
        try:
            screen = Screen('ir.note', domain=[
                    ('resource', '=', self.resource),
                    ], mode=['tree', 'form'], context=context,
                exclude_field='resource')
        except:
            return
        super(Note, self).__init__(screen, self.callback, view_type='tree')
        screen.search_filter()
        # Set parent after to be allowed to call search_filter
        screen.parent = record

    def destroy(self):
        self.prev_view.save_width_height()
        super(Note, self).destroy()

    def callback(self, result):
        if result:
            resource = self.screen.group.fields['resource']
            unread = self.screen.group.fields['unread']
            for record in self.screen.group:
                resource.set_client(record, self.resource)
                unread.set_client(record, False)
            self.screen.group.save()
        if self.note_callback:
            self.note_callback()
