from __future__ import annotations

from urllib.parse import urlparse

import tldextract

EXTRACTION_VERSION = "v2-tldextract-5.3"

# Constructed once at module load. suffix_list_urls=() disables all live HTTP fetches;
# the PSL snapshot bundled in the tldextract wheel is the sole source of truth.
# cache_dir is committed to the repo so every GitHub Actions run uses an identical
# PSL snapshot regardless of when publicsuffix.org was last updated.
_extract = tldextract.TLDExtract(
    suffix_list_urls=(),
    cache_dir=".cache/tldextract",
    fallback_to_snapshot=True,
    include_psl_private_domains=False,
)


def normalize_domain(url: str) -> str | None:
    """Return eTLD+1 for a URL using the Public Suffix List, or None if not extractable.

    Examples:
      hbr.org                  -> hbr.org
      www.blog.hbr.org         -> hbr.org
      bbc.co.uk                -> bbc.co.uk
      www.bbc.co.uk/news       -> bbc.co.uk
      example.com.au           -> example.com.au
      "" or non-URL            -> None
    """
    if not url:
        return None
    candidate = url.strip()
    if "://" not in candidate:
        candidate = "http://" + candidate
    try:
        host = urlparse(candidate).hostname or ""
    except ValueError:
        return None
    if not host:
        return None
    ext = _extract(host)
    # top_domain_under_public_suffix is the tldextract v5.x API (replaces deprecated registered_domain)
    result = ext.top_domain_under_public_suffix
    return result.lower() if result else None
