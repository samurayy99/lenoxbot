import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.system_program import transfer, TransferParams
from solders.message import Message
from solana.rpc.async_api import AsyncClient
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
        self.keypair = Keypair.from_bytes(base58.b58decode(private_key))
        self.public_key = self.keypair.pubkey()
        self.logger = logger or BotLogger()

    async def connect(self) -> bool:
        """Verbindet mit dem Solana Netzwerk."""
        try:
            await self.client.is_connected()
            self.logger.info("Wallet erfolgreich verbunden")
            return True
        except Exception as e:
            self.logger.error(f"Verbindungsfehler: {str(e)}")
            return False

    async def disconnect(self):
        """Trennt die Verbindung zum Solana Netzwerk."""
        try:
            await self.client.close()
            self.logger.info("Wallet-Verbindung getrennt")
        except Exception as e:
            self.logger.error(f"Fehler beim Trennen der Verbindung: {str(e)}")

    async def get_balance(self) -> float:
        """Ruft den aktuellen SOL-Saldo der Wallet ab."""
        try:
            response = await self.client.get_balance(self.public_key)
            sol_balance = response.value / 1e9 if response.value is not None else 0.0
            self.logger.info(f"Wallet-Saldo: {sol_balance:.6f} SOL")
            return sol_balance
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Wallet-Saldos: {str(e)}")
            return 0.0

    async def send_transaction(self, transaction: Transaction) -> Optional[str]:
        """
        Sendet eine bereits erstellte und signierte Transaktion.

        Args:
            transaction: Eine Transaktion, die mit Transaction.new(...) erzeugt und signiert wurde.

        Returns:
            Transaktionssignatur als String oder None bei Fehler.
        """
        try:
            response = await self.client.send_raw_transaction(bytes(transaction))
            if response.value:
                signature = str(response.value)
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
            Transaktionssignatur oder None bei Fehler.
        """
        try:
            lamports = int(amount * 1e9)  # Umwandlung von SOL in Lamports
            blockhash = (await self.client.get_latest_blockhash()).value.blockhash
            instruction = transfer(
                TransferParams(
                    from_pubkey=self.public_key,
                    to_pubkey=Pubkey.from_string(recipient),
                    lamports=lamports
                )
            )
            
            message = Message.new_with_blockhash(
                instructions=[instruction],
                payer=self.public_key,
                recent_blockhash=blockhash
            )
            
            tx = Transaction.new_from_message(
                message=message,
                signer_keypairs=[self.keypair]
            )
            
            return await self.send_transaction(tx)
        except Exception as e:
            self.logger.error(f"Fehler bei SOL-Überweisung an {recipient}: {str(e)}")
            return None

    async def get_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Ruft die letzten Transaktionen der Wallet ab.

        Args:
            limit: Maximale Anzahl der Transaktionen

        Returns:
            Liste der letzten Transaktionen.
        """
        try:
            response = await self.client.get_signatures_for_address(self.public_key, limit=limit)
            transactions = [{
                'signature': tx.signature,
                'slot': tx.slot,
                'err': tx.err,
                'memo': tx.memo,
                'blockTime': tx.block_time,
            } for tx in response.value] if response.value else []
            self.logger.info(f"{len(transactions)} Transaktionen gefunden")
            return transactions
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Transaktionshistorie: {str(e)}")
            return []