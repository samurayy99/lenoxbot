import aiohttp
from typing import Dict, Any, Optional
from utils.logger import BotLogger

class Jupiter:
    """
    Integration mit der Jupiter API v6 für Solana Token Swaps.
    Dokumentation: https://station.jup.ag/docs/apis/swap-api
    """

    def __init__(self, logger: BotLogger):
        self.BASE_URL = "https://quote-api.jup.ag/v6"
        self.logger = logger

    async def get_best_route(
        self,
        input_mint: str,
        output_mint: str,
        amount: float,
        slippage_bps: int = 50,  # 0.5% default slippage
        platform_fee_bps: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Holt die beste Swap-Route von Jupiter mit optimierten Parametern.
        """
        try:
            url = f"{self.BASE_URL}/quote"
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(int(amount)),
                "slippageBps": slippage_bps,
                "platformFeeBps": platform_fee_bps,
                "restrictIntermediateTokens": True,  # Für stabilere Routen
                "asLegacyTransaction": False  # Wir nutzen Versioned Transactions
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.info(f"Route gefunden mit Output Amount: {data.get('outAmount')}")
                        return data
                    else:
                        error_data = await response.text()
                        self.logger.error(f"Jupiter Quote API Error: {response.status} - {error_data}")
                        return None

        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Route: {str(e)}")
            return None

    async def execute_trade(
        self,
        quote_response: Dict[str, Any],
        wallet_public_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Erstellt und führt einen Swap basierend auf der Quote aus.
        """
        try:
            url = f"{self.BASE_URL}/swap"
            payload = {
                "quoteResponse": quote_response,
                "userPublicKey": wallet_public_key,
                "dynamicComputeUnitLimit": True,  # Optimierte CU Nutzung
                "dynamicSlippage": {
                    "maxBps": 300  # Max 3% slippage für höhere Erfolgsrate
                },
                "prioritizationFeeLamports": {
                    "priorityLevelWithMaxLamports": {
                        "maxLamports": 10000000,
                        "priorityLevel": "veryHigh"
                    }
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        swap_response = await response.json()
                        self.logger.info("Swap Transaktion erstellt")
                        return swap_response
                    else:
                        error_data = await response.text()
                        self.logger.error(f"Jupiter Swap API Error: {response.status} - {error_data}")
                        return None

        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Swap-Transaktion: {str(e)}")
            return None

    async def submit_transaction(self, transaction_payload: Dict[str, Any]) -> Optional[str]:
        """
        Sendet die Transaktion über Jupiters optimierten Transaction Sender.
        """
        try:
            url = "https://worker.jup.ag/send-transaction"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=transaction_payload,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        tx_id = result.get("txid")
                        self.logger.info(f"Transaktion erfolgreich gesendet: {tx_id}")
                        return tx_id
                    else:
                        error_data = await response.text()
                        self.logger.error(f"Transaction Submit Error: {response.status} - {error_data}")
                        return None

        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Transaktion: {str(e)}")
            return None

    async def get_token_price(self, token_mint: str) -> Optional[float]:
        """
        Holt den aktuellen Token-Preis in USDC.
        
        Args:
            token_mint: Token mint address
            
        Returns:
            Price in USDC or None if failed
        """
        try:
            # USDC mint address on Solana
            usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            
            # Get quote for 1 unit of token
            quote = await self.get_best_route(
                input_mint=token_mint,
                output_mint=usdc_mint,
                amount=1_000_000  # 1 unit in lamports
            )
            
            if quote and "outAmount" in quote:
                # Convert from USDC decimals (6) to float
                price = float(quote["outAmount"]) / 1_000_000
                return price
            return None

        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Token-Preises: {str(e)}")
            return None