"""Check that the version in ``pyproject.toml`` and ``__init__.py`` coincide."""

import importlib.metadata
import sys

import abnf_to_regexp


def main() -> None:
    """Execute the main routine."""
    init_version = abnf_to_regexp.__version__

    pyproject_toml_version = importlib.metadata.version("abnf-to-regexp")

    if init_version != pyproject_toml_version:
        print(
            f"The version in {abnf_to_regexp.__file__} is: {init_version!r}, "
            f"but the version in pyproject.toml is: {pyproject_toml_version!r}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
