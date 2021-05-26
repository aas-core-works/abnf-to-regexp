"""Run abnf-to-regexp as Python module."""

import abnf_to_regexp.main

if __name__ == "__main__":
    # The ``prog`` needs to be set in the argparse.
    # Otherwise the program name in the help shown to the user will be ``__main__``.
    abnf_to_regexp.main.main()
