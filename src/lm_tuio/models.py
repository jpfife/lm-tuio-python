"""Establishes data structures for LMS Native v1 REST API GET Models response.

Optional JSON fields from API response may be 'None'.
"""

from pydantic import BaseModel


class QuantizationInfo(BaseModel):
    """Model quantization information."""

    name: str
    bits_per_weight: int | float | None = None


class ModelInfo(BaseModel):
    """Single model block returned by LM Studio Native v1 REST API."""

    type: str
    publisher: str
    key: str  # Unique ID for API calls
    display_name: str
    architecture: str | None = None
    size_bytes: int
    params_string: str | None = None
    max_context_length: int
    format: str
    quantization: QuantizationInfo | None = None


class ModelListResponse(BaseModel):
    """Top-level JSON response from /api/v1/models endpoint."""

    models: list[ModelInfo]
