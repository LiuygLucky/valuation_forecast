from enum import StrEnum


class RunMode(StrEnum):
    DEMO = "DEMO"
    PROVISIONAL = "PROVISIONAL"
    LIVE = "LIVE"
    REPLAY = "REPLAY"
    HISTORICAL_ARCHIVED = "HISTORICAL_ARCHIVED"


def parse_mode(mode):
    return RunMode(str(mode).upper())
