import sys

from forecast.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["settle", *sys.argv[1:]]))
