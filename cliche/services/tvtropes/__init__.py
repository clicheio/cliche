""":mod:`cliche.services.tvtropes` --- Interfacing TVTropes_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _TVTropes: http://tvtropes.org/

"""

from .crawler import crawl as sync  # noqa


__all__ = 'sync',
