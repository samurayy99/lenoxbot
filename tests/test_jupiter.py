import pytest
from unittest.mock import AsyncMock, patch
from services.jupiter import Jupiter
from utils.logger import BotLogger

@pytest.fixture
def jupiter():
    """
    Test Fixture für Jupiter-Instanz
    """
    logger = BotLogger()
    return Jupiter(logger)

@pytest.mark.asyncio
async def test_get_quote_success(jupiter):
    """
    Test für erfolgreiche Quote-Abrufung
    """
    mock_response = {
        "data": {
            "inputMint": "So11111111111111111111111111111111111111112",  # SOL
            "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "inAmount": 1000000000,  # 1 SOL
            "outAmount": 20000000,   # 20 USDC
            "priceImpactPct": 0.5,
            "slippageBps": 50,       # 0.5%
            "otherAmountThreshold": "19900000"
        }
    }

    with patch("aiohttp.ClientSession.get", new=AsyncMock(
        return_value=AsyncMock(
            status=200,
            json=AsyncMock(return_value=mock_response)
        )
    )):
        quote = await jupiter.get_quote(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            amount=1.0,
            slippage=0.5
        )
        
        assert quote["inputMint"] == "So11111111111111111111111111111111111111112"
        assert quote["outputMint"] == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        assert quote["inAmount"] == 1000000000
        assert quote["outAmount"] == 20000000
        assert quote["priceImpactPct"] == 0.5

@pytest.mark.asyncio
async def test_get_routes_success(jupiter):
    """
    Test für erfolgreiche Routen-Abrufung
    """
    mock_response = {
        "data": {
            "routes": [
                {
                    "marketInfos": [
                        {
                            "amm": "Raydium",
                            "label": "SOL-USDC",
                            "inputMint": "So11111111111111111111111111111111111111112",
                            "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                            "inAmount": "1000000000",
                            "outAmount": "20000000",
                            "priceImpactPct": 0.5,
                            "lpFee": {"amount": "3000000"}
                        }
                    ],
                    "outAmount": "20000000",
                    "priceImpactPct": 0.5
                }
            ]
        }
    }

    with patch("aiohttp.ClientSession.get", new=AsyncMock(
        return_value=AsyncMock(
            status=200,
            json=AsyncMock(return_value=mock_response)
        )
    )):
        routes = await jupiter.get_routes(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            amount=1.0
        )
        
        assert len(routes) > 0
        assert routes[0]["outAmount"] == "20000000"
        assert routes[0]["priceImpactPct"] == 0.5
        assert len(routes[0]["marketInfos"]) > 0

@pytest.mark.asyncio
async def test_execute_swap_success(jupiter):
    """
    Test für erfolgreiche Swap-Ausführung
    """
    mock_quote_response = {
        "data": {
            "quoteId": "test_quote_id",
            "swapTransaction": "encoded_transaction_data"
        }
    }

    mock_swap_response = {
        "success": True,
        "txid": "test_transaction_signature"
    }

    with patch("aiohttp.ClientSession.get", new=AsyncMock(
        return_value=AsyncMock(
            status=200,
            json=AsyncMock(return_value=mock_quote_response)
        )
    )), patch("aiohttp.ClientSession.post", new=AsyncMock(
        return_value=AsyncMock(
            status=200,
            json=AsyncMock(return_value=mock_swap_response)
        )
    )):
        result = await jupiter.execute_swap(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            amount=1.0,
            slippage=0.5
        )
        
        assert result["success"] is True
        assert result["txid"] == "test_transaction_signature"

@pytest.mark.asyncio
async def test_error_handling(jupiter):
    """
    Test für Fehlerbehandlung
    """
    # Quote Fehler
    with patch("aiohttp.ClientSession.get", new=AsyncMock(return_value=AsyncMock(status=500))):
        quote = await jupiter.get_quote(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            amount=1.0,
            slippage=0.5
        )
        assert quote == {}

    # Routes Fehler
    with patch("aiohttp.ClientSession.get", new=AsyncMock(return_value=AsyncMock(status=500))):
        routes = await jupiter.get_routes(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            amount=1.0
        )
        assert routes == []

    # Swap Fehler
    with patch("aiohttp.ClientSession.get", new=AsyncMock(return_value=AsyncMock(status=500))):
        result = await jupiter.execute_swap(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            amount=1.0,
            slippage=0.5
        )
        assert result == {"success": False, "error": "Quote fetch failed"}

@pytest.mark.asyncio
async def test_validation(jupiter):
    """
    Test für Input-Validierung
    """
    # Ungültige Amount
    with pytest.raises(ValueError):
        await jupiter.get_quote(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            amount=0,
            slippage=0.5
        )

    # Ungültiger Slippage
    with pytest.raises(ValueError):
        await jupiter.get_quote(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            amount=1.0,
            slippage=50  # Zu hoch
        )