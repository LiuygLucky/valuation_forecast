import sys

from forecast.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["backtest", *sys.argv[1:]]))
