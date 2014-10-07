""":mod:`cliche.services.wikipedia` --- Crawl data from Wikipedia_ via DBpedia
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _Wikipedia: http://wikipedia.org/

"""

from .crawler import crawl as sync  # noqa


__all__ = 'sync',
