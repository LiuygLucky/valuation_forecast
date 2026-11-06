from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class DataFetchResult:
    provider: str
    status: str
    data: dict = field(default_factory=dict)
    http_status: int | None = None
    reason: str | None = None


class NpmValuationProvider(Protocol):
    def fetch_latest(self) -> DataFetchResult: ...


class SearchProvider(Protocol):
    def search(self, query: str, **kwargs) -> DataFetchResult: ...


class ExtractionProvider(Protocol):
    def extract(self, source: dict) -> DataFetchResult: ...
