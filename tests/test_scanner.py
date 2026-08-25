"""Tests for ../src/lm_tuio/scanner.py.

Tests check_host() and scan_targets() with mocked network connections.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ===== check_host =====


class TestCheckHost:
    """Test check_host() TCP connection check."""

    @pytest.mark.anyio
    async def test_successful_connection(self):
        """Successful TCP connection returns the IP."""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()

        async def _close():
            pass

        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
            result = await asyncio.wait_for(
                __import__("lm_tuio.scanner", fromlist=["check_host"]).check_host(
                    "192.168.1.10", 1234
                ),
                timeout=5,
            )
        assert result == "192.168.1.10"

    @pytest.mark.anyio
    async def test_connection_refused(self):
        """ConnectionRefusedError returns None."""
        with patch(
            "asyncio.open_connection",
            side_effect=ConnectionRefusedError("Connection refused"),
        ):
            result = await asyncio.wait_for(
                __import__("lm_tuio.scanner", fromlist=["check_host"]).check_host(
                    "192.168.1.10", 1234
                ),
                timeout=5,
            )
        assert result is None

    @pytest.mark.anyio
    async def test_timeout(self):
        """TimeoutError returns None."""
        with patch(
            "asyncio.open_connection",
            side_effect=TimeoutError("Connection timed out"),
        ):
            result = await asyncio.wait_for(
                __import__("lm_tuio.scanner", fromlist=["check_host"]).check_host(
                    "192.168.1.10", 1234
                ),
                timeout=5,
            )
        assert result is None

    @pytest.mark.anyio
    async def test_os_error(self):
        """Generic OSError returns None."""
        with patch(
            "asyncio.open_connection",
            side_effect=OSError("Network unreachable"),
        ):
            result = await asyncio.wait_for(
                __import__("lm_tuio.scanner", fromlist=["check_host"]).check_host(
                    "192.168.1.10", 1234
                ),
                timeout=5,
            )
        assert result is None

    @pytest.mark.anyio
    async def test_custom_timeout(self):
        """Custom timeout is passed to wait_for."""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()

        async def _close():
            pass

        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
            result = await asyncio.wait_for(
                __import__("lm_tuio.scanner", fromlist=["check_host"]).check_host(
                    "192.168.1.10", 1234, timeout=5.0
                ),
                timeout=10,
            )
        assert result == "192.168.1.10"


# ===== scan_targets =====


class TestScanTargets:
    """Test scan_targets() network scanning."""

    @pytest.mark.anyio
    async def test_scan_single_ip_success(self):
        """Single IP mode returns active host."""
        from lm_tuio.config.settings import AppConfig

        config = AppConfig(target="192.168.1.10", port=1234)
        config.is_network = False  # single IP

        mock_reader = AsyncMock()
        mock_writer = AsyncMock()

        async def _close():
            pass

        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
            hosts, err = await asyncio.wait_for(
                __import__("lm_tuio.scanner", fromlist=["scan_targets"]).scan_targets(
                    config
                ),
                timeout=10,
            )

        assert err is None
        assert hosts == ["192.168.1.10"]

    @pytest.mark.anyio
    async def test_scan_single_ip_failure(self):
        """Single IP mode with no response returns None hosts."""
        from lm_tuio.config.settings import AppConfig

        config = AppConfig(target="192.168.1.10", port=1234)
        config.is_network = False

        with patch(
            "asyncio.open_connection",
            side_effect=ConnectionRefusedError(),
        ):
            hosts, err = await asyncio.wait_for(
                __import__("lm_tuio.scanner", fromlist=["scan_targets"]).scan_targets(
                    config
                ),
                timeout=10,
            )

        assert hosts is None
        assert "No active endpoints" in str(err)

    @pytest.mark.anyio
    async def test_scan_network_multiple_hosts(self):
        """Network scan returns all active hosts."""
        from lm_tuio.config.settings import AppConfig

        config = AppConfig(target="192.168.1.0/24", port=1234)
        config.is_network = True

        call_count = [0]

        async def mock_open(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] in (1, 3):  # only first and third IPs respond
                mock_writer = AsyncMock()

                async def _close():
                    pass

                mock_writer.close = MagicMock()
                mock_writer.wait_closed = AsyncMock()
                return AsyncMock(), mock_writer
            raise ConnectionRefusedError()

        with patch("asyncio.open_connection", side_effect=mock_open):
            hosts, err = await asyncio.wait_for(
                __import__("lm_tuio.scanner", fromlist=["scan_targets"]).scan_targets(
                    config
                ),
                timeout=30,
            )

        assert err is None
        assert len(hosts) == 2
        assert "192.168.1.1" in hosts
        assert "192.168.1.3" in hosts

    @pytest.mark.anyio
    async def test_scan_network_no_active_hosts(self):
        """All hosts down returns None and error message."""
        from lm_tuio.config.settings import AppConfig

        config = AppConfig(target="192.168.1.255/30", port=1234)
        config.is_network = True

        with patch(
            "asyncio.open_connection",
            side_effect=ConnectionRefusedError(),
        ):
            hosts, err = await asyncio.wait_for(
                __import__("lm_tuio.scanner", fromlist=["scan_targets"]).scan_targets(
                    config
                ),
                timeout=10,
            )

        assert hosts is None
        assert "No active endpoints" in str(err)

    @pytest.mark.anyio
    async def test_scan_network_all_hosts_active(self):
        """All hosts in a small subnet are active."""
        from lm_tuio.config.settings import AppConfig

        config = AppConfig(target="192.168.1.252/30", port=1234)
        config.is_network = True

        async def mock_open(*args, **kwargs):
            mock_writer = AsyncMock()

            async def _close():
                pass

            mock_writer.close = MagicMock()
            mock_writer.wait_closed = AsyncMock()
            return AsyncMock(), mock_writer

        with patch("asyncio.open_connection", side_effect=mock_open):
            hosts, err = await asyncio.wait_for(
                __import__("lm_tuio.scanner", fromlist=["scan_targets"]).scan_targets(
                    config
                ),
                timeout=10,
            )

        assert err is None
        assert hosts is not None
        assert len(hosts) == 2  # /30 has 2 usable hosts

    @pytest.mark.anyio
    async def test_scan_single_ip_with_subnet_notation(self):
        """Single IP with /32 notation still scans one host."""
        from lm_tuio.config.settings import AppConfig

        config = AppConfig(target="10.0.0.1/32", port=1234)
        config.is_network = False

        mock_writer = AsyncMock()

        async def _close():
            pass

        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch("asyncio.open_connection", return_value=(AsyncMock(), mock_writer)):
            hosts, err = await asyncio.wait_for(
                __import__("lm_tuio.scanner", fromlist=["scan_targets"]).scan_targets(
                    config
                ),
                timeout=10,
            )

        assert err is None
        assert hosts == ["10.0.0.1"]
