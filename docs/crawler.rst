How to run crawler
==================

This tutorial covers how to run the cliche crawlers.


Running TVTropes crawler
------------------------

You can run TVTropes crawler using :program:`cliche crawler` command with
:program:`celery worker`:

.. code-block:: console

   $ celery worker -A cliche.services.tvtropes.crawler \
     --config CONFIG_FILENAME_WITHOUT_EXT
   $ cliche crawler

with subcommands you can provide options:

:program:`celery worker`
   It runs celery worker to crawl links. You can supply ``--purge`` option
   for purging pending work queue, and ``-f LOG_FILE`` to save logs into a
   file.

:program:`cliche crawler`
   You have to provide config file with ``-c CONFIG_FILE`` option or
   ``CLICHE_CONFIG`` environmental variable. Config option must be provided
   before ``crawler`` subcommand.

when the crawler is first run, it will fetch and populate the celery queue
with links from `TVTropes Index Report`_. If there is already some crawled
links in the database, the crawler will skip this step and populate the queue
from the database.

.. _TVTropes Index Report: http://tvtropes.org/pmwiki/index_report.php


Running Wikipedia crawler
-------------------------

You can run Wikipedia crawler in the same way using :program:`cliche crawler`
command with :program:`celery worker`:

.. code-block:: console

   $ celery worker -A cliche.services.wikipedia.crawler \
     --config dev.py
   $ cliche sync wikipedia -c CONFIG_FILENAME_WITHOUT_EXT

It also provides same options.
