import pytest
from unittest.mock import AsyncMock, patch
from services.phantom_wallet import PhantomWallet
from utils.logger import BotLogger
from solders.transaction import Transaction

@pytest.fixture
def phantom_wallet():
    """
    Test Fixture für PhantomWallet-Instanz.
    """
    logger = BotLogger()
    private_key = "4NwMH9qEP5gYdpHNxhSgRh4e5V4LrHvG5uKhKHoKHjYvGmZE3wsxqNcMbpuuT5GoAiCczSuXkPvhQEqxwQpvZXJu"  # Example private key for testing
    return PhantomWallet(private_key, rpc_url="https://api.mainnet-beta.solana.com", logger=logger)

@pytest.mark.asyncio
async def test_connect_success(phantom_wallet):
    """
    Test für erfolgreiche Wallet-Verbindung.
    """
    with patch("services.phantom_wallet.AsyncClient.__init__", return_value=None) as mock_client:
        mock_client.return_value.connect = AsyncMock(return_value=True)
        connected = await phantom_wallet.connect()
        assert connected is True
        assert phantom_wallet.is_connected() is True

@pytest.mark.asyncio
async def test_connect_failure(phantom_wallet):
    """
    Test für fehlgeschlagene Wallet-Verbindung.
    """
    with patch("services.phantom_wallet.AsyncClient.connect", side_effect=Exception("Verbindungsfehler")):
        connected = await phantom_wallet.connect()
        assert connected is False
        assert phantom_wallet.is_connected() is False

@pytest.mark.asyncio
async def test_get_balance_success(phantom_wallet):
    """
    Test für erfolgreiche Balance-Abrufung.
    """
    mock_response = AsyncMock()
    mock_response.value = 1000000000  # 1 SOL in Lamports

    with patch.object(phantom_wallet.client, "get_balance", return_value=mock_response):
        balance = await phantom_wallet.get_balance()
        assert balance == 1.0  # 1 SOL

@pytest.mark.asyncio
async def test_get_balance_failure(phantom_wallet):
    """
    Test für fehlgeschlagene Balance-Abrufung.
    """
    with patch("services.phantom_wallet.AsyncClient.get_balance", side_effect=Exception("Balance-Fehler")):
        balance = await phantom_wallet.get_balance()
        assert balance == 0.0

@pytest.mark.asyncio
async def test_sign_transaction_success(phantom_wallet):
    """
    Test für erfolgreiche Transaktionssignierung.
    """
    transaction = Transaction()
    with patch("services.phantom_wallet.Transaction.sign", return_value=transaction):
        signed_transaction = await phantom_wallet.sign_transaction(transaction)
        assert signed_transaction is not None

@pytest.mark.asyncio
async def test_sign_transaction_failure(phantom_wallet):
    """
    Test für fehlgeschlagene Transaktionssignierung.
    """
    transaction = Transaction()
    with patch("services.phantom_wallet.Transaction.sign", side_effect=Exception("Signaturfehler")):
        signed_transaction = await phantom_wallet.sign_transaction(transaction)
        assert signed_transaction is None

@pytest.mark.asyncio
async def test_send_transaction_success(phantom_wallet):
    """
    Test für erfolgreiche Transaktionsausführung.
    """
    mock_response = AsyncMock()
    mock_response.value = "mock_signature"

    with patch.object(phantom_wallet.client, "send_raw_transaction", return_value=mock_response):
        transaction = Transaction()
        signature = await phantom_wallet.send_transaction(transaction)
        assert signature == "mock_signature"

@pytest.mark.asyncio
async def test_send_transaction_failure(phantom_wallet):
    """
    Test für fehlgeschlagene Transaktionsausführung.
    """
    with patch.object(phantom_wallet.client, "send_raw_transaction", side_effect=Exception("Sende-Fehler")):
        transaction = Transaction()
        signature = await phantom_wallet.send_transaction(transaction)
        assert signature is None

@pytest.mark.asyncio
async def test_get_token_balance_success(phantom_wallet):
    """
    Test für erfolgreiche Token-Balance-Abrufung.
    """
    mock_response = {
        "value": [
            {
                "account": {
                    "data": {
                        "parsed": {
                            "info": {
                                "tokenAmount": {"uiAmount": 10.0}  # 10 Token
                            }
                        }
                    }
                }
            }
        ]
    }

    with patch("services.phantom_wallet.AsyncClient.get_token_accounts_by_owner", return_value=AsyncMock(value=mock_response)):
        balance = await phantom_wallet.get_token_balance("test_token_address")
        assert balance == 10.0

@pytest.mark.asyncio
async def test_get_token_balance_failure(phantom_wallet):
    """
    Test für fehlgeschlagene Token-Balance-Abrufung.
    """
    with patch("services.phantom_wallet.AsyncClient.get_token_accounts_by_owner", side_effect=Exception("Token Balance Fehler")):
        balance = await phantom_wallet.get_token_balance("test_token_address")
        assert balance == 0.0
