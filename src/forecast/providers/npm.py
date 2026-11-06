from forecast.providers.base import DataFetchResult


class ManualNpmProvider:
    """No authorized stable official API identified. Never probe hidden endpoints."""

    def fetch_latest(self) -> DataFetchResult:
        return DataFetchResult(
            "NPM",
            "NPM_FETCH_BLOCKED",
            reason="No authorized official API configured; import a reviewed capture/export.",
        )
