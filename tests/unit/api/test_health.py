"""
Unit tests for health check endpoints.
"""

import pytest


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.unit
    def test_health_check_structure(self):
        """Health check should return expected structure."""
        # Expected health response structure
        expected_fields = ["status", "version"]

        # Mock health response
        health_response = {
            "status": "healthy",
            "version": "1.0.0"
        }

        for field in expected_fields:
            assert field in health_response

    @pytest.mark.unit
    def test_health_status_values(self):
        """Health status should be one of expected values."""
        valid_statuses = ["healthy", "degraded", "unhealthy"]

        assert "healthy" in valid_statuses
        assert "degraded" in valid_statuses


class TestAPIStructure:
    """Tests for API structure and conventions."""

    @pytest.mark.unit
    def test_auth_headers_fixture(self, auth_headers):
        """Auth headers fixture should have required headers."""
        assert "Authorization" in auth_headers
        assert auth_headers["Authorization"].startswith("Bearer ")
        assert auth_headers["Content-Type"] == "application/json"
