"""Asset validation and loading for Studio module."""

from pathlib import Path
from typing import List, Dict
from studio.errors import AssetError
from studio.types import AssetManifest


def get_assets_dir() -> Path:
    """Get path to studio assets directory.

    Returns:
        Path to studio/assets/
    """
    return Path(__file__).parent / "assets"


def list_required_assets() -> List[str]:
    """List all required asset files for rendering.

    Returns:
        List of required asset filenames
    """
    return [
        "avatar_base.blend",
        "studio_default.blend",
        "actions/idle_bob.blend",
        "actions/deck_scratch_L.blend",
        "actions/deck_scratch_R.blend",
        "actions/crossfader_hit.blend",
        "actions/drop_reaction.blend",
        "actions/spotlight_present.blend",
    ]


def validate_assets() -> tuple[bool, List[str]]:
    """Validate that all required assets exist.

    Returns:
        (is_valid, missing_files) tuple

    Raises:
        AssetError: If critical assets are missing and strict mode enabled
    """
    assets_dir = get_assets_dir()
    required = list_required_assets()
    missing = []

    for asset in required:
        asset_path = assets_dir / asset
        if not asset_path.exists():
            missing.append(asset)

    is_valid = len(missing) == 0
    return (is_valid, missing)


def validate_assets_strict() -> None:
    """Validate assets and raise exception if any are missing.

    Raises:
        AssetError: If any required assets are missing
    """
    is_valid, missing = validate_assets()

    if not is_valid:
        assets_dir = get_assets_dir()
        error_msg = (
            f"Required assets missing from {assets_dir}:\n" +
            "\n".join(f"  • {f}" for f in missing) +
            f"\n\nSee {assets_dir / 'README.md'} for asset specifications."
        )
        raise AssetError(error_msg)


def get_asset_path(asset_name: str) -> Path:
    """Get full path to a specific asset file.

    Args:
        asset_name: Asset filename (e.g., "avatar_base.blend" or "actions/idle_bob.blend")

    Returns:
        Full path to asset

    Raises:
        AssetError: If asset doesn't exist
    """
    assets_dir = get_assets_dir()
    asset_path = assets_dir / asset_name

    if not asset_path.exists():
        raise AssetError(f"Asset not found: {asset_path}")

    return asset_path


def load_asset_manifest() -> AssetManifest:
    """Load asset manifest with all required file paths.

    Returns:
        AssetManifest with paths to all required assets

    Raises:
        AssetError: If any required assets are missing
    """
    validate_assets_strict()

    assets_dir = get_assets_dir()

    return {
        "avatar_base": str(assets_dir / "avatar_base.blend"),
        "studio_environment": str(assets_dir / "studio_default.blend"),
        "actions": [
            str(assets_dir / "actions" / "idle_bob.blend"),
            str(assets_dir / "actions" / "deck_scratch_L.blend"),
            str(assets_dir / "actions" / "deck_scratch_R.blend"),
            str(assets_dir / "actions" / "crossfader_hit.blend"),
            str(assets_dir / "actions" / "drop_reaction.blend"),
            str(assets_dir / "actions" / "spotlight_present.blend"),
        ]
    }


def check_asset_integrity(asset_path: Path) -> bool:
    """Check if a .blend file is valid (basic sanity check).

    Args:
        asset_path: Path to .blend file

    Returns:
        True if file appears valid, False otherwise
    """
    if not asset_path.exists():
        return False

    # Basic check: .blend files should be >100KB
    # (Blender's minimum file size is typically around 500KB)
    if asset_path.stat().st_size < 100 * 1024:
        return False

    # Check magic bytes (Blender files start with "BLENDER")
    try:
        with open(asset_path, "rb") as f:
            header = f.read(7)
            return header == b"BLENDER"
    except Exception:
        return False


def validate_all_asset_integrity() -> Dict[str, bool]:
    """Validate integrity of all assets.

    Returns:
        Dict mapping asset name to validity status
    """
    results = {}
    assets_dir = get_assets_dir()

    for asset_name in list_required_assets():
        asset_path = assets_dir / asset_name
        if asset_path.exists():
            results[asset_name] = check_asset_integrity(asset_path)
        else:
            results[asset_name] = False

    return results
