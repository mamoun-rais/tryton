import gobject
import gtk
import gettext
from interface import WidgetInterface
import tryton.common as common
from tryton.gui.window.view_form.screen import Screen
from tryton.gui.window.win_search import WinSearch
from tryton.rpc import RPCProxy
import tryton.rpc as rpc
from tryton.action import Action
from tryton.config import TRYTON_ICON
from tryton.gui.window.view_form.widget_search.form import _LIMIT

_ = gettext.gettext


class Dialog(object):

    def __init__(self, model, obj_id=None, attrs=None, domain=None,
            context=None, window=None):
        if attrs is None:
            attrs = {}

        self.dia = gtk.Dialog(_('Tryton - Link'), window,
                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT)
        self.window = window
        if ('string' in attrs) and attrs['string']:
            self.dia.set_title(self.dia.get_title() + ' - ' + attrs['string'])
        self.dia.set_property('default-width', 760)
        self.dia.set_property('default-height', 500)
        self.dia.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.dia.set_icon(TRYTON_ICON)

        self.accel_group = gtk.AccelGroup()
        self.dia.add_accel_group(self.accel_group)

        icon_cancel = gtk.STOCK_CLOSE
        if not obj_id:
            icon_cancel = gtk.STOCK_CANCEL
        self.but_cancel = self.dia.add_button(icon_cancel,
                gtk.RESPONSE_CANCEL)
        self.but_cancel.add_accelerator('clicked', self.accel_group,
                gtk.keysyms.Escape, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        self.but_ok = self.dia.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.but_ok.add_accelerator('clicked', self.accel_group,
                gtk.keysyms.Return, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.set_placement(gtk.CORNER_TOP_LEFT)
        scroll.set_shadow_type(gtk.SHADOW_NONE)
        self.dia.vbox.pack_start(scroll, expand=True, fill=True)

        viewport = gtk.Viewport()
        viewport.set_shadow_type(gtk.SHADOW_NONE)
        scroll.add(viewport)

        self.dia.show()
        self.screen = Screen(model, self.dia, domain=domain, context=context,
                view_type=['form'])
        if obj_id:
            self.screen.load([obj_id])
        else:
            self.screen.new()
        viewport.add(self.screen.widget)
        i, j = self.screen.screen_container.size_get()
        viewport.set_size_request(i, j + 30)
        self.dia.show_all()
        self.screen.current_view.set_cursor()
        self.screen.display()

    def run(self):
        while True:
            res = self.dia.run()
            if res == gtk.RESPONSE_OK:
                if self.screen.save_current():
                    return (True, self.screen.current_model.name_get())
                else:
                    self.screen.display()
            else:
                break
        return (False, False)

    def destroy(self):
        self.window.present()
        self.dia.destroy()

class Many2One(WidgetInterface):

    def __init__(self, window, parent, model, attrs=None):
        if attrs is None:
            attrs = {}
        WidgetInterface.__init__(self, window, parent, model, attrs)

        self.widget = gtk.HBox(spacing=3)
        self.widget.set_property('sensitive', True)
        self.widget.connect('focus-in-event', lambda x, y: self._focus_in())
        self.widget.connect('focus-out-event', lambda x, y: self._focus_out())

        self.wid_text = gtk.Entry()
        self.wid_text.set_property('width-chars', 13)
        self.wid_text.set_property('activates_default', True)
        self.wid_text.connect('key_press_event', self.sig_key_press)
        self.wid_text.connect('populate-popup', self._populate_popup)
        self.wid_text.connect_after('changed', self.sig_changed)
        self.changed = True
        self.wid_text.connect_after('activate', self.sig_activate)
        self.wid_text.connect_after('focus-out-event',
                        self.sig_activate)
        self.focus_out = True
        self.widget.pack_start(self.wid_text, expand=True, fill=True)

        self.but_new = gtk.Button()
        img_new = gtk.Image()
        img_new.set_from_stock('gtk-new', gtk.ICON_SIZE_BUTTON)
        self.but_new.set_image(img_new)
        self.but_new.set_relief(gtk.RELIEF_NONE)
        self.but_new.connect('clicked', self.sig_new)
        self.but_new.set_alignment(0.5, 0.5)
        self.but_new.set_property('can-focus', False)
        self.widget.pack_start(self.but_new, expand=False, fill=False)

        self.but_open = gtk.Button()
        img_find = gtk.Image()
        img_find.set_from_stock('gtk-find', gtk.ICON_SIZE_BUTTON)
        img_open = gtk.Image()
        img_open.set_from_stock('gtk-open', gtk.ICON_SIZE_BUTTON)
        self.but_open.set_image(img_find)
        self.but_open.set_relief(gtk.RELIEF_NONE)
        self.but_open.connect('clicked', self.sig_edit)
        self.but_open.set_alignment(0.5, 0.5)
        self.but_open.set_property('can-focus', False)
        self.widget.pack_start(self.but_open, expand=False, fill=False)

        self.tooltips = gtk.Tooltips()
        self.tooltips.set_tip(self.but_new, _('Create a new record'))
        self.tooltips.set_tip(self.but_open, _('Open a record'))
        self.tooltips.enable()

        self._readonly = False
        self.model_type = attrs['relation']

        self.completion = gtk.EntryCompletion()
        self.liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        if attrs.get('completion', False):
            try:
                ids = rpc.execute('object', 'execute',
                        self.attrs['relation'], 'name_search', '', [],
                        'ilike', {})
            except Exception, exception:
                common.process_exception(exception, self._window)
                ids = []
            if ids:
                self.load_completion(ids)

    def grab_focus(self):
        return self.wid_text.grab_focus()

    def _focus_out(self):
        return WidgetInterface._focus_out(self)

    def _focus_in(self):
        return WidgetInterface._focus_in(self)

    def load_completion(self, ids):
        self.completion.set_match_func(self.match_func, None)
        self.completion.connect("match-selected", self.on_completion_match)
        self.wid_text.set_completion(self.completion)
        self.completion.set_model(self.liststore)
        self.completion.set_text_column(0)
        for i, word in enumerate(ids):
            if word[1][0] == '[':
                i = word[1].find(']')
                str1 = word[1][1:i]
                str2 = word[1][i+2:]
                self.liststore.append([("%s %s" % (str1, str2)), str2])
            else:
                self.liststore.append([word[1], word[1]])

    def match_func(self, completion, key_string, iter, data):
        model = self.completion.get_model()
        modelstr = model[iter][0].lower()
        return modelstr.startswith(key_string)

    def on_completion_match(self, completion, model, iter):
        name = model[iter][1]
        domain = self._view.modelfield.domain_get(self._view.model)
        context = self._view.modelfield.context_get(self._view.model)
        try:
            ids = rpc.execute('object', 'execute',
                    self.attrs['relation'], 'name_search', name, domain, 'ilike',
                    context)
        except Exception, exception:
            common.process_exception(exception, self._window)
            return False
        if len(ids)==1:
            self._view.modelfield.set_client(self._view.model, ids[0])
            self.display(self._view.model, self._view.modelfield)
        else:
            win = WinSearch(self.attrs['relation'], sel_multi=False,
                    ids = [x[0] for x in ids], context=context,
                    domain=domain, window=self._window)
            ids = win.go()
            if ids:
                try:
                    name = rpc.execute('object', 'execute',
                            self.attrs['relation'], 'name_get', [ids[0]],
                            rpc.CONTEXT)[0]
                except Exception, exception:
                    common.process_exception(exception, self._window)
                    return False
                self._view.modelfield.set_client(self._view.model, name)
        return True

    def _readonly_set(self, value):
        self._readonly = value
        self.wid_text.set_editable(not value)
        self.but_new.set_sensitive(not value)

    def _color_widget(self):
        return self.wid_text

    def sig_activate(self, widget, event=None):
        if not self.focus_out:
            return
        if not self._view.modelfield:
            return
        self.changed = False
        value = self._view.modelfield.get(self._view.model)

        self.focus_out = False
        if not value:
            if not self._readonly and self.wid_text.get_text():
                domain = self._view.modelfield.domain_get(self._view.model)
                context = self._view.modelfield.context_get(self._view.model)
                self.wid_text.grab_focus()

                try:
                    ids = rpc.execute('object', 'execute',
                            self.attrs['relation'], 'name_search',
                            self.wid_text.get_text(), domain, 'ilike', context,
                            _LIMIT)
                except Exception, exception:
                    self.focus_out = True
                    common.process_exception(exception, self._window)
                    self.changed = True
                    return False
                if len(ids)==1:
                    self._view.modelfield.set_client(self._view.model, ids[0],
                            force_change=True)
                    self.focus_out = True
                    self.display(self._view.model, self._view.modelfield)
                    return True

                win = WinSearch(self.attrs['relation'], sel_multi=False,
                        ids = [x[0] for x in ids], context=context,
                        domain=domain, parent=self._window)
                ids = win.run()
                if ids:
                    try:
                        name = rpc.execute('object', 'execute',
                                self.attrs['relation'], 'name_get', [ids[0]],
                                rpc.CONTEXT)[0]
                    except Exception, exception:
                        self.focus_out = True
                        common.process_exception(exception, self._window)
                        self.changed = True
                        return False
                    self._view.modelfield.set_client(self._view.model, name,
                            force_change=True)
        self.focus_out = True
        self.display(self._view.model, self._view.modelfield)
        self.changed = True

    def sig_new(self, *args):
        self.focus_out = False
        domain = self._view.modelfield.domain_get(self._view.model)
        context = self._view.modelfield.context_get(self._view.model)
        dia = Dialog(self.attrs['relation'], attrs=self.attrs,
                window=self._window, domain=domain, context=context)
        res, value = dia.run()
        if res:
            self._view.modelfield.set_client(self._view.model, value)
            self.display(self._view.model, self._view.modelfield)
        dia.destroy()
        self.focus_out = True

    def sig_edit(self, widget):
        self.changed = False
        value = self._view.modelfield.get(self._view.model)
        self.focus_out = False
        if value:
            domain = self._view.modelfield.domain_get(self._view.model)
            context = self._view.modelfield.context_get(self._view.model)
            dia = Dialog(self.attrs['relation'],
                    self._view.modelfield.get(self._view.model),
                    attrs=self.attrs, window=self._window, domain=domain,
                    context=context)
            res, value = dia.run()
            if res:
                self._view.modelfield.set_client(self._view.model, value,
                        force_change=True)
            dia.destroy()
        else:
            if not self._readonly:
                domain = self._view.modelfield.domain_get(self._view.model)
                context = self._view.modelfield.context_get(self._view.model)
                self.wid_text.grab_focus()

                try:
                    ids = rpc.execute('object', 'execute',
                            self.attrs['relation'], 'name_search',
                            self.wid_text.get_text(), domain, 'ilike', context,
                            _LIMIT)
                except Exception, exception:
                    self.focus_out = True
                    common.process_exception(exception, self._window)
                    self.changed = True
                    return False
                if ids and len(ids)==1:
                    self._view.modelfield.set_client(self._view.model, ids[0],
                            force_change=True)
                    self.focus_out = True
                    self.display(self._view.model, self._view.modelfield)
                    return True

                win = WinSearch(self.attrs['relation'], sel_multi=False,
                        ids = [x[0] for x in (ids or [])], context=context,
                        domain=domain, parent=self._window)
                ids = win.run()
                if ids:
                    try:
                        name = rpc.execute('object', 'execute',
                                self.attrs['relation'], 'name_get', [ids[0]],
                                rpc.CONTEXT)[0]
                    except Exception, exception:
                        self.focus_out = True
                        common.process_exception(exception, self._window)
                        self.changed = True
                        return False
                    self._view.modelfield.set_client(self._view.model, name,
                            force_change=True)
        self.focus_out = True
        self.display(self._view.model, self._view.modelfield)
        self.changed = True

    def sig_key_press(self, widget, event, *args):
        if event.keyval == gtk.keysyms.F3:
            self.sig_new(widget, event)
        elif event.keyval==gtk.keysyms.F2:
            self.sig_edit(widget)
        elif event.keyval  == gtk.keysyms.Tab:
            if self._view.modelfield.get(self._view.model) or \
                    not self.wid_text.get_text():
                return False
            self.sig_activate(widget, event)
            return True
        return False

    def sig_changed(self, *args):
        if not self.changed:
            return False
        if self._view.modelfield.get(self._view.model):
            self._view.modelfield.set_client(self._view.model, False)
            self.display(self._view.model, self._view.modelfield)
        return False

    def set_value(self, model, model_field):
        pass # No update of the model, the model is updated in real time !

    def display(self, model, model_field):
        self.changed = False
        if not model_field:
            self.wid_text.set_text('')
            self.changed = True
            return False
        WidgetInterface.display(self, model, model_field)
        res = model_field.get_client(model)
        self.wid_text.set_text((res and str(res)) or '')
        img = gtk.Image()
        if res:
            img.set_from_stock('gtk-open', gtk.ICON_SIZE_BUTTON)
            self.but_open.set_image(img)
            self.tooltips.set_tip(self.but_open, _('Open a record'))
        else:
            img.set_from_stock('gtk-find', gtk.ICON_SIZE_BUTTON)
            self.but_open.set_image(img)
            self.tooltips.set_tip(self.but_open, _('Search a record'))
        self.changed = True

    def _populate_popup(self, widget, menu):
        value = self._view.modelfield.get(self._view.model)
        ir_action_keyword = RPCProxy('ir.action.keyword')
        relates = ir_action_keyword.get_keyword('form_relate',
                (self.model_type, 0), rpc.CONTEXT)
        menu_entries = []
        menu_entries.append((None, None, None))
        menu_entries.append((_('Actions'),
            lambda x: self.click_and_action('form_action'),0))
        menu_entries.append((_('Reports'),
            lambda x: self.click_and_action('form_print'),0))
        menu_entries.append((None, None, None))
        for relate in relates:
            relate['string'] = relate['name']
            fct = lambda action: lambda x: self.click_and_relate(action)
            menu_entries.append(
                    ('... ' + relate['name'], fct(relate), 0))

        for stock_id, callback, sensitivity in menu_entries:
            if stock_id:
                item = gtk.ImageMenuItem(stock_id)
                if callback:
                    item.connect("activate", callback)
                item.set_sensitive(bool(sensitivity or value))
            else:
                item = gtk.SeparatorMenuItem()
            item.show()
            menu.append(item)
        return True

    def click_and_relate(self, action):
        data = {}
        context = {}
        act = action.copy()
        obj_id = self._view.modelfield.get(self._view.model)
        if not obj_id:
            common.message(_('You must select a record to use the relation !'))
            return False
        screen = Screen(self.attrs['relation'], self._window)
        screen.load([obj_id])
        act['domain'] = screen.current_model.expr_eval(act['domain'],
                check_load=False)
        act['context'] = str(screen.current_model.expr_eval(act['context'],
            check_load=False))
        return Action._exec_action(act, data, context)

    def click_and_action(self, atype):
        obj_id = self._view.modelfield.get(self._view.model)
        return Action.exec_keyword(atype, {'model': self.model_type,
            'id': obj_id or False, 'ids': [obj_id]})
