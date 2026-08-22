"""Scans provided network for active LM Studio API endpoints.

User provided IP and port information via CLI or server change screen.
Uses ./config.py AppConfig structure for parallel network checks.
Default scan parameters: 192.168.1.0/24, port 1234.
"""

import asyncio
import ipaddress

from lm_tuio.config import AppConfig


async def check_host(ip: str, port: int, timeout: float = 2.0) -> str | None:
    """
    Attempts a TCP connection to specific IP and port.
    Returns IP string if success, None on fail.
    """

    try:
        coro = asyncio.open_connection(ip, port)
        _reader, writer = await asyncio.wait_for(coro, timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return ip

    except (TimeoutError, OSError, ConnectionRefusedError):
        return None


async def scan_targets(config: AppConfig) -> tuple[list[str] | None, str | None]:
    """Scans target in AppConfig concurrently."""

    network: ipaddress.IPv4Network = ipaddress.IPv4Network(config.target, strict=False)
    tasks: list[asyncio.Task[str | None]] = []

    if config.is_network:
        for host in network.hosts():
            task: asyncio.Task[str | None] = asyncio.create_task(
                check_host(str(host), config.port)
            )
            tasks.append(task)
    else:
        single_ip: str = str(network.network_address)
        task: asyncio.Task[str | None] = asyncio.create_task(
            check_host(single_ip, config.port)
        )
        tasks.append(task)

    results: list[str | None] = await asyncio.gather(*tasks)
    active_hosts: list[str] = [ip for ip in results if ip is not None]

    if not active_hosts:
        return None, f"No active endpoints found on {config.target}:{config.port}"

    return active_hosts, None
