**************
abnf-to-regexp
**************

.. image:: https://github.com/aas-core-works/abnf-to-regexp/actions/workflows/check-on-push-to-main.yml/badge.svg
    :target: https://github.com/aas-core-works/abnf-to-regexp/actions/workflows/check-on-push-to-main.yml
    :alt: Check on push to main

.. image:: https://coveralls.io/repos/github/aas-core-works/abnf-to-regexp/badge.svg?branch=main
    :target: https://coveralls.io/github/aas-core-works/abnf-to-regexp?branch=main
    :alt: Test coverage

.. image:: https://badge.fury.io/py/abnf-to-regexp.svg
    :target: https://badge.fury.io/py/abnf-to-regexp
    :alt: PyPI - version

.. image:: https://img.shields.io/pypi/pyversions/abnf-to-regexp.svg
    :alt: PyPI - Python Version


The program ``abnf-to-regexp`` converts augmented Backus-Naur form (ABNF) to a regular expression.

Motivation
==========
For a lot of string matching problems, it is easier to maintain an ABNF grammar instead of a regular expression.
However, many programming languages do not provide parsing and matching of ABNFs in their standard libraries.
This tool allows you to write your grammars in ABNF and convert it to a regular expression which you then include in your source code.

It is based on `abnf`_ Python module, which is used to parse the ABNFs.

.. _abnf: https://pypi.org/project/abnf

After the parsing, we apply a series of optimizations to make the regular expression a bit more readable.
For example, the alternations of character classes are taken together to form a single character class.

``--help``
==========
.. Help starts: python3 abnf_to_regexp/main.py --help
.. code-block::

    usage: abnf-to-regexp [-h] -i INPUT [-o OUTPUT]
                          [--format {single-regexp,python-nested}]

    Convert ABNF grammars to Python regular expressions.

    optional arguments:
      -h, --help            show this help message and exit
      -i INPUT, --input INPUT
                            path to the ABNF file
      -o OUTPUT, --output OUTPUT
                            path to the file where regular expression is stored;
                            if not specified, writes to STDOUT
      --format {single-regexp,python-nested}
                            Output format; for example a single regular expression
                            or a code snippet

.. Help ends: python3 abnf_to_regexp/main.py --help

Example Conversion
==================
Please see `test_data/nested-python/rfc3987/grammar.abnf`_ for an example grammar.

The corresponding generated code, *e.g.*, in Python, is stored at `test_data/nested-python/rfc3987/expected.py`_.

.. _test_data/nested-python/rfc3987/grammar.abnf: https://github.com/aas-core-works/abnf-to-regexp/blob/main/test_data/nested-python/rfc3987/grammar.abnf
.. _test_data/nested-python/rfc3987/expected.py: https://github.com/aas-core-works/abnf-to-regexp/blob/main/test_data/nested-python/rfc3987/expected.py

Installation
============
You can install the tool with pip in your virtual environment:

.. code-block::

    pip3 install abnf-to-regexp

Development
===========

* Check out the repository.

* In the repository root, create the virtual environment:

.. code-block:: bash

    python3 -m venv venv3

* Activate the virtual environment (in this case, on Linux):

.. code-block:: bash

    source venv3/bin/activate

* Install the development dependencies:

.. code-block:: bash

    pip3 install -e .[dev]

* Run the pre-commit checks:

.. code-block:: bash

    python precommit.py

Versioning
==========
We follow `Semantic Versioning <http://semver.org/spec/v1.0.0.html>`_.
The version X.Y.Z indicates:

* X is the major version (backward-incompatible),
* Y is the minor version (backward-compatible), and
* Z is the patch version (backward-compatible bug fix).
