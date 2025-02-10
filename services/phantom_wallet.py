import base58
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.rpc.types import TxOpts
from typing import Dict, Any
from utils.logger import BotLogger

class PhantomWallet:
    """
    Integration für Phantom Wallet zur Ausführung von Solana-Transaktionen.
    """

    def __init__(self, private_key: str, rpc_url: str = "https://api.mainnet-beta.solana.com", logger: BotLogger = None):
        """
        Initialisiert die PhantomWallet-Klasse.

        Args:
            private_key: Private Key der Phantom Wallet (Base58-Format)
            rpc_url: Solana RPC-URL
            logger: Logger-Instanz für Debugging und Fehler
        """
        self.client = AsyncClient(rpc_url)
        self.keypair = Keypair.from_secret_key(base58.b58decode(private_key))
        self.public_key = self.keypair.public_key
        self.logger = logger or BotLogger()

    async def get_balance(self) -> float:
        """
        Ruft den aktuellen SOL-Saldo der Wallet ab.

        Returns:
            Wallet-Saldo in SOL
        """
        try:
            balance = await self.client.get_balance(self.public_key)
            sol_balance = balance['result']['value'] / 1e9  # Konvertierung in SOL
            self.logger.info(f"Wallet-Saldo: {sol_balance} SOL")
            return sol_balance
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Wallet-Saldos: {str(e)}")
            return 0.0

    async def get_token_balance(self, token_address: str) -> float:
        """
        Ruft den Balance eines spezifischen Tokens ab.

        Args:
            token_address: Token Mint Address

        Returns:
            Token Balance oder 0 bei Fehler
        """
        try:
            token_accounts = await self.client.get_token_accounts_by_owner(
                self.public_key,
                {"mint": token_address}
            )
            
            if token_accounts.value:
                balance = float(token_accounts.value[0].account.data.parsed["info"]["tokenAmount"]["uiAmount"])
                self.logger.info(f"Token Balance: {balance}")
                return balance
            return 0.0
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Token Balances: {str(e)}")
            return 0.0

    async def send_transaction(self, transaction: Transaction) -> str:
        """
        Signiert und sendet eine Transaktion.

        Args:
            transaction: Solana-Transaktion

        Returns:
            Transaktionssignatur
        """
        try:
            transaction.sign(self.keypair)
            response = await self.client.send_transaction(transaction, self.keypair, opts=TxOpts(skip_preflight=True))
            tx_signature = response.get('result')
            self.logger.info(f"Transaktion erfolgreich gesendet: {tx_signature}")
            return tx_signature
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Transaktion: {str(e)}")
            return ""

    async def transfer_sol(self, recipient: str, amount: float) -> str:
        """
        Überweist SOL an eine andere Adresse.

        Args:
            recipient: Empfangsadresse
            amount: Betrag in SOL

        Returns:
            Transaktionssignatur
        """
        try:
            lamports = int(amount * 1e9)  # Konvertierung in Lamports
            transaction = Transaction()
            transaction.add(
                self.client.get_transfer_txn(self.public_key, recipient, lamports)
            )
            return await self.send_transaction(transaction)
        except Exception as e:
            self.logger.error(f"Fehler bei SOL-Überweisung: {str(e)}")
            return ""

    async def get_recent_transactions(self, limit: int = 10) -> Dict[str, Any]:
        """
        Ruft die letzten Transaktionen der Wallet ab.

        Args:
            limit: Maximale Anzahl der Transaktionen

        Returns:
            Liste der letzten Transaktionen
        """
        try:
            transaction_history = await self.client.get_confirmed_signatures_for_address2(
                self.public_key, limit=limit
            )
            self.logger.info(f"{len(transaction_history['result'])} Transaktionen gefunden.")
            return transaction_history['result']
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Transaktionshistorie: {str(e)}")
            return {}

    async def close(self):
        """
        Schließt die RPC-Verbindung.
        """
        await self.client.close()
        self.logger.info("RPC-Verbindung geschlossen.")
