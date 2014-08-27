How to contribute
=================

How to setup commit hook
------------------------

.. code-block:: console

   $ mkdir -p .git/hooks/
   $ ln -s `pwd`/hooks/pre-commit .git/hooks/


How to download dependencies
----------------------------

.. code-block:: console

   $ pip install -e .


The Perils of Rebasing
----------------------

Do not rebase commits that you have pushed to a public repository.

Refer http://git-scm.com/book/en/Git-Branching-Rebasing#The-Perils-of-Rebasing

Use

.. code-block:: console

   $ git pull --rebase
