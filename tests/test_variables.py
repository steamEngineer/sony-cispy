"""Tests for variables module."""

from sony_cisip2 import variables_dict


def test_variables_dict_exists():
    """Test that variables_dict exists and is not empty."""
    assert variables_dict is not None
    assert len(variables_dict) > 0


def test_variables_dict_structure():
    """Test that variables_dict has the expected structure."""
    assert isinstance(variables_dict, dict)
    for key, value in variables_dict.items():
        assert isinstance(key, str)
        assert isinstance(value, (set, list, dict))


def test_common_variables_exist():
    """Test that common variable groups exist."""
    expected_variables = [
        "INPUTSOURCE_VARIABLES",
        "INPUTCONFIG_VARIABLES",
        "ICON_VARIABLES",
        "SOUNDFIELD_VARIABLES",
    ]

    for var in expected_variables:
        assert var in variables_dict, f"Variable group {var} not found"


def test_input_source_variables():
    """Test INPUTSOURCE_VARIABLES structure."""
    if "INPUTSOURCE_VARIABLES" in variables_dict:
        sources = variables_dict["INPUTSOURCE_VARIABLES"]
        assert isinstance(sources, set)
        assert len(sources) > 0


def test_soundfield_variables():
    """Test SOUNDFIELD_VARIABLES structure."""
    if "SOUNDFIELD_VARIABLES" in variables_dict:
        soundfields = variables_dict["SOUNDFIELD_VARIABLES"]
        assert isinstance(soundfields, set)
        assert len(soundfields) > 0
