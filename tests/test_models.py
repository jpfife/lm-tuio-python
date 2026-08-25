"""Tests for ../src/lm_tuio/models.py.

Tests format_bytes() and estimate_context_cache_memory().
"""

from lm_tuio.models import format_bytes, estimate_context_cache_memory


# ===== format_bytes =====


class TestFormatBytes:
    """Test the bytes-to-human-string conversion."""

    def test_zero(self) -> None:
        assert format_bytes(0) == "0 B"

    def test_exact_kb(self) -> None:
        assert format_bytes(1024) == "1K"

    def test_truncated_kb(self) -> None:
        # 2048 bytes = exactly 2 KB (not truncated — it's an exact multiple)
        assert format_bytes(2048) == "2K"

    def test_exact_mb(self) -> None:
        assert format_bytes(1024**2) == "1.00 MB"

    def test_fractional_mb(self) -> None:
        # 1536 KB = 1.5 MB → should be in MB tier (not GB, since < 1GB)
        result = format_bytes(1536 * 1024)
        assert result == "1.50 MB"

    def test_exact_gb(self) -> None:
        # 7*GB is exactly at the tier boundary — should be in GB tier (not TB)
        result = format_bytes(7 * 1024**3)
        assert result == "7.00 GB"

    def test_fractional_gb(self) -> None:
        # 7.5 GB → should be in GB tier (not TB)
        result = format_bytes(int(7.5 * 1024**3))
        assert result == "7.50 GB"

    def test_exact_tb(self) -> None:
        assert format_bytes(1024**4) == "1.00 TB"

    def test_fractional_tb(self) -> None:
        # 2.5 TB → should be in TB tier (not PB — no PB support)
        result = format_bytes(int(2.5 * 1024**4))
        assert result == "2.50 TB"

    def test_large_number(self) -> None:
        # 999.99 GB → should be in GB tier (not TB)
        result = format_bytes(int(999.99 * 1024**3))
        assert result == "999.99 GB"

    def test_just_over_gb_threshold(self) -> None:
        # Exactly 7 GB → should be tier1 (tier1 is < 7GB, so this is tier2)
        result = format_bytes(7 * 1024**3)
        assert result == "7.00 GB"

    def test_just_under_gb_threshold(self) -> None:
        # 6.999... GB → should be in GB tier (not MB)
        result = format_bytes(int(6.99 * 1024**3))
        assert result == "6.99 GB"


# ===== estimate_context_cache_memory =====


class TestEstimateContextCacheMemory:
    """Test the rough KV cache memory estimation."""

    def test_tier1_small_file(self) -> None:
        # 5 GB file → tier1 (32 layers, 4096 tokens)
        result = estimate_context_cache_memory(5 * 1024**3, 8192)
        expected = 8192 * (32 * 4096)
        assert result == expected

    def test_tier1_boundary(self) -> None:
        # Exactly 7 GB → tier2
        result = estimate_context_cache_memory(7 * 1024**3, 8192)
        expected = 8192 * (64 * 4096)
        assert result == expected

    def test_tier2_medium_file(self) -> None:
        # 20 GB file → tier2
        result = estimate_context_cache_memory(20 * 1024**3, 8192)
        expected = 8192 * (64 * 4096)
        assert result == expected

    def test_tier2_boundary(self) -> None:
        # Exactly 28 GB → tier3
        result = estimate_context_cache_memory(28 * 1024**3, 8192)
        expected = 8192 * (80 * 4096)
        assert result == expected

    def test_tier3_large_file(self) -> None:
        # 50 GB file → tier3
        result = estimate_context_cache_memory(50 * 1024**3, 8192)
        expected = 8192 * (80 * 4096)
        assert result == expected

    def test_zero_file(self) -> None:
        # Zero file size → tier1 (default path)
        result = estimate_context_cache_memory(0, 8192)
        expected = 8192 * (32 * 4096)
        assert result == expected

    def test_zero_context(self) -> None:
        # Zero context → should return 0 regardless of tier
        result = estimate_context_cache_memory(5 * 1024**3, 0)
        assert result == 0

    def test_exact_tier_boundary_minus_one_byte(self) -> None:
        # Just under the 7 GB boundary → still tier1
        result = estimate_context_cache_memory((7 * 1024**3) - 1, 8192)
        expected = 8192 * (32 * 4096)
        assert result == expected

    def test_exact_tier_boundary_plus_one_byte(self) -> None:
        # Just over the 7 GB boundary → tier2
        result = estimate_context_cache_memory((7 * 1024**3) + 1, 8192)
        expected = 8192 * (64 * 4096)
        assert result == expected

    def test_exact_tier_boundary_minus_one_byte_28gb(self) -> None:
        # Just under the 28 GB boundary → tier2
        result = estimate_context_cache_memory((28 * 1024**3) - 1, 8192)
        expected = 8192 * (64 * 4096)
        assert result == expected

    def test_exact_tier_boundary_plus_one_byte_28gb(self) -> None:
        # Just over the 28 GB boundary → tier3
        result = estimate_context_cache_memory((28 * 1024**3) + 1, 8192)
        expected = 8192 * (80 * 4096)
        assert result == expected
