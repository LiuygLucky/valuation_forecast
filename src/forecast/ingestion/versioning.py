from forecast.audit.hashing import sha256
from forecast.db.models import Source, SourceVersion
from forecast.domain.time_policy import utc
from forecast.ingestion.canonicalize import canonical_url


def save_source(
    session,
    *,
    url,
    publisher,
    source_type,
    seen_at,
    published_at,
    content,
    title,
    archive_uri=None,
    origin_group_id=None,
    parent_source_id=None,
    synthetic=False,
    access_status="ACCESSIBLE",
    metadata=None,
    archive_capture_at=None,
    archive_verified=False,
    content_digest=None,
):
    url = canonical_url(url)
    sid = "src_" + sha256(url + str(synthetic))[:24]
    seen = utc(seen_at).isoformat()
    published = utc(published_at).isoformat() if published_at else None
    if session.get(Source, sid) is None:
        session.add(
            Source(
                source_id=sid,
                canonical_url=url,
                publisher=publisher,
                source_type=source_type,
                first_public_at=published,
                first_seen_at=seen,
                retrieved_at=seen,
                access_status=access_status,
                origin_group_id=origin_group_id,
                parent_source_id=parent_source_id,
                synthetic=synthetic,
            )
        )
        session.flush()
    digest = content_digest or sha256(content)
    vid = "ver_" + sha256(sid + digest + str(published))[:24]
    if session.get(SourceVersion, vid) is None:
        session.add(
            SourceVersion(
                version_id=vid,
                source_id=sid,
                content_sha256=digest,
                captured_at=seen,
                archive_uri=archive_uri,
                title=title,
                raw_excerpt=content[:12000],
                published_at=published,
                content_version_status="SYNTHETIC" if synthetic else "CAPTURED",
                metadata_json=metadata or {},
                archive_capture_at=archive_capture_at,
                archive_verified=archive_verified,
            )
        )
        session.flush()
    return sid, vid
