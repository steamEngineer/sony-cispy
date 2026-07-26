"""Tests for constants module."""

from sony_cisip2 import constants


def test_default_port():
    """Test default port constant."""
    assert constants.DEFAULT_PORT == 33336


def test_tcp_timeout():
    """Test TCP timeout constant."""
    assert constants.TCP_TIMEOUT == 10.0
    assert isinstance(constants.TCP_TIMEOUT, float)


def test_command_id_initial():
    """Test command ID initial value."""
    assert constants.CMD_ID_INITIAL == 10
    assert isinstance(constants.CMD_ID_INITIAL, int)


def test_command_id_max():
    """Test command ID max value."""
    assert constants.CMD_ID_MAX == 1_000_000
    assert constants.CMD_ID_MAX > constants.CMD_ID_INITIAL


def test_message_types():
    """Test message type constants."""
    assert constants.MSG_TYPE_SET == "set"
    assert constants.MSG_TYPE_GET == "get"
    assert constants.MSG_TYPE_NOTIFY == "notify"
    assert constants.MSG_TYPE_RESULT == "result"


def test_response_values():
    """Test response value constants."""
    assert constants.RESPONSE_ACK == "ACK"
    assert constants.RESPONSE_NAK == "NAK"
    assert constants.RESPONSE_ERR == "ERR"


def test_feature_prefixes():
    """Test feature prefix constants."""
    assert constants.FEATURE_MAIN == "main."
    assert constants.FEATURE_ZONE2 == "zone2."
    assert constants.FEATURE_AUDIO == "audio."
    assert constants.FEATURE_SYSTEM == "system."
