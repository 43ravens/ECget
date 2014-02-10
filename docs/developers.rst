**************
For Developers
**************

If you would like to contribute to ECget directly,
these instructions should help you get started.
Bug reports and feature requests are all welcome through the `Bitbucket project`_.

.. _Bitbucket project: https://bitbucket.org/douglatornell/ecget

Changes to ECget should be submitted as pull requests on `Bitbucket project`_.

Bugs should be files under the `Bitbucket project`_.

.. note::

    Before contributing new features to ECget,
    please consider whether they should be implemented as an extension instead.
    The architecture is highly pluggable precisely to keep the core small.


.. _DevelopmentEnvironment:

Development Environment
=======================

ECget is developed under Python 3.3 and tested under Python 2.7 and Python 3.2.
Setting up a Python 3.3 virtualenv via pyvenv is a little tricky because pyvenv doesn't install/include pip and setuptools.
These commands should result in a viable,
working Python 3.3 virtual environment:

.. code-block:: bash

    pyvenv-3.3 ecget
    cd ecget
    (ecget)$ . bin/activate
    (ecget)$ curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    (ecget)$ python3.3 get-pip.py

Thanks to `Richard Jones`_ for those commands.

.. _Richard Jones: http://www.mechanicalcat.net/richard/log/Python/Python_3_3_and_virtualenv

After cloning the source code repo from the `Bitbucket project`_,
the Python packages at the versions used for development at tip can be installed with:

.. code-block:: bash

    (ecget)$ pip install -r requirements.txt

Install the ECget package for development with:

.. code-block:: bash

    (ecget)$ cd ecget
    (ecget)$ pip install -e .

or

.. code-block:: bash

    (ecget)$ cd ecget
    (ecget)$ python setup.py develop

.. note::

    Because ECget uses setuptools entry points for plug-in discovery it is necessary to install the package whenever entry points are changed or added in :file:`setup.py`.


Building Documentation
======================

The documentation for ECget is written in reStructuredText and converted to HTML using Sphinx.
The build itself is driven by make.
Installing the development packages via the :file:`requirements.txt` file as described above will install Sphinx.
Once that has been done use:

.. code-block:: bash

    (ecget)$ (cd docs && make clean html)
    rm -rf _build/*
    sphinx-build -b html -d _build/doctrees   . _build/html
    Making output directory...
    Running Sphinx v1.2.1
    loading pickled environment... done
    building [html]: targets for 3 source files that are out of date
    updating environment: 3 added, 0 changed, 0 removed
    reading sources... [100%] install
    looking for now-outdated files... none found
    pickling environment... done
    checking consistency... done
    preparing documents... done
    writing output... [100%] install
    writing additional files... (0 module code pages) genindex search
    copying static files... done
    copying extra files... done
    dumping search index... done
    dumping object inventory... done
    build succeeded.

    Build finished. The HTML pages are in _build/html.

to generate the HTML version of the documentation.
The output ends up in :file:`./docs/_build/html/` in your development directory.


Running Tests
=============

The test suite for ECget uses pytest_,
coverage_,
and tox_.
Installing the development packages via the :file:`requirements.txt` file as described in the :ref:`DevelopmentEnvironment` section above will install those packages and their dependencies.

.. _pytest: http://pytest.org/
.. _coverage: http://nedbatchelder.com/code/coverage/
.. _tox: http://tox.testrun.org/

Use the :command:`py.test` command from the top level directory of the Mercurial repository to run the test suite in the development environment:

.. code-block:: bash

    (ecget)$ py.test
    ======================================= test session starts ========================================
    platform darwin -- Python 3.3.2 -- pytest-2.5.1
    collected 1 items

    tests/test_SOG_formatters.py .

    ===================================== 1 passed in 0.13 seconds =====================================

To gather test coverage data use :command:`coverage run -m py.test` and view the coverage report with :command:`coverage report`:

.. code-block:: bash

    (ecget)$ coverage report
    Name                        Stmts   Miss Branch BrMiss  Cover   Missing
    -----------------------------------------------------------------------
    ecget/SOG_formatters            9      0      4      2    85%
    ecget/__init__                  0      0      0      0   100%
    ecget/main                     12     12      2      2     0%   22-45
    ecget/river                   110    110     24     24     0%   18-229
    tests/test_SOG_formatters       9      0      0      0   100%
    -----------------------------------------------------------------------
    TOTAL                         140    122     30     28    12%

The default :program:`coverage` run and report option values are set in the :file:`.coveragerc` file.

Use the :command:`tox` command to run the tests under Python 3.3,
3.2,
and 2.7.

.. note::

    You must have all of those versions of Python installed on your system for :program:`tox` to succeed.

To run the tests under a single version of Python,
specify the appropriate environment when running :command:`tox`:

.. code-block:: bash

    (ecget)$ tox -e py27
