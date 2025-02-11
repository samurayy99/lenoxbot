import aiohttp
from typing import Dict, Any, Optional
from utils.logger import BotLogger


class Jupiter:
    """
    Integration mit der Jupiter-API für Trading-Execution.
    """

    def __init__(self, logger: BotLogger, rpc_url: str = "https://quote-api.jup.ag/v4"):
        """
        Initialisiert den Jupiter-Service.

        Args:
            logger: Logger-Instanz für Debugging
            rpc_url: Basis-URL für die Jupiter-API
        """
        self.BASE_URL = rpc_url
        self.logger = logger

    async def get_best_route(self, input_token: str, output_token: str, amount: float) -> Optional[Dict[str, Any]]:
        """
        Holt die beste Trading-Route von Jupiter.

        Args:
            input_token: Token-Adresse für das Eingabe-Token
            output_token: Token-Adresse für das Ausgabe-Token
            amount: Betrag des Eingabe-Tokens

        Returns:
            Die beste Route als Dictionary oder None bei Fehlern.
        """
        url = f"{self.BASE_URL}/quote"
        params = {
            "inputMint": input_token,
            "outputMint": output_token,
            "amount": int(amount * 10**6),  # Annahme: 6 Dezimalstellen für SOL
            "slippage": 1.0  # 1% Slippage
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data and data["data"]:
                            self.logger.info(f"Beste Route gefunden: {data['data'][0]}")
                            return data["data"][0]  # Beste Route
                        else:
                            self.logger.warning("Keine Route verfügbar.")
                            return None
                    else:
                        self.logger.error(f"Jupiter API Fehler: {response.status}")
                        return None
            except Exception as e:
                self.logger.error(f"Fehler beim Abrufen der Route: {str(e)}")
                return None

    async def execute_trade(self, route: Dict[str, Any], private_key: str) -> Optional[str]:
        """
        Führt einen Trade basierend auf einer Route aus.

        Args:
            route: Beste Route von der Jupiter-API
            private_key: Private Key der Wallet zum Signieren der Transaktion

        Returns:
            Die Transaktions-Signatur oder None bei Fehlern.
        """
        url = f"{self.BASE_URL}/swap"
        payload = {
            "route": route,
            "userPublicKey": route["userPublicKey"],
            "userPrivateKey": private_key
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "txSignature" in data:
                            self.logger.info(f"Trade erfolgreich: {data['txSignature']}")
                            return data["txSignature"]
                        else:
                            self.logger.warning("Keine Transaktions-Signatur erhalten.")
                            return None
                    else:
                        self.logger.error(f"Jupiter API Fehler beim Trade: {response.status}")
                        return None
            except Exception as e:
                self.logger.error(f"Fehler bei der Trade-Ausführung: {str(e)}")
                return None

    async def get_token_price(self, token_address: str) -> Optional[float]:
        """
        Holt den aktuellen Token-Preis.
        """
        try:
            route = await self.get_best_route(
                token_address,
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                1.0
            )
            if route:
                return float(route["outAmount"]) / 1e6  # Konvertierung von USDC (6 Dezimalstellen)
            return None
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Token-Preises: {str(e)}")
            return None
