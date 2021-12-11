# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

try:
    from trytond.modules.product_image.tests.test_product_image import \
        suite  # noqa: E501
except ImportError:
    from .test_product_image import suite

__all__ = ['suite']
