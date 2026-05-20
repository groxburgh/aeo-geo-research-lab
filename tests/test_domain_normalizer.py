from __future__ import annotations

from src.domain_normalizer import EXTRACTION_VERSION, normalize_domain


def test_standard_domain():
    assert normalize_domain("https://hbr.org/article") == "hbr.org"


def test_subdomain_stripped():
    assert normalize_domain("https://www.blog.hbr.org/page") == "hbr.org"


def test_ccSLD_uk():
    assert normalize_domain("https://bbc.co.uk/news") == "bbc.co.uk"


def test_ccSLD_uk_with_subdomain():
    assert normalize_domain("https://www.bbc.co.uk/news/article") == "bbc.co.uk"


def test_ccSLD_au():
    assert normalize_domain("https://example.com.au/page") == "example.com.au"


def test_plain_domain_no_scheme():
    assert normalize_domain("semrush.com") == "semrush.com"


def test_empty_string_returns_none():
    assert normalize_domain("") is None


def test_none_equivalent_empty():
    # normalize_domain expects str; empty string is the None-equivalent input
    assert normalize_domain("   ") is None


def test_bare_tld_returns_none():
    # "co.uk" is itself a public suffix, not a registered domain
    assert normalize_domain("https://co.uk") is None


def test_org_uk_is_suffix_not_domain():
    assert normalize_domain("https://org.uk") is None


def test_extraction_version_is_string():
    assert isinstance(EXTRACTION_VERSION, str)
    assert EXTRACTION_VERSION.startswith("v2")
