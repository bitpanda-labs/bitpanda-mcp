"""Tests for package metadata and build correctness."""

from importlib.metadata import entry_points, metadata


def test_package_metadata() -> None:
    m = metadata("bitpanda-mcp")
    assert m["Name"] == "bitpanda-mcp"
    assert m["Version"]
    assert "Bitpanda" in m["Author-email"]


def test_entry_point_registered() -> None:
    eps = entry_points(group="console_scripts", name="bitpanda-mcp")
    ep = next(iter(eps))
    assert ep.value == "bitpanda_mcp.server:main"
