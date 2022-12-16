# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta

__all__ = ['PaymentTerm', 'PaymentTermLine']


class PaymentTerm:
    __metaclass__ = PoolMeta
    __name__ = 'account.invoice.payment_term'
    _history = True


class PaymentTermLine:
    __metaclass__ = PoolMeta
    __name__ = 'account.invoice.payment_term.line'
    _history = True
