Installation
============

This section explains how to install **mgconfig**.

Prerequisites
-------------

- Python 3.8 or later
- (Optional) `pip` for package installation
- (Optional) `virtualenv` for isolated environments

From PyPI
---------

If `mgconfig` is published on PyPI, you can install it with:

.. code-block:: bash

    pip install mgconfig

From Source
-----------

If you have the source code locally (e.g., from GitHub or a zip file):

.. code-block:: bash

    git clone https://github.com/yourusername/mgconfig.git
    cd mgconfig
    pip install .

Development Installation
------------------------

To install in editable mode for development:

.. code-block:: bash

    pip install -e .[dev]

This will install `mgconfig` and its development dependencies.

Verifying the Installation
--------------------------

Run Python and import the package:

.. code-block:: python

    import mgconfig
    print(mgconfig.__version__)
