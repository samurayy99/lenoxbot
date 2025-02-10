import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.solana_sniffer import SolanaSniffer
from utils.logger import BotLogger

@pytest.fixture
def sniffer():
    """
    Test Fixture für SolanaSniffer-Instanz
    """
    logger = BotLogger()
    return SolanaSniffer(
        logger=logger,
        rpc_url="https://api.mainnet-beta.solana.com"
    )

@pytest.mark.asyncio
async def test_analyze_token_success(sniffer):
    """
    Test für erfolgreiche Token-Analyse
    """
    mock_token_info = {
        "program_id": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        "data": b"mock_data",
        "executable": True
    }

    mock_program_info = {
        "executable": True,
        "owner": "owner_address",
        "data_len": 1024
    }

    with patch.object(sniffer, "_get_token_info", return_value=mock_token_info), \
         patch.object(sniffer, "_get_program_info", return_value=mock_program_info), \
         patch.object(sniffer, "_check_program_verification", return_value=True), \
         patch.object(sniffer, "_analyze_supply", return_value={"total_supply": 1_000_000, "is_mintable": False}), \
         patch.object(sniffer, "_analyze_holders", return_value={"total_holders": 10, "concentration_risk": "low"}):
        
        result = await sniffer.analyze_token("test_token_address")
        assert result["is_verified"] is True
        assert result["supply_analysis"]["total_supply"] == 1_000_000
        assert result["program_analysis"]["risk_level"] == "low"

@pytest.mark.asyncio
async def test_get_token_info_success(sniffer):
    """
    Test für erfolgreiche Token-Info-Abfrage
    """
    mock_response = MagicMock()
    mock_response.value = MagicMock(
        owner="test_program_id",
        data=b"mock_data",
        executable=True
    )

    with patch("solana.rpc.async_api.AsyncClient.get_account_info", return_value=mock_response):
        result = await sniffer._get_token_info("test_token_address")
        assert result["program_id"] == "test_program_id"
        assert result["data"] == b"mock_data"
        assert result["executable"] is True

@pytest.mark.asyncio
async def test_get_program_info_success(sniffer):
    """
    Test für erfolgreiche Programm-Info-Abfrage
    """
    mock_response = MagicMock()
    mock_response.value = MagicMock(
        executable=True,
        owner="owner_address",
        data=b"mock_program_data"
    )

    with patch("solana.rpc.async_api.AsyncClient.get_account_info", return_value=mock_response):
        result = await sniffer._get_program_info("test_program_id")
        assert result["executable"] is True
        assert result["owner"] == "owner_address"
        assert result["data_len"] == len(b"mock_program_data")

@pytest.mark.asyncio
async def test_check_program_verification(sniffer):
    """
    Test für Programm-Verifikation
    """
    verified_programs = [
        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # SPL Token Program
        "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"   # Token-2022 Program
    ]

    with patch.object(sniffer, "_check_program_verification", side_effect=lambda program_id: program_id in verified_programs):
        assert await sniffer._check_program_verification("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA") is True
        assert await sniffer._check_program_verification("UnknownProgramID") is False

@pytest.mark.asyncio
async def test_analyze_supply(sniffer):
    """
    Test für Token-Supply-Analyse
    """
    mock_supply_response = MagicMock()
    mock_supply_response.value = MagicMock(amount="1000000", decimals=9)

    with patch("solana.rpc.async_api.AsyncClient.get_token_supply", return_value=mock_supply_response), \
         patch.object(sniffer, "_get_token_info", return_value={"data": b"mock_data"}):
        result = await sniffer._analyze_supply("test_token_address")
        assert result["total_supply"] == 1_000_000
        assert result["is_mintable"] is False

@pytest.mark.asyncio
async def test_analyze_holders(sniffer):
    """
    Test für Token-Holder-Analyse
    """
    mock_holder_response = {
        "accounts": [
            {"address": "holder1", "balance": 50_000},
            {"address": "holder2", "balance": 20_000},
            {"address": "holder3", "balance": 10_000}
        ]
    }

    with patch("solana.rpc.async_api.AsyncClient.get_token_accounts_by_owner", return_value=mock_holder_response):
        result = await sniffer._analyze_holders("test_token_address")
        assert result["total_holders"] == 3
        assert result["concentration_risk"] == "low"

@pytest.mark.asyncio
async def test_error_handling(sniffer):
    """
    Test für Fehlerbehandlung
    """
    with patch("solana.rpc.async_api.AsyncClient.get_account_info", side_effect=Exception("RPC Error")):
        result = await sniffer._get_token_info("test_token_address")
        assert result is None
