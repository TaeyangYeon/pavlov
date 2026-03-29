"""
Integration tests for Position API endpoints.
Tests actual HTTP endpoints with real test database.
"""

from decimal import Decimal

import pytest


class TestPositionAPI:
    """Integration tests for position API endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_position_returns_201(self, async_client):
        """Test POST /positions/ returns 201 with correct data."""
        payload = {
            "ticker": "AAPL",
            "market": "US",
            "entries": [
                {
                    "price": "150.00",
                    "quantity": "10",
                    "entered_at": "2024-01-02T10:00:00"
                }
            ]
        }

        response = await async_client.post("/api/v1/positions/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["market"] == "US"
        assert data["avg_price"] == "150.0000"
        assert data["status"] == "open"
        assert len(data["entries"]) == 1
        assert data["entries"][0]["price"] == "150.00"
        assert data["entries"][0]["quantity"] == "10"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_multi_entry_calculates_avg(self, async_client):
        """Test multi-entry position calculates weighted average correctly."""
        # price=100*10 + price=90*5 → avg=96.6667
        payload = {
            "ticker": "GOOGL",
            "market": "US",
            "entries": [
                {
                    "price": "100.00",
                    "quantity": "10",
                    "entered_at": "2024-01-01T10:00:00"
                },
                {
                    "price": "90.00",
                    "quantity": "5",
                    "entered_at": "2024-01-02T10:00:00"
                }
            ]
        }

        response = await async_client.post("/api/v1/positions/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["ticker"] == "GOOGL"

        # Expected: (100*10 + 90*5) / 15 = 1450/15 = 96.6667
        expected_avg = Decimal("96.6667")
        assert Decimal(data["avg_price"]) == expected_avg
        assert len(data["entries"]) == 2

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_positions_returns_open_only(self, async_client):
        """Test GET /positions/ returns only open positions."""
        # Create an open position
        open_payload = {
            "ticker": "TSLA",
            "market": "US",
            "entries": [
                {
                    "price": "200.00",
                    "quantity": "5",
                    "entered_at": "2024-01-01T10:00:00"
                }
            ]
        }

        # Create position
        create_response = await async_client.post("/api/v1/positions/", json=open_payload)
        assert create_response.status_code == 201
        position_id = create_response.json()["id"]

        # List positions (should include the open position)
        list_response = await async_client.get("/api/v1/positions/")
        assert list_response.status_code == 200
        positions = list_response.json()

        # Should have at least our created position
        assert len(positions) >= 1
        tesla_positions = [p for p in positions if p["ticker"] == "TSLA"]
        assert len(tesla_positions) == 1
        assert tesla_positions[0]["status"] == "open"

        # Close the position
        delete_response = await async_client.delete(f"/api/v1/positions/{position_id}")
        assert delete_response.status_code == 204

        # List positions again (should not include closed position)
        list_response_after = await async_client.get("/api/v1/positions/")
        assert list_response_after.status_code == 200
        positions_after = list_response_after.json()

        # Should have one fewer position
        assert len(positions_after) == len(positions) - 1
        tesla_positions_after = [p for p in positions_after if p["ticker"] == "TSLA"]
        assert len(tesla_positions_after) == 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_add_entry_recalculates_avg(self, async_client):
        """Test PATCH /positions/{id}/entries recalculates avg_price."""
        # Create initial position
        initial_payload = {
            "ticker": "NVDA",
            "market": "US",
            "entries": [
                {
                    "price": "100.00",
                    "quantity": "10",
                    "entered_at": "2024-01-01T10:00:00"
                }
            ]
        }

        # Create position
        create_response = await async_client.post("/api/v1/positions/", json=initial_payload)
        assert create_response.status_code == 201
        position_id = create_response.json()["id"]
        initial_avg = create_response.json()["avg_price"]
        assert initial_avg == "100.0000"

        # Add new entry
        new_entry = {
            "price": "80.00",
            "quantity": "10",
            "entered_at": "2024-01-02T10:00:00"
        }

        add_response = await async_client.patch(
            f"/api/v1/positions/{position_id}/entries",
            json=new_entry
        )
        assert add_response.status_code == 200

        updated_data = add_response.json()
        assert len(updated_data["entries"]) == 2

        # Expected new avg: (100*10 + 80*10) / 20 = 1800/20 = 90.0000
        expected_new_avg = Decimal("90.0000")
        assert Decimal(updated_data["avg_price"]) == expected_new_avg

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_position_by_id(self, async_client):
        """Test GET /positions/{id} returns specific position."""
        payload = {
            "ticker": "AMZN",
            "market": "US",
            "entries": [
                {
                    "price": "150.00",
                    "quantity": "3",
                    "entered_at": "2024-01-01T10:00:00"
                }
            ]
        }

        # Create position
        create_response = await async_client.post("/api/v1/positions/", json=payload)
        assert create_response.status_code == 201
        position_id = create_response.json()["id"]

        # Get position by ID
        get_response = await async_client.get(f"/api/v1/positions/{position_id}")
        assert get_response.status_code == 200

        position_data = get_response.json()
        assert position_data["id"] == position_id
        assert position_data["ticker"] == "AMZN"
        assert position_data["avg_price"] == "150.0000"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_nonexistent_position_returns_404(self, async_client):
        """Test GET /positions/{id} returns 404 for nonexistent position."""
        nonexistent_id = "00000000-0000-0000-0000-000000000999"

        response = await async_client.get(f"/api/v1/positions/{nonexistent_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Position not found"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_add_entry_to_nonexistent_position_returns_404(self, async_client):
        """Test PATCH /positions/{id}/entries returns 404 for nonexistent position."""
        nonexistent_id = "00000000-0000-0000-0000-000000000999"
        new_entry = {
            "price": "100.00",
            "quantity": "5",
            "entered_at": "2024-01-01T10:00:00"
        }

        response = await async_client.patch(
            f"/api/v1/positions/{nonexistent_id}/entries",
            json=new_entry
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Position not found"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_close_nonexistent_position_returns_404(self, async_client):
        """Test DELETE /positions/{id} returns 404 for nonexistent position."""
        nonexistent_id = "00000000-0000-0000-0000-000000000999"

        response = await async_client.delete(f"/api/v1/positions/{nonexistent_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Position not found"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_position_validation_error(self, async_client):
        """Test POST /positions/ returns 422 for invalid data."""
        invalid_payload = {
            "ticker": "",  # Invalid: empty ticker
            "market": "US",
            "entries": []  # Invalid: empty entries list
        }

        response = await async_client.post("/api/v1/positions/", json=invalid_payload)

        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        # Should have validation errors for ticker and entries
        assert len(error_data["detail"]) >= 2
