import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from services.dexscreener import DexScreener
from utils.logger import BotLogger

@pytest.fixture
def dexscreener():
    logger = BotLogger()
    filters = {
        "liquidity_min": 20_000,
        "market_cap": {"min": 100_000, "max": 2_000_000},
        "hourly_transactions": 200,
        "buy_sell_ratio": 1.5
    }
    return DexScreener(logger, filters)


@pytest.mark.asyncio
async def test_fetch_pairs_success(dexscreener):
    mock_response = {"pairs": [{"baseToken": {"symbol": "SOL", "address": "address_1"}, "liquidity": {"usd": 60000}}]}
    with patch("aiohttp.ClientSession.get", new=AsyncMock(return_value=AsyncMock(status=200, json=AsyncMock(return_value=mock_response)))):
        result = await dexscreener.fetch_pairs("solana")
        assert len(result) > 0
        assert result[0]["baseToken"]["symbol"] == "SOL"


@pytest.mark.asyncio
async def test_fetch_pairs_failure(dexscreener):
    with patch("aiohttp.ClientSession.get", new=AsyncMock(return_value=AsyncMock(status=500))):
        result = await dexscreener.fetch_pairs("solana")
        assert result == []


def test_filter_pairs(dexscreener):
    test_pairs = [
        {"liquidity_usd": 25000, "market_cap": 150000, "hourly_tx": 250, "buy_sell_ratio": 2.0},
        {"liquidity_usd": 15000, "market_cap": 150000, "hourly_tx": 250, "buy_sell_ratio": 2.0},  # Invalid liquidity
        {"liquidity_usd": 25000, "market_cap": 50000, "hourly_tx": 250, "buy_sell_ratio": 2.0},   # Invalid market cap
    ]
    filtered = dexscreener._filter_opportunities(test_pairs)
    assert len(filtered) == 1
    assert filtered[0]["liquidity_usd"] >= dexscreener.filters["liquidity_min"]


@pytest.mark.asyncio
async def test_get_token_price(dexscreener):
    mock_response = {"pairs": [{"priceUsd": "1.23", "liquidity": {"usd": 50000}}]}
    with patch("aiohttp.ClientSession.get", new=AsyncMock(return_value=AsyncMock(status=200, json=AsyncMock(return_value=mock_response)))):
        price = await dexscreener.get_token_price("test_token_address")
        assert price == 1.23


@pytest.mark.asyncio
async def test_error_handling(dexscreener):
    with patch("aiohttp.ClientSession.get", new=AsyncMock(return_value=AsyncMock(status=404))):
        opportunities = await dexscreener.get_trading_opportunities("solana")
        assert opportunities == []

        price = await dexscreener.get_token_price("test_token_address")
        assert price == 0.0
