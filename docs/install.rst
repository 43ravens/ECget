************
Installation
************

Python Versions
===============

ECget is being developed under Python 3.4 and is tested with Python 2.7.


Source Code
===========

The source code is hosted on Bitbucket: https://bitbucket.org/douglatornell/ecget


Reporting Bugs
==============

Please report bugs through the Bitbucket project: https://bitbucket.org/douglatornell/ecget/issues


Installation
============

The steps to install ECget are:

#. Use Mercurial to clone the project repo from Bitbucket;
   i.e.

   .. code-block:: bash

       $ hg clone https://bitbucket.org/douglatornell/ecget

#. Install the Python packages that ECget depends on.
#. Install ECget iteself.

Several ways of accomplishing the above steps are described below.
Please choose the one that best suits your working environment and your personal preferences regarding isolation of software installations.


Install in an Anaconda Python Default Environment
-------------------------------------------------

If you use the `Anaconda Python`_ distribution and want to install ECget in your default working environment
(or you don't know about creating alternate environments with :command:`conda create`),
these are the instructions for you:

.. _Anaconda Python: https://store.continuum.io/cshop/anaconda/

#. Use Mercurial to clone the project repo from Bitbucket;
   i.e.

   .. code-block:: bash

       $ hg clone https://bitbucket.org/douglatornell/ecget

#. Use :command:`conda` to install the Python packages that ECget depends on that are part of the Anaconda distribution:

   .. code-block:: bash

       $ conda install pip requests beautiful-soup six

#. Use :command:`pip` to install from PyPI_ the Python packages that ECget depends on that are *not* part of the Anaconda distribution:

   .. code-block:: bash

       $ pip install arrow cliff kombu

.. _PyPI: https://pypi.python.org/pypi

#. Use :command:`pip` to install ECget in editable mode so that updates that you pull from the Bitbucket repo will take effect immediately:

   .. code-block:: bash

       $ pip install --editable ./ecget


Install in a New :command:`conda` Environment
---------------------------------------------

#. Use Mercurial to clone the project repo from Bitbucket;
   i.e.

   .. code-block:: bash

       $ hg clone https://bitbucket.org/douglatornell/ecget

#. Use :command:`conda` to create a new Python 3.4 environment and install the Python packages that ECget depends on that are part of the Anaconda distribution:

   .. code-block:: bash

       $ conda create -n ecget python=3.4 pip requests beautiful-soup six

#. Activate the :kbd:`ecget` environment:

   .. code-block:: bash

       $ source activate ecget

#. Use :command:`pip` to install from PyPI_ the Python packages that ECget depends on that are *not* part of the Anaconda distribution:

   .. code-block:: bash

       (ecget)$ pip install arrow cliff kombu

#. Use :command:`pip` to install ECget in editable mode so that updates that you pull from the Bitbucket repo will take effect immediately:

   .. code-block:: bash

       (ecget)$ pip install --editable ./ecget

When you are finished using ECget you can deactivate the environment with:

.. code-block:: bash

    (ecget)$ source deactivate


Install in a Python 3.4 Virtual Environment
-------------------------------------------

#. Use :command:`pyvenv-3.4` to create a new Python 3.4 virtual environment and activate it:

   .. code-block:: bash

       $ pyvenv-3.4 ecget-venv
       $ cd ecget-venv
       $ source bin/activate

#. Use Mercurial to clone the project repo from Bitbucket;
   i.e.

   .. code-block:: bash

       (ecget-venv)$ hg clone https://bitbucket.org/douglatornell/ecget

#. Use :command:`pip` to install from PyPI_ the Python packages that ECget depends on,
    and install ECget in editable mode so that updates that you pull from the Bitbucket repo will take effect immediately:

   .. code-block:: bash

       (ecget-venv)$ pip install --editable ./ecget

When you are finished using ECget you can deactivate the environment with:

.. code-block:: bash

    (ecget-venv)$ deactivate

