"""Tests for studio.asset_loader module."""

import pytest
from pathlib import Path
from studio.asset_loader import (
    get_assets_dir,
    list_required_assets,
    validate_assets,
    get_asset_path,
    check_asset_integrity
)
from studio.errors import AssetError


def test_get_assets_dir():
    """Test getting assets directory path."""
    assets_dir = get_assets_dir()

    assert assets_dir.exists()
    assert assets_dir.name == "assets"
    assert (assets_dir.parent.name == "studio")


def test_list_required_assets():
    """Test listing required assets."""
    required = list_required_assets()

    assert "avatar_base.blend" in required
    assert "studio_default.blend" in required
    assert "actions/idle_bob.blend" in required
    assert "actions/drop_reaction.blend" in required
    assert len(required) >= 8  # At least 8 required assets


def test_validate_assets():
    """Test asset validation."""
    is_valid, missing = validate_assets()

    # Assets likely missing in test environment
    assert isinstance(is_valid, bool)
    assert isinstance(missing, list)

    # If invalid, should have missing files
    if not is_valid:
        assert len(missing) > 0


def test_get_asset_path_missing():
    """Test getting path to non-existent asset raises error."""
    # This will likely fail since assets aren't committed
    with pytest.raises(AssetError):
        get_asset_path("avatar_base.blend")


def test_check_asset_integrity_missing():
    """Test integrity check on non-existent file."""
    fake_path = Path("/nonexistent/file.blend")
    assert check_asset_integrity(fake_path) is False


def test_check_asset_integrity_too_small(tmp_path):
    """Test integrity check fails for file too small."""
    small_file = tmp_path / "small.blend"
    small_file.write_bytes(b"BLENDER" + b"x" * 100)  # Only 107 bytes

    assert check_asset_integrity(small_file) is False


def test_check_asset_integrity_wrong_header(tmp_path):
    """Test integrity check fails for wrong magic bytes."""
    wrong_file = tmp_path / "wrong.blend"
    wrong_file.write_bytes(b"NOTBLEND" + b"x" * 200000)

    assert check_asset_integrity(wrong_file) is False


def test_check_asset_integrity_valid(tmp_path):
    """Test integrity check passes for valid-looking file."""
    valid_file = tmp_path / "valid.blend"
    # Create file with BLENDER header and >100KB size
    valid_file.write_bytes(b"BLENDER" + b"x" * 150000)

    assert check_asset_integrity(valid_file) is True
