"""python -m zoo: the same as the `zoo` command."""

import sys

from zoo.cli import main

if __name__ == "__main__":
    sys.exit(main())
