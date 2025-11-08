*********
CHANGELOG
*********

..
    NOTE (mristin, 2021-12-27):
    Please keep this file at 72 line width so that we can copy-paste
    the release logs directly into commit messages.

1.2.0 (2025-11-08)
==================
* Support Python 3.12 and 3.13 (#55)
* Improve regexp generation for ``#`` (#50)
* Remove spurious CRLF warning (#48)
* Improve python-nested regex output for repetition (#45)
* Fix default for format argument (#42)
* Constrain abnf dependency to 2.2.0 (#43)

This is a minor version which mainly improves on the compatibility of
generated regular expressions so that they can be (re-)used across
more platforms.

1.1.3 (2024-03-22)
==================
* Fix for the case no min. and only max. repetition (#34)
* Discontinue Python 3.7 and include 3.11 (#33)

1.1.2 (2022-09-28)
==================
*  Upgrade to abnf 2.0.0 (#27)

1.1.1 (2022-06-15)
==================
* Add support for Python 3.9 and 3.10 (#24)
* Fix escaping for UTF-32 (#23)

1.1.0 (2022-05-22)
==================
* Add ``nested-in-python`` representation (#3)
* Merge character classes in alternations (#4)
* Remove unnecessary parentheses (#5)
* Remove unnecessary ``+`` in nested-python output (#7)
* Make compressions for nicer RFC 3339 (#8)
* Use Tarjan's depth-first topological sort (#10)
* Fix non-deterministic behavior due to sets (#11)
* Replace repetition range with shorter alternatives (#16)
* Test for RFC 8141 and fix transformations for it (#20)

1.0.0 (2022-05-27)
==================
* This is the initial release.
