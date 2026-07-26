"""Tests for commandset module."""

from sony_cisip2 import commands_dict


def test_commands_dict_exists():
    """Test that commands_dict exists and is not empty."""
    assert commands_dict is not None
    assert len(commands_dict) > 0


def test_commands_dict_structure():
    """Test that commands_dict has the expected structure."""
    for feature, details in list(commands_dict.items())[:5]:
        assert isinstance(feature, str)
        assert isinstance(details, dict)
        assert "description" in details
        assert "set" in details
        assert "get" in details
        assert "notify" in details


def test_common_commands_exist():
    """Test that common commands exist in the dictionary."""
    common_commands = [
        "main.power",
        "main.input",
        "main.volumestep",
        "main.mute",
        "audio.soundfield",
    ]

    for cmd in common_commands:
        assert cmd in commands_dict, f"Command {cmd} not found in commands_dict"


def test_command_properties():
    """Test command properties for specific commands."""
    if "main.power" in commands_dict:
        cmd = commands_dict["main.power"]
        assert cmd["set"] in ["Y", "N"]
        assert cmd["get"] in ["Y", "N"]
        assert cmd["notify"] in ["Y", "N"]
        assert isinstance(cmd["description"], str)


def test_command_feature_format():
    """Test that command features follow expected format."""
    # Check first 10 commands have expected format
    for feature in list(commands_dict.keys())[:10]:
        # Features should have at least one dot (e.g., "main.power")
        assert "." in feature or feature.startswith(("GUI", "system")), (
            f"Unexpected feature format: {feature}"
        )
