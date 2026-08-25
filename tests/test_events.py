"""Tests for ../src/lm_tuio/events.py.

Tests each Message subclass verifies msg/severity/ip/port/model/instance_ids are set correctly.
"""

from lm_tuio.events import (
    ActionLogUpdate,
    ServerEndpointUpdated,
    ServerConnected,
    ModelSelected,
    ModelLoadRequest,
    UnloadInstancesRequested,
    SettingsSaved,
)
from lm_tuio.models import ModelInfo


# ===== ActionLogUpdate =====


class TestActionLogUpdate:
    """Test ActionLogUpdate Message class."""

    def test_default_severity(self):
        """Default severity is 'info'."""
        msg = ActionLogUpdate("test message")
        assert msg.msg == "test message"
        assert msg.severity == "info"

    def test_custom_severity(self):
        """Custom severity is set correctly."""
        msg = ActionLogUpdate("error occurred", severity="error")
        assert msg.msg == "error occurred"
        assert msg.severity == "error"

    def test_all_severity_levels(self):
        """Each severity level is preserved."""
        for sev in ["info", "warn", "error", "success"]:
            msg = ActionLogUpdate("test", severity=sev)
            assert msg.severity == sev

    def test_is_textual_message(self):
        """Inherits from textual.message.Message."""
        from textual.message import Message
        msg = ActionLogUpdate("test")
        assert isinstance(msg, Message)


# ===== ServerEndpointUpdated =====


class TestServerEndpointUpdated:
    """Test ServerEndpointUpdated Message class."""

    def test_ip_and_port_set(self):
        """IP and port are set correctly."""
        msg = ServerEndpointUpdated("192.168.1.10", 1234)
        assert msg.ip == "192.168.1.10"
        assert msg.port == 1234

    def test_different_ips(self):
        """Different IPs are preserved."""
        for ip in ["127.0.0.1", "10.0.0.1", "192.168.0.1"]:
            msg = ServerEndpointUpdated(ip, 8080)
            assert msg.ip == ip

    def test_different_ports(self):
        """Different ports are preserved."""
        for port in [8080, 443, 1234]:
            msg = ServerEndpointUpdated("127.0.0.1", port)
            assert msg.port == port

    def test_is_textual_message(self):
        """Inherits from textual.message.Message."""
        from textual.message import Message
        msg = ServerEndpointUpdated("127.0.0.1", 1234)
        assert isinstance(msg, Message)


# ===== ServerConnected =====


class TestServerConnected:
    """Test ServerConnected Message class."""

    def test_ip_and_port_set(self):
        """IP and port are set correctly."""
        msg = ServerConnected("192.168.1.10", 1234)
        assert msg.ip == "192.168.1.10"
        assert msg.port == 1234

    def test_is_textual_message(self):
        """Inherits from textual.message.Message."""
        from textual.message import Message
        msg = ServerConnected("127.0.0.1", 1234)
        assert isinstance(msg, Message)


# ===== ModelSelected =====


class TestModelSelected:
    """Test ModelSelected Message class."""

    def test_with_model_info(self):
        """ModelInfo is set correctly."""
        model = ModelInfo(
            id="test.gguf",
            name="test",
            size=1024,
            parameters=512,
            family="test",
            format="gguf",
            type="test",
            publisher="Test",
            key="test",
            display_name="test",
            size_bytes=1024,
            max_context_length=4096,
            loaded_instances=[],
        )
        msg = ModelSelected(model)
        assert msg.model == model
        assert msg.model.key == "test"

    def test_with_none(self):
        """None model is set correctly."""
        msg = ModelSelected(None)
        assert msg.model is None

    def test_is_textual_message(self):
        """Inherits from textual.message.Message."""
        from textual.message import Message
        msg = ModelSelected(None)
        assert isinstance(msg, Message)


# ===== ModelLoadRequest =====


class TestModelLoadRequest:
    """Test ModelLoadRequest Message class."""

    def test_with_model_info(self):
        """ModelInfo is set correctly."""
        model = ModelInfo(
            id="test.gguf",
            name="test",
            size=1024,
            parameters=512,
            family="test",
            format="gguf",
            type="test",
            publisher="Test",
            key="test",
            display_name="test",
            size_bytes=1024,
            max_context_length=4096,
            loaded_instances=[],
        )
        msg = ModelLoadRequest(model)
        assert msg.model == model

    def test_with_none(self):
        """None model is set correctly."""
        msg = ModelLoadRequest(None)
        assert msg.model is None

    def test_is_textual_message(self):
        """Inherits from textual.message.Message."""
        from textual.message import Message
        msg = ModelLoadRequest(None)
        assert isinstance(msg, Message)


# ===== UnloadInstancesRequested =====


class TestUnloadInstancesRequested:
    """Test UnloadInstancesRequested Message class."""

    def test_single_instance(self):
        """Single instance ID is set correctly."""
        msg = UnloadInstancesRequested(["inst-1"])
        assert msg.instance_ids == ["inst-1"]

    def test_multiple_instances(self):
        """Multiple instance IDs are set correctly."""
        ids = ["inst-1", "inst-2", "inst-3"]
        msg = UnloadInstancesRequested(ids)
        assert msg.instance_ids == ids

    def test_empty_list(self):
        """Empty list is set correctly."""
        msg = UnloadInstancesRequested([])
        assert msg.instance_ids == []

    def test_is_textual_message(self):
        """Inherits from textual.message.Message."""
        from textual.message import Message
        msg = UnloadInstancesRequested(["inst-1"])
        assert isinstance(msg, Message)


# ===== SettingsSaved =====


class TestSettingsSaved:
    """Test SettingsSaved Message class."""

    def test_theme_and_timezone_set(self):
        """Theme and timezone are set correctly."""
        msg = SettingsSaved("textual-dark", "America/New_York")
        assert msg.theme == "textual-dark"
        assert msg.timezone == "America/New_York"

    def test_different_theme(self):
        """Different theme values are preserved."""
        msg = SettingsSaved("textual-light", "UTC")
        assert msg.theme == "textual-light"
        assert msg.timezone == "UTC"

    def test_is_textual_message(self):
        """Inherits from textual.message.Message."""
        from textual.message import Message
        msg = SettingsSaved("textual-dark", "UTC")
        assert isinstance(msg, Message)


# ===== All events are Message subclasses =====


class TestAllEventsInheritMessage:
    """All event classes inherit from textual.message.Message."""

    def test_all_events_are_messages(self):
        """Each event class is a subclass of Message."""
        from textual.message import Message

        events = [
            ActionLogUpdate("test"),
            ServerEndpointUpdated("127.0.0.1", 1234),
            ServerConnected("127.0.0.1", 1234),
            ModelSelected(None),
            ModelLoadRequest(None),
            UnloadInstancesRequested([]),
            SettingsSaved("textual-dark", "UTC"),
        ]

        for event in events:
            assert isinstance(event, Message)
