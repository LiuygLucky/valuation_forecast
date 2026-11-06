import sys

from forecast.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["init-db", *sys.argv[1:]]))
