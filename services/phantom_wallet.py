import base58
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.rpc.types import TxOpts
from solana.system_program import TransferParams, transfer
from solana.publickey import PublicKey
from typing import Dict, Any, Optional, List
from utils.logger import BotLogger


class PhantomWallet:
    """
    Integration für Phantom Wallet zur Ausführung von Solana-Transaktionen.
    """

    def __init__(self, private_key: str, rpc_url: str = "https://api.mainnet-beta.solana.com", logger: Optional[BotLogger] = None):
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

    async def connect(self) -> bool:
        """
        Verbindet mit dem Solana Netzwerk.

        Returns:
            True wenn erfolgreich verbunden
        """
        try:
            await self.client.is_connected()
            self.logger.info("Wallet erfolgreich verbunden")
            return True
        except Exception as e:
            self.logger.error(f"Verbindungsfehler: {str(e)}")
            return False

    async def disconnect(self):
        """
        Trennt die Verbindung zum Solana Netzwerk.
        """
        try:
            await self.client.close()
            self.logger.info("Wallet-Verbindung getrennt")
        except Exception as e:
            self.logger.error(f"Fehler beim Trennen der Verbindung: {str(e)}")

    async def get_balance(self) -> float:
        """
        Ruft den aktuellen SOL-Saldo der Wallet ab.

        Returns:
            Wallet-Saldo in SOL
        """
        try:
            response = await self.client.get_balance(self.public_key)
            if response.value is not None:
                sol_balance = response.value / 1e9  # Konvertierung in SOL
                self.logger.info(f"Wallet-Saldo: {sol_balance:.6f} SOL")
                return sol_balance
            return 0.0
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
            token_program_id = PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
            response = await self.client.get_token_accounts_by_owner(
                self.public_key,
                token_program_id
            )

            accounts = response.value
            for account in accounts:
                account_info = await self.client.get_account_info(account.pubkey)
                account_data = await self.client.get_token_account_balance(account.pubkey)
                if account_data.value and str(account_info.value.owner) == token_address:
                    balance = float(account_data.value.ui_amount or 0)
                    self.logger.info(f"Token Balance ({token_address}): {balance:.6f}")
                    return balance
            return 0.0
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Token-Balances für {token_address}: {str(e)}")
            return 0.0

    async def send_transaction(self, transaction: Transaction) -> Optional[str]:
        """
        Signiert und sendet eine Transaktion.

        Args:
            transaction: Solana-Transaktion

        Returns:
            Transaktionssignatur als String oder None bei Fehler
        """
        try:
            transaction.sign(self.keypair)
            opts = TxOpts(skip_preflight=True)
            response = await self.client.send_transaction(
                transaction, 
                self.keypair,
                opts=opts
            )
            if response.value:
                signature = str(response.value)  # Konvertierung zu String
                self.logger.info(f"Transaktion erfolgreich gesendet: {signature}")
                return signature
            self.logger.error("Fehler: Keine Transaktionssignatur erhalten")
            return None
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Transaktion: {str(e)}")
            return None

    async def transfer_sol(self, recipient: str, amount: float) -> Optional[str]:
        """
        Überweist SOL an eine andere Adresse.

        Args:
            recipient: Empfangsadresse (PublicKey als String)
            amount: Betrag in SOL

        Returns:
            Transaktionssignatur oder None bei Fehler
        """
        try:
            lamports = int(amount * 1e9)  # Konvertierung in Lamports
            transaction = Transaction()
            transaction.add(
                transfer(
                    TransferParams(
                        from_pubkey=self.public_key,
                        to_pubkey=PublicKey(recipient),
                        lamports=lamports
                    )
                )
            )
            return await self.send_transaction(transaction)
        except Exception as e:
            self.logger.error(f"Fehler bei SOL-Überweisung an {recipient}: {str(e)}")
            return None

    async def get_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Ruft die letzten Transaktionen der Wallet ab.

        Args:
            limit: Maximale Anzahl der Transaktionen

        Returns:
            Liste der letzten Transaktionen
        """
        try:
            response = await self.client.get_signatures_for_address(self.public_key, limit=limit)
            if response.value:
                transactions = [{
                    'signature': tx.signature,
                    'slot': tx.slot,
                    'err': tx.err,
                    'memo': tx.memo,
                    'blockTime': tx.block_time,
                } for tx in response.value]
                self.logger.info(f"{len(transactions)} Transaktionen gefunden")
                return transactions
            return []
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Transaktionshistorie: {str(e)}")
            return []