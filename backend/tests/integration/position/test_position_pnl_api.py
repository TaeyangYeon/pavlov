"""
Integration tests for Position P&L API endpoints.
Tests actual HTTP endpoints with real test database.
"""


import pytest


class TestPositionPnLAPI:
    """Integration tests for position P&L API endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_position_pnl_returns_enriched_data(self, async_client):
        """Test GET /positions/{id}/pnl returns position with P&L calculations."""
        # Create a position first
        payload = {
            "ticker": "AAPL",
            "market": "US",
            "entries": [
                {
                    "price": "100.00",
                    "quantity": "10",
                    "entered_at": "2024-01-01T10:00:00"
                }
            ]
        }

        create_response = await async_client.post("/api/v1/positions/", json=payload)
        assert create_response.status_code == 201
        position_id = create_response.json()["id"]

        # Get position with P&L
        current_price = "120.00"
        pnl_response = await async_client.get(
            f"/api/v1/positions/{position_id}/pnl",
            params={"current_price": current_price}
        )

        assert pnl_response.status_code == 200
        data = pnl_response.json()

        # Assert basic position data preserved
        assert data["id"] == position_id
        assert data["ticker"] == "AAPL"
        assert data["market"] == "US"
        assert data["avg_price"] == "100.0000"

        # Assert P&L calculations
        assert data["current_price"] == current_price
        assert data["unrealized_pnl"] == "200.0000"  # (120-100) * 10
        assert data["unrealized_pnl_percent"] == "20.0000"  # (120-100)/100 * 100
        assert data["realized_pnl"] == "0.0000"
        assert data["total_pnl"] == "200.0000"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_position_pnl_with_loss(self, async_client):
        """Test P&L calculation with negative values (loss)."""
        # Create a position
        payload = {
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

        create_response = await async_client.post("/api/v1/positions/", json=payload)
        assert create_response.status_code == 201
        position_id = create_response.json()["id"]

        # Get position with P&L (price dropped)
        current_price = "150.00"
        pnl_response = await async_client.get(
            f"/api/v1/positions/{position_id}/pnl",
            params={"current_price": current_price}
        )

        assert pnl_response.status_code == 200
        data = pnl_response.json()

        # Assert P&L calculations for loss
        assert data["current_price"] == current_price
        assert data["unrealized_pnl"] == "-250.0000"  # (150-200) * 5
        assert data["unrealized_pnl_percent"] == "-25.0000"  # (150-200)/200 * 100
        assert data["total_pnl"] == "-250.0000"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_position_pnl_multi_entry_weighted_avg(self, async_client):
        """Test P&L calculation with multiple entries (weighted average)."""
        # Create position with multiple entries
        payload = {
            "ticker": "NVDA",
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

        create_response = await async_client.post("/api/v1/positions/", json=payload)
        assert create_response.status_code == 201
        position_id = create_response.json()["id"]

        # Get position with P&L
        current_price = "110.00"
        pnl_response = await async_client.get(
            f"/api/v1/positions/{position_id}/pnl",
            params={"current_price": current_price}
        )

        assert pnl_response.status_code == 200
        data = pnl_response.json()

        # Expected weighted avg: (100*10 + 90*5) / 15 = 96.6667
        assert data["avg_price"] == "96.6667"
        assert data["current_price"] == current_price

        # Expected P&L: 15 * (110 - 96.6667) = 15 * 13.3333 = 199.9995
        assert data["unrealized_pnl"] == "199.9995"
        assert data["unrealized_pnl_percent"] == "13.7931"  # 13.3333/96.6667 * 100

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_position_pnl_nonexistent_returns_404(self, async_client):
        """Test GET /positions/{id}/pnl returns 404 for nonexistent position."""
        nonexistent_id = "00000000-0000-0000-0000-000000000999"
        current_price = "100.00"

        response = await async_client.get(
            f"/api/v1/positions/{nonexistent_id}/pnl",
            params={"current_price": current_price}
        )

        assert response.status_code == 404
        assert "Position" in response.json()["detail"]
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_position_pnl_invalid_price_returns_422(self, async_client):
        """Test GET /positions/{id}/pnl returns 422 for invalid current_price."""
        # Create a position first
        payload = {
            "ticker": "AAPL",
            "market": "US",
            "entries": [
                {
                    "price": "100.00",
                    "quantity": "10",
                    "entered_at": "2024-01-01T10:00:00"
                }
            ]
        }

        create_response = await async_client.post("/api/v1/positions/", json=payload)
        assert create_response.status_code == 201
        position_id = create_response.json()["id"]

        # Test negative current_price
        negative_response = await async_client.get(
            f"/api/v1/positions/{position_id}/pnl",
            params={"current_price": "-10.00"}
        )
        assert negative_response.status_code == 422

        # Test zero current_price
        zero_response = await async_client.get(
            f"/api/v1/positions/{position_id}/pnl",
            params={"current_price": "0.00"}
        )
        assert zero_response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_position_pnl_missing_price_returns_422(self, async_client):
        """Test GET /positions/{id}/pnl returns 422 when current_price is missing."""
        # Create a position first
        payload = {
            "ticker": "AAPL",
            "market": "US",
            "entries": [
                {
                    "price": "100.00",
                    "quantity": "10",
                    "entered_at": "2024-01-01T10:00:00"
                }
            ]
        }

        create_response = await async_client.post("/api/v1/positions/", json=payload)
        assert create_response.status_code == 201
        position_id = create_response.json()["id"]

        # Request without current_price parameter
        response = await async_client.get(f"/api/v1/positions/{position_id}/pnl")

        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("current_price" in str(error) for error in error_detail)
