"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

import os

from setuptools import setup, find_packages

# pylint: disable=redefined-builtin

here = os.path.abspath(os.path.dirname(__file__))  # pylint: disable=invalid-name

with open(os.path.join(here, "README.rst"), encoding="utf-8") as fid:
    long_description = fid.read()  # pylint: disable=invalid-name

with open(os.path.join(here, "requirements.txt"), encoding="utf-8") as fid:
    install_requires = [line for line in fid.read().splitlines() if line.strip()]

setup(
    name="abnf-to-regexp",
    # Don't forget to update the version in __init__.py!
    version="1.1.3",
    description="Convert ABNF grammars to Python regular expressions.",
    long_description=long_description,
    url="https://github.com/aas-core-works/abnf-to-regexp",
    author="Marko Ristin",
    author_email="marko@ristin.ch",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    license="License :: OSI Approved :: MIT License",
    keywords="abnf backus-naur convert regular expressions",
    packages=find_packages(exclude=["tests"]),
    install_requires=install_requires,
    # fmt: off
    extras_require={
        "dev": [
            "black==24.3.0",
            "mypy==1.9.0",
            "pylint==2.3.1",
            "pydocstyle>=2.1.1,<3",
            "coverage>=4.5.1,<5",
            "docutils>=0.14,<1",
            "pygments>=2,<3",
        ],
    },
    # fmt: on
    py_modules=["abnf_to_regexp"],
    package_data={"abnf_to_regexp": ["py.typed"]},
    data_files=[(".", ["LICENSE", "README.rst", "requirements.txt"])],
    entry_points={"console_scripts": ["abnf-to-regexp = abnf_to_regexp.main:main"]},
)
