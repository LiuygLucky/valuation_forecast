from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def canonical_url(url: str) -> str:
    p = urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        raise ValueError("public HTTP(S) URL required")
    query = sorted(
        (k, v)
        for k, v in parse_qsl(p.query)
        if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")
    )
    return urlunsplit(
        (p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/", urlencode(query), "")
    )
