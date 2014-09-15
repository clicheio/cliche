How to run loader
==================

This tutorial covers how to run the wikipedia loaders.


Running Wikipedia loader
------------------------

You can run Wikipedia loader using :program:`cliche loader` command with
:program:`celery worker`:

.. code-block:: console

   $ celery worker -A cliche.services.wikipedia.loader \
     --config CONFIG_FILENAME_WITHOUT_EXT
   $ cliche -c CONFIG_FILENAME load

``CONFIG_FILENAME_WITHOUT_EXT`` is ``dev`` in cliche.
with subcommands you can provide options:

:program:`celery worker`
   It runs celery worker to load datas. You can supply ``--purge`` option
   for purging pending work queue, and ``-f LOG_FILE`` to save logs into a
   file.

:program:`cliche loader`
   You have to provide config file with ``-c CONFIG_FILE`` option or
   ``CLICHE_CONFIG`` environmental variable. Config option must be provided
   before ``loader`` subcommand.

when the loader is first run, it will fetch and populate the celery queue
with datas from `DBpedia`_.

.. _DBpedia: http://dbpedia.org/sparql