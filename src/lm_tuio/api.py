"""Engine for handling remote LMS endpoint connections.

Uses async HTTPX clients for server heartbeat checks (HEAD only) and performing API actions.
"""

import asyncio

import httpx
from pydantic import ValidationError

from lm_tuio.models import ModelInfo, ModelListResponse

# NOTE: Using LM Studio Native v1 REST API endpoints (/api/v1/[api_action]) for more robust server functionality.
#       OpenAI compatible endpoints (/v1/[api_action]) are primarily for inference.

API_TIMEOUT: float = 2.0
UNLOAD_TIMEOUT: float = 10.0

api_action: dict[str, str] = {
    "models": "/api/v1/models",
    "load": "/api/v1/models/load",
    "unload": "/api/v1/models/unload",
    "download": "/api/v1/models/download",
    "dl_progress": "/api/v1/models/download/status",
}


async def fetch_available_models(
    ip: str, port: int, timeout: float = API_TIMEOUT
) -> tuple[list[ModelInfo] | None, str | None]:
    """
    Calls LM Studio /api/v1/models API to list installed models, does not describe model load state
    Returns tuple: (List of ModelInfo objects, err)
    """
    server_url: str = f"http://{ip}:{port}{api_action['models']}"

    async with httpx.AsyncClient() as client:
        try:
            response: httpx.Response = await client.get(server_url, timeout=timeout)
            response.raise_for_status()
            raw_json: dict = response.json()
            validated_data: ModelListResponse = ModelListResponse.model_validate(
                raw_json
            )
            return validated_data.models, None

        except httpx.HTTPStatusError as e:
            return None, f"API returned error code: {e.response.status_code}"
        except httpx.RequestError as e:
            return None, f"Network request failed: {e}"
        except ValidationError as e:
            return None, f"Unexpected API response format: {e}"
        except Exception as e:
            return None, f"Unknown error fetching models: {e}"


async def unload_model_instances(
    ip: str, port: int, instance_ids: list[str]
) -> tuple[bool, str | None]:
    """Send one or more model instances to be unloaded via LMS API /api/v1/unload endpoint."""
    if not instance_ids:
        return True, None

    server_url: str = f"http://{ip}:{port}{api_action['unload']}"
    headers: dict = {"Content-Type": "application/json"}

    async def _unload_single(client: httpx.AsyncClient, inst_id: str) -> None:
        payload = {"instance_id": inst_id}
        resp = await client.post(url=server_url, json=payload, headers=headers)

        if resp.status_code not in (200, 204):
            raise RuntimeError(
                f"Failed to unload '{inst_id}' (HTTP {resp.status_code}): {resp.text}"
            )

    try:
        timeout = httpx.Timeout(UNLOAD_TIMEOUT)
        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = [_unload_single(client, inst_id) for inst_id in instance_ids]
            await asyncio.gather(*tasks)
            return True, None

    except Exception as e:
        return False, str(e)


async def check_server_status(ip: str, port: int, timeout: float = API_TIMEOUT) -> bool:
    """Lightweight http ping to LMS server endpoint"""
    server_url: str = f"http://{ip}:{port}{api_action['models']}"

    async with httpx.AsyncClient() as client:
        try:
            response: httpx.Response = await client.head(server_url, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False
