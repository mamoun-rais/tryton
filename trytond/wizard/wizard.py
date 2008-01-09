"Wizard"
from trytond.netsvc import Service, service_exist, Logger, LOG_ERROR
from trytond import pooler
import copy
from xml import dom
from trytond.osv import ExceptORM, ExceptOSV, OSV
import sys

MODULE_LIST = []
MODULE_CLASS_LIST = {}
CLASS_POOL = {}


class ExceptWizard(Exception):
    def __init__(self, name, value):
        Exception.__init__(self)
        self.name = name
        self.value = value
        self.args = (name, value)

except_wizard = ExceptWizard

class WizardService(Service):

    def __init__(self):
        self.object_name_pool = {}
        self.module_obj_list = {}
        Service.__init__(self, 'wizard_proxy')
        Service.join_group(self, 'web-services')
        Service.export_method(self, self.execute)

    def execute_cr(self, cursor, user, wizard_name, data, state='init',
            context=None):
        try:
            wizard = pooler.get_pool_wizard(cursor.dbname).get(wizard_name)
            if not wizard:
                self.abort_response('Wizard Error', 'warning',
                        'Wizard %s doesn\'t exist' % str(wizard_name))
            res = wizard.execute(cursor, user, data, state, context)
            return res
        except ExceptORM, inst:
            self.abort_response(inst.name, 'warning', inst.value)
        except ExceptOSV, inst:
            self.abort_response(inst.name, inst.exc_type, inst.value)
        except ExceptWizard, inst:
            self.abort_response(inst.name, 'warning', inst.value)
        except:
            import traceback
            tb_s = reduce(lambda x, y: x+y, traceback.format_exception(
                sys.exc_type, sys.exc_value, sys.exc_traceback))
            Logger().notify_channel("web-services", LOG_ERROR,
                    'Exception in call: ' + tb_s)
            raise

    def execute(self, dbname, user, wizard_name, data, state='init',
            context=None):
        cursor = pooler.get_db(dbname).cursor()
        pool = pooler.get_pool_wizard(dbname)
        try:
            try:
                res = pool.execute_cr(cursor, user, wizard_name, data, state,
                        context)
                cursor.commit()
            except Exception:
                cursor.rollback()
                raise
        finally:
            cursor.close()
        return res

    def add(self, name, object_name_inst):
        """
        adds a new obj instance to the obj pool.
        if it already existed, the instance is replaced
        """
        if self.object_name_pool.has_key(name):
            del self.object_name_pool[name]
        self.object_name_pool[name] = object_name_inst

        module = str(object_name_inst.__class__)[6:]
        module = module[:len(module)-1]
        module = module.split('.')[0][2:]
        self.module_obj_list.setdefault(module, []).append(object_name_inst)

    def get(self, name):
        return self.object_name_pool.get(name, None)

    def instanciate(self, module, pool_obj):
        res = []
        class_list = MODULE_CLASS_LIST.get(module, [])
        for klass in class_list:
            res.append(klass.create_instance(self, module, pool_obj))
        return res


class Wizard(object):
    _name = ""
    states = {}

    def __new__(cls):
        for module in cls.__module__.split('.'):
            if module != 'trytond' and module != 'addons':
                break
        if not hasattr(cls, '_module'):
            cls._module = module
        MODULE_CLASS_LIST.setdefault(cls._module, []).append(cls)
        CLASS_POOL[cls._name] = cls
        if module not in MODULE_LIST:
            MODULE_LIST.append(cls._module)
        return None

    def create_instance(cls, pool, module, pool_obj):
        """
        try to apply inheritancy at the instanciation level and
        put objs in the pool var
        """
        if pool.get(cls._name):
            parent_class = pool.get(cls._name).__class__
            cls = type(cls._name, (cls, parent_class), {})

        obj = object.__new__(cls)
        obj.__init__(pool, pool_obj)
        return obj

    create_instance = classmethod(create_instance)

    def __init__(self, pool, pool_obj):
        pool.add(self._name, self)
        self.pool = pool_obj
        super(Wizard, self).__init__()

    def execute(self, cursor, user, data, state='init', context=None):
        if context is None:
            context = {}
        res = {}
        translation_obj = self.pool.get('ir.translation')

        state_def = self.states[state]
        result_def = state_def.get('result', {})

        actions_res = {}
        # iterate through the list of actions defined for this state
        for action in state_def.get('actions', []):
            # execute them
            action_res = action(self, cursor, user, data, context)
            assert isinstance(action_res, dict), \
                    'The return value of wizard actions ' \
                    'should be a dictionary'
            actions_res.update(action_res)

        res = copy.copy(result_def)
        res['datas'] = actions_res

        lang = context.get('lang', 'en_US')
        if result_def['type'] == 'action':
            res['action'] = result_def['action'](self, cursor, user, data,
                    context)
        elif result_def['type'] == 'form':
            obj = self.pool.get(result_def['object'])

            view = obj.fields_view_get(cursor, user, view_type='form',
                    context=context, toolbar=False)
            fields = view['fields']
            arch = view['arch']

            button_list = copy.copy(result_def['state'])

            default_values = obj.default_get(cursor, user, fields.keys(),
                    context=None)
            for field in default_values.keys():
                fields[field]['value'] = default_values[field]

            # translate buttons
            for i, button  in enumerate(button_list):
                button_name = button[0]
                res_trans = translation_obj._get_source(cursor, user,
                        self._name + ',' + state + ',' + button_name,
                        'wizard_button', lang)
                if res_trans:
                    button = list(button)
                    button[1] = res_trans
                    button_list[i] = tuple(button)

            res['fields'] = fields
            res['arch'] = arch
            res['state'] = button_list
        if result_def['type'] == 'choice':
            next_state = result_def['next_state'](self, cursor, user,
                    data, context)
            return self.execute(cursor, user, data, next_state, context)
        return res

class WizardOSV(OSV):
    """
    Object to use for wizard state
    """
    _protected = [
            'default_get',
            'fields_get',
            'fields_view_get',
            ]
    _auto = False

    def auto_init(self, cursor):
        pass

    def init(self, cursor):
        pass

    def browse(self, cursor, user, select, context=None, list_class=None):
        pass

    def export_data(self, cursor, user, ids, fields_name, context=None):
        pass

    def import_data(self, cursor, fields_names, datas, mode='init',
            current_module=None, noupdate=False, context=None):
        pass

    def read(self, cursor, ids, fields_names=None, context=None,
            load='_classic_read'):
        pass

    def unlink(self, cursor, user, ids, context=None):
        pass

    def write(self, cursor, user, ids, vals, context=None):
        pass

    def create(self, cursor, user, vals, context=None):
        pass

    def search_count(self, cursor, user, args, context=None):
        pass

    def search(self, cursor, user, args, offset=0, limit=None, order=None,
            context=None, count=False):
        pass

    def name_get(self, cursor, user, ids, context=None):
        pass

    def name_search(self, cursor, user, name='', args=None, operator='ilike',
            context=None, limit=80):
        pass

    def copy(self, cursor, user, object_id, default=None, context=None):
        pass
