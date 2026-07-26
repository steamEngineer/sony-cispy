"""Constants for the Sony CIS-IP2 protocol."""

from __future__ import annotations

# Default port for CIS-IP2 TCP communication
DEFAULT_PORT = 33336

# Timeout for TCP operations (in seconds)
TCP_TIMEOUT = 10.0

# Reconnection delays (seconds); sleep then try; double on failure, capped
RECONNECT_INITIAL_DELAY = 5.0
RECONNECT_MAX_DELAY = 60.0

# Command ID management
CMD_ID_INITIAL = 10
CMD_ID_MAX = 1_000_000

# Message types
MSG_TYPE_SET = "set"
MSG_TYPE_GET = "get"
MSG_TYPE_NOTIFY = "notify"
MSG_TYPE_RESULT = "result"

# Common response values
RESPONSE_ACK = "ACK"
RESPONSE_NAK = "NAK"
RESPONSE_ERR = "ERR"

# Common feature prefixes
FEATURE_MAIN = "main."
FEATURE_ZONE2 = "zone2."
FEATURE_ZONE3 = "zone3."
FEATURE_AUDIO = "audio."
FEATURE_HDMI = "hdmi."
FEATURE_SYSTEM = "system."
FEATURE_GUI = "GUI."
FEATURE_DISTANCE = "distance."
FEATURE_LEVEL = "level."
FEATURE_SIZE = "size."
FEATURE_CROSSOVER = "crossover."
FEATURE_SPEAKER = "speaker."
FEATURE_BASS = "bass."
FEATURE_TREBLE = "treble."
FEATURE_NETWORK = "network."
FEATURE_TUNER = "tuner."
